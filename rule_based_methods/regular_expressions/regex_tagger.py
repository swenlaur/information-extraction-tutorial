import regex
from copy import deepcopy

from typing import Set, List, Dict, Union, Generator, Callable

Layer = List[Dict[str, any]]


class RegexTagger:
    """
    An somewhat efficient tagger for extracting reasonable amount of regular expressions form texts.
    Extraction rules are specified as a mapping string --> dict where dict is used to annotating the match.
    By convention we keep only maximal matches and allow overlapping matches.
    The configuration is fixed during the initialisation and cannot be changed afterwards.
    The tagger matches each pattern separately and thus is not suitable to handle more than hundred rules.
    Processing many rules adds a significant performance penalty.
    """

    def __init__(self, rules: Union[Dict[str, dict], Set[str]],
                 overlapped: bool = True, regex_flags: int = 0,
                 conflict_resolver: Union[Callable[[Layer], Layer], str] = 'KEEP_MAXIMAL_MATCHES'):
        """
        Extraction rules are in the form regex string --> dict where the dict contains the match annotation, e.g.
        '\\d+'        --> {type: integer, token: number},
        '\\d+\\.\\d+' --> {type: decimal, token: number}
        'USD|EUR|CNY' --> {type: code, token: currency}
        Attributes 'start' and 'end' are reserved to mark the start and end positions

        Be careful with regular expressions. You can easily confuse when they are greedy and lazy.
        In particular remember that r'a|ab|abc' is very different from r'abc|ab|c'.

        If the flag overlapped is not set then non-overlapping matches are returned for each pattern.
        The regex_flags allows to control the details of regex matching is standard way.

        Rules produce overlapping matches even if the flag overlapped is not set.
        By specifying a conflict resolver you can control which spans are kept and which are removed.

        There are two predefined strategies:
        * KEEP_ALL:     all spans are kept
        * KEEP_MAXIMAL_MATCHES: spans that are covered by other spans are removed

        Other strategies must be implemented as a function which takes in a span list and produces a new span list.
        """

        if isinstance(rules, dict):
            for pattern, annotation in rules.items():
                if 'start' in annotation or 'end' in annotation:
                    raise ValueError("Attributes 'start' and 'end' are reserved do not use it inside annotations")
        elif not isinstance(rules, set):
            raise ValueError('Extraction rules must be specified as Dict[str, dict] or Set[str]')

        if (conflict_resolver not in ['KEEP_ALL', 'KEEP_MAXIMAL_MATCHES']) and not callable(conflict_resolver):
            raise ValueError('Invalid conflict resolving strategy')

        # Protect parameters against changes
        self.rules = deepcopy(rules)
        self.overlapped = overlapped

        # Instantiate conflict resolver
        self.conflict_resolver = conflict_resolver

        # Compile rules
        self.regexes = dict()
        for pattern in self.rules:

            try:
                self.regexes[pattern] = regex.compile(pattern, flags=regex_flags)
            except BaseException as e:
                raise ValueError('Invalid regular expression inside the rule:\n{}\n{}'.format(pattern, e))

    def __call__(self, text: str) -> List[Dict[str, any]]:
        """
        The way to apply the extraction rules to a string.
        Returns a list dictionaries describing the match where 'start' and 'end' attributes specify the location.
        By default KEEP_MAXIMAL conflict resolving strategy is used and only all maximal matches are returned.
        """

        # Extract and annotate matches
        spans = list()
        for pattern, regexp in self.regexes.items():
            annotations = self.rules[pattern]
            spans.extend(
                dict(start=m.start(), end=m.end(), text=text[m.start():m.end()], **annotations)
                for m in regexp.finditer(text, overlapped=self.overlapped)
            )

        spans = sorted(spans, key=lambda x: (x['start'], x['end']))

        if self.conflict_resolver == 'KEEP_ALL':
            return spans
        elif self.conflict_resolver == 'KEEP_MAXIMAL_MATCHES':
            return list(self.keep_maximal_matches(spans))
        else:
            return self.conflict_resolver(spans)

    @staticmethod
    def keep_maximal_matches(spans: Layer) -> Generator[dict, None, None]:
        """
        Given a list of canonically ordered spans removes spans that are covered by another span.
        This automaton always produces matches in the canonical ordering that is defined by two restrictions:

            span[i]['start'] <= span[i+1]['start']
            span[i]['start'] == span[i+1]['start'] ==> span[i]['end'] <= span[i + 1]['end']
        """

        spans = iter(spans)
        current_span = next(spans, None)
        while current_span is not None:
            next_span = next(spans, None)

            # Current span is last
            if next_span is None:
                yield current_span
                return

            # Check if the next span covers the current
            if current_span['start'] == next_span['start']:
                current_span = next_span
                continue

            yield current_span

            # Ignore following spans that are covered by the current span
            while next_span['end'] <= current_span['end']:
                next_span = next(spans, None)
                if next_span is None:
                    return

            current_span = next_span

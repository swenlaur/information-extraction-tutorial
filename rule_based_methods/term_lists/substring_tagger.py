from copy import copy, deepcopy
from ahocorasick import Automaton

from typing import Dict
from typing import List
from typing import Generator


class SubstringTagger:
    """
    An efficient tagger for extracting many substrings form texts.
    Extraction rules are specified as a mapping string --> dict where dict is used to annotating the match.
    By convention we keep only maximal matches and if separators are specified then only complete tokens are matched.
    The configuration is fixed during the initialisation and cannot be changed afterwards.
    """

    def __init__(self, rules: Dict[str, dict], separators: str = ''):
        """
        Extraction rules are in the form string --> dict where the dict contains the annotation for the match, e.g.
        Washington --> {type: capital, country: US},
        Tartu --> {type: town, country: Estonia}
        St. Mary Mead --> {type: village, country: UK}
        Attributes 'start' and 'end' are reserved to mark the start and end positions

        Separators define token boundaries. If they are set then the string must match the entire token, e.g.
        separators = '|' implies that the second match in '|Washington| Tartu |St. Mary Mead' is dropped.
        The last match is valid as the separator does not have to be at the ends of the entire text.

        Extraction rules work for multi-token strings, however, the separators between tokens are fixed by the pattern.
        For multiple separator symbols, all pattern variants must be explicitly listed.
        """

        if not isinstance(rules, dict):
            raise ValueError('Extraction rules must be specified as Dict[str, dict]')
        for pattern, annotation in rules.items():
            if 'start' in annotation or 'end' in annotation:
                raise ValueError("Attributes 'start' and 'end' are reserved do not use it inside annotations")

        # Protect parameters against changes
        self.rules = deepcopy(rules)
        self.separators = copy(separators)

        # Set up the automaton
        self.automaton = Automaton()
        for pattern, attributes in self.rules.items():
            self.automaton.add_word(pattern, len(pattern))
        self.automaton.make_automaton()

    def __call__(self, text:str) -> List[Dict[str,any]]:
        """
        The way to apply the extraction rules to a string.
        Returns a list dictionaries describing the match where 'start' and 'end' attributes specify the location.
        If the token separators are unspecified then all maximal matches are returned.
        Otherwise only matches corresponding to complete tokens are returned.
        To mach a multi-token string the extraction pattern must contain correct separator.
        """

        # Extract matches
        if len(self.separators) == 0:
            return list(self.decorate_spans(self.keep_maximal_matches(self.iterate_over_matches(text))))
        else:
            return list(self.decorate_spans(self.keep_tokens(
                self.keep_maximal_matches(self.iterate_over_matches(text)), text, self.separators)))

    def iterate_over_matches(self, text: str) -> Generator[dict, None, None]:
        """
        Iterates over all matches of the defined by the list of extraction rules.
        Matches can overlap and do not have to be maximal, i.e., one span may completely contain the other.
        """

        for loc, value in self.automaton.iter(text):
            yield dict(start=loc - value + 1, end=loc + 1, text=text[loc - value + 1:loc + 1])

    def decorate_spans(self, spans: Generator[dict, None, None]) -> List[Dict[str, any]]:
        """
        Add annotations to extracted spans based on the right-hand-side of the matching rule.
        """

        current_span = next(spans, None)
        while current_span is not None:

            annotation = self.rules.get(current_span['text'], None)
            if annotation is None:
                current_span = next(spans, None)
                continue

            yield {**current_span, **annotation}
            current_span = next(spans, None)

    @staticmethod
    def keep_maximal_matches(spans: Generator[dict, None, None]) -> Generator[dict, None, None]:
        """
        Given a list of canonically ordered spans removes spans that are covered by another span.
        This automaton always produces matches in the canonical ordering that is defined by two restrictions:

            span[i]['start'] <= span[i+1]['start']
            span[i]['start'] == span[i+1]['start'] ==> span[i]['end'] <= span[i + 1]['end']
        """

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

    @staticmethod
    def keep_tokens(spans: Generator[dict, None, None], text: str, separators: str) -> Generator[dict, None, None]:
        """
        Given a list of spans keeps spans that do not contain of incomplete tokens.
        That is, the symbol before the match and the symbol after the match is a separator symbol.
        """

        n = len(text)
        current_span = next(spans, None)
        while current_span is not None:
            # Check that a preceding symbol is a separator
            if current_span['start'] > 0 and text[current_span['start'] - 1] not in separators:
                current_span = next(spans, None)
                continue

            # Check that a succeeding symbol is a separator
            if current_span['end'] < n and text[current_span['end']] not in separators:
                current_span = next(spans, None)
                continue

            yield current_span
            current_span = next(spans, None)

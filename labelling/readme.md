# Tools for labelling

Data labelling plays a central role in information extraction:
* We examples to understand patterns in the data.
* We need to relabel data in order to improve the extraction algorithm.
* We need good test sets to track the progress and estimate quality.
* We need to assess labelling conflicts to estimate coherence between different annotators.
* We need to assess labelling conflicts to estimate relative difference between algorithms.  

There are four basic tasks in text labelling:
* text classification  
* keyword assignment for text
* named entity recognition
* relation extraction

In the following, we use open source data labelling tool [Label Studio](https://labelstud.io/guide/)
which is available as a separate **pip** package [label-studio](https://pypi.org/project/label-studio/).  


## I. Simple alternatives to Label Studio

**Excel spreadsheets** are good for text classification tasks or for manual validation of algorithms.
* The setup and learning curves are minimal.
* This works only when the expected output is either binary or can be summarised in few words.
* This cannot be used for defining annotation boundaries.

**Tabulated text formats** are good when annotators do not like graphical user interface.
* Usually each word is on separate line and annotator adds attributes after it.
* Separate index column must be added to add relations between words.  
* This can be significantly more efficient way to annotate text.
* It creates many errors and inconsistencies and thus additional post-processing is needed.


## II. Basic steps to set up Label Studio

0. Activate right Python environment
1. Use **pip** to install label-studio and configure it if you need this
2. Use command `label-studio` or `label-studio start` to fire server up
3. Set up user accounts and manage access rights if you need it
4. Log in and configure project
5. Import data into the project
6. Label the data
7. Export annotated data


### Configuration

The best way to configure Label Studio is using environment variables.
There are many of those but the following three variables solve most of the issues:

* `LABEL_STUDIO_PORT = 900`  
* `LABEL_STUDIO_HOST = https://subdomain.example.com:7777`
* `DATABASE_URL = postgres://username:password@hostname.compute.amazonaws.com:5432/dbname`       


### Project Configuration

To setup a labelling project you need to
* name the project
* configure the labelling tasks
* import data to be labelled

The simplest way to choose labelling method is through user interface.
For text annotations you need to pick templates from `Natural Language Processing`:
* Text Classification
* Taxonomy -- keyword assignment
* Named Entity Recognition -- token level classification
* Relation extraction

Labelling configuration goes hand to hand with input data format.
Dollar variables like `$text`, `$header`, `$value` are taken from the JSON fields of input data.
There are shortcut keys which you can configure hidden in the second `Settings` menu that is hidden away.
You can find it when you start labelling. Then there is a mystical icon next to trashcan icon that brings this up  


### Data import

There are three basic data formats one should use data export:
* `txt`
* `tsv` or `csv`
* `json`

Importing raw text files creates a annotation task per each line and you cannot specify any additional
attributes. Tab-separated files allow to specify extra attributes such as predicted labels.

JSON data format is the most complex and allows to specify spans together with annotations.
The JSON file is a list of JSON entries. There are four basic fields for each JSON entry:
* `id` -- task id
* `data` -- text together with the meta information
* `annotations` -- manual annotations
* `predictions` -- automatic predictions  

You can use [`label-studio-converter` library](https://github.com/heartexlabs/label-studio-converter)
to convert most common labelling data formats into the right JSON format.

The simplest way to determine the correct JSON format for pre-annotated texts is to
* Fix a good labelling configuration
* Import one or two raw texts
* Annotate them manually and export the result as a full JSON
* Rename the section `annotations` with the section `predictions`
* Add additional fields to the section `predictions` and update labelling configuration to show them.
After that you have a correct example of the input file and can generate it programmatically 

### Data export

The annotations can be exported form the SQL database when it is properly configured or from the user interface.
The resulting file is in JSON format with the same structure described in the data import section.  


## III. Examples

The directory contains some examples of data and label configurations.

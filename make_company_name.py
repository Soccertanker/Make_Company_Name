"""Makes an awesome company name.

Company names are only awesome if they...
1. Consist of two words with a space in between.
2. Have no non-awesome words. That means each word...
    1. Can't have two characters of the same letter anywhere in the word.       r'^(?!.*(.).*\1)[a-z]*$'
    2. Must have at least one letter that is q, v, w, x, y, or z...     r'^.*[qvwxyz]+.*$'
            but can't start with any of these letters.      r'^[^qvwxyz].*$'
    3. Can't have the letter k. Ks are stupid.      r'^[^k]*$'
    4. Can't be a swear word. Those are inappropriate.
    5. Can't be a stop-word. Those are boring.
    6. Is at least 4 characters long but no longer than 9 characters.
3. Are a noun followed by a verb, noun, adjective, or interjection.
"""
import sys
import os
import json
import random
import re
import requests
import string
import bs4
import nltk
from nltk.corpus import stopwords
#import pdb; pdb.set_trace()


# 10 thousand word list.
WORD_LIST_URL = 'https://www.mit.edu/~ecprice/wordlist.10000'
# 400 thousand plus word list.
#WORD_LIST_URL = 'https://raw.githubusercontent.com/dwyl/english-words/master/words.txt'
PROFANE_WORD_LIST_URL = 'https://www.cs.cmu.edu/~biglou/resources/bad-words.txt'
WORD_SETTINGS = {
    're': r'(?=^[^qvwxyz].*$)(?=^.*[qvwxyz]+.*$)(?=^(?!.*(.).*\1)[a-z]*$)(?=^[^k]*$)',
    'min_len': 2,
    'max_len': 6
}
FIRST_WORD_PARTS_OF_SPEECH_RE = r'^NN[^S]?$'
SECOND_WORD_PARTS_OF_SPEECH_RE = r'^NN[^S]?$|^VB.?$|^JJ.?$|^UH$'
WORD_OPTIONS_JSON = 'json/word_options.json'
COMPANY_NAMES_FILENAME = 'company_names.txt'


def get_words(url):
    """Returns a list of words from the url."""
    page = requests.get(url)
    page.raise_for_status()
    soup = bs4.BeautifulSoup(page.text, 'html.parser')
    return nltk.tokenize.word_tokenize(soup.get_text())


def get_words_by_parts_of_speech(words, parts_of_speech_re):
    """Finds words with the desired parts of speech.
    Parts of speech tag reference: https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html
    """
    return [word for word, part_of_speech in words if re.match(parts_of_speech_re, part_of_speech)]


def generate_word_combinations(first_word_options, second_word_options, num_combinations):
    """Generates strings that are random combinations of the two words."""
    return ['{:s} {:s}'.format(random.choice(first_word_options), random.choice(second_word_options))
            for _ in range(num_combinations)]


def remove_displeasing_words(words, word_settings):
    """Keeps words that match word_re and if they're within length boundaries."""
    word_re = word_settings['re']
    max_word_len = word_settings['max_len']
    min_word_len = word_settings['min_len']
    return [word for word in words if re.match(word_re, word)
            and min_word_len <= len(word) <= max_word_len]


def save_word_options(first_word_options, second_word_options):
    """Saves word options in json files."""
    json_dict = {
        'first_word_options': first_word_options,
        'second_word_options': second_word_options,
        'word_settings': WORD_SETTINGS
    }
    with open(WORD_OPTIONS_JSON, 'w') as json_file:
        json.dump(json_dict, json_file, indent='\t')
    print('Saved new word data at {:s}\n'.format(WORD_OPTIONS_JSON), file=sys.stderr)


def existing_word_data_is_valid(word_options_dict):
    return 'word_settings' in word_options_dict     \
           and word_options_dict['word_settings'] == WORD_SETTINGS      \
           and 'first_word_options' in word_options_dict        \
           and len(word_options_dict['first_word_options']) >= 1        \
           and 'second_word_options' in word_options_dict        \
           and len(word_options_dict['second_word_options']) >= 1


def get_existing_word_data():
    if not os.path.exists(os.path.dirname(os.path.abspath(__file__)) + '/' + WORD_OPTIONS_JSON):
        return None
    print('Opening existing word data.\n', file=sys.stderr)
    with open(WORD_OPTIONS_JSON, 'r') as json_file:
        json_data = json.load(json_file)
    if not existing_word_data_is_valid(json_data):
        print('No valid existing word data exists.\n', file=sys.stderr)
        return None
    return json_data['first_word_options'], json_data['second_word_options']


def get_word_options():
    """Gets a tuple of (first_word_options, second_word_options)."""
    word_options = get_existing_word_data()
    if word_options:
        print('Using existing word data.\n', file=sys.stderr)
        return word_options

    print('Generating new word data.\n', file=sys.stderr)
    words = set(get_words(WORD_LIST_URL))
    profane_words = set(get_words(PROFANE_WORD_LIST_URL))
    stop_words = set(stopwords.words('english'))
    words = list(words - profane_words - stop_words)
    words = remove_displeasing_words(words, WORD_SETTINGS)
    words = nltk.pos_tag(words)
    first_word_options = get_words_by_parts_of_speech(words, FIRST_WORD_PARTS_OF_SPEECH_RE)
    second_word_options = get_words_by_parts_of_speech(words, SECOND_WORD_PARTS_OF_SPEECH_RE)
    save_word_options(first_word_options, second_word_options)
    return first_word_options, second_word_options


def main():
    first_word_options, second_word_options = get_word_options()
    company_name_options = generate_word_combinations(first_word_options, second_word_options, 100)
    company_names_text = ''
    for company_name_option in company_name_options:
        company_names_text += '{:s}\n'.format(string.capwords(company_name_option))
    with open(COMPANY_NAMES_FILENAME, 'w') as names_file:
        names_file.write(company_names_text)
    print('Saved awesome company names to {:s}\n'.format(COMPANY_NAMES_FILENAME), file=sys.stderr)


if __name__ == '__main__':
    main()

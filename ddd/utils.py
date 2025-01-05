import os
import re
import unicodedata

from bs4 import BeautifulSoup as BS
from bs4.element import Comment, NavigableString



DIR_ROOT = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DIR_DATA = os.path.join(DIR_ROOT, 'data')
DIR_MAIL_DATASET = os.path.join(DIR_DATA, 'mail_dataset')

RE_LINKS = re.compile(r'https?://\S+|www\.\S+', flags=re.IGNORECASE)
RE_LONG_STR = re.compile(r'\S{256,}')
RE_LONG_SEQ = re.compile(r'(\S)\1{9,}')

_CSS_AT_RULES = [
    'layer', 'identifier', 'charset', 'charset', 'import', 'namespace', 'identifier', 'media',
    'scope', 'starting', 'supports', 'document', 'page', 'font-face', 'keyframes', 'counter',
    'font', 'swash', 'ornaments', 'annotation', 'stylistic', 'styleset', 'character', 'charset-variant',
    'property', 'layer', 'media', 'scope', 'starting-style', 'supports', 'document', 'layer', 'charset',
    'color-profile', 'container', 'counter-style', 'document', 'font-face', 'font-feature-values',
    'font-palette-values', 'import', 'keyframes', 'layer', 'media', 'namespace', 'page', 'property',
    'scope', 'starting-style', 'supports'
]
RE_CSS_COMMENT = re.compile(r'/\*.*?\*/', flags=re.DOTALL)
RE_CSS_STMT = re.compile(r'\{(\s*|[^\{\}:]+:[^\{\}]+)\}', flags=re.DOTALL)
RE_CSS_BLCK = re.compile(r'((?<=[\{\}\n])|(?<=^))[^\{\}\n]+\s?\{(\s|<CSS>)*\}', flags=re.DOTALL)
RE_CSS_AT_RULE = re.compile(f'@({"|".join(_CSS_AT_RULES)})' + r'.*?\{[^\{\}]*?\}', flags=re.DOTALL|re.IGNORECASE)



def strip_css(s):
    def _sub(regex, sub_str, s):
        while True:
            new_s = regex.sub(sub_str, s, count=1)
            if new_s == s:
                return s
            s = new_s

    while True:
        s_new = _sub(RE_CSS_COMMENT, ' ', s)
        s_new = _sub(RE_CSS_STMT, '{<CSS>}', s_new)
        s_new = _sub(RE_CSS_BLCK, '<CSS>', s_new)
        s_new = _sub(RE_CSS_AT_RULE, '<CSS>', s_new)
        s_new = s_new.replace('<CSS>', '\n')
        if s == s_new:
            return s_new
        s = s_new


def normalize_lines(s):
    lines = s.split('\n')
    lines = [' '.join(l.split()) for l in lines]
    return '\n'.join([l for l in lines if l]).strip()


def _element_is_visible(element):
    hidden = ['style', 'script', 'head', 'title', 'meta']
    if element.parent.name in hidden or isinstance(element, Comment):
        return False
    if element.parent.name == '[document]':
        return type(element) is NavigableString
    return True


def extract_text_from_html(s):
    soup = BS(s.strip(), 'html.parser')
    if not soup.find():
        return s

    text = soup.find_all(text=True)
    text = filter(_element_is_visible, text)  
    return ' '.join(text)


def extract_links_from_html(s):
    soup = BS(s.strip(), 'html.parser')
    if not soup.find():
        return s

    links = soup.find_all('a', href=True)
    links = filter(_element_is_visible, links)  
    return [l['href'] for l in links]


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
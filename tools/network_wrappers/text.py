import string
import re
from nltk.stem.wordnet import WordNetLemmatizer
import nltk
from nltk.corpus import wordnet


STOP_WORDS = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours',
              'ourselves', 'you', 'your', 'yours', 'yourself',
              'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her',
              'hers', 'herself', 'it', 'its', 'itself', 'they', 'them',
              'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom',
              'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was',
              'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having',
              'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but',
              'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by',
              'for', 'with', 'about', 'against', 'between', 'into', 'through',
              'during', 'before', 'after', 'above', 'below', 'to', 'from',
              'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
              'again', 'further', 'then', 'once', 'here', 'there', 'when',
              'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few',
              'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
              'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't',
              'can', 'will', 'just', 'don', 'should', 'now']
# STOP_WORDS = []
DELIMITERS = [';', '.', '?', '!', ':', '"', ","]  # ':', '"', ","
reDELIMITER_STR=re.escape(''.join(DELIMITERS))

lemmatizer = WordNetLemmatizer()


def get_traceroutes(plain_text_path):
    # print 'Load %s' % plain_text_path
    with open(plain_text_path, 'r') as f:
        text = f.read()
    text = filter(lambda x: x in string.printable, text)
    text = text.lower()
    text = text.replace('\r\n', ' ')
    text = text.replace('\n', ' ')
    text = re.sub('[^a-z%s]+' % (reDELIMITER_STR), ' ', text)
    sentences = [x for x in [y.strip() for y in re.split("[%s]" % (reDELIMITER_STR), text.strip())] if len(x) > 0]

    traceroutes = create_traceroutes(sentences)

    return traceroutes


def load_topology(adj_matrix_path):
    raise NotImplementedError('Topology loading in text class not implemented yet')


def create_traceroutes(sentences):

    traces = []

    for counter, sentence in enumerate(sentences):
        print counter, '/', len(sentences)
        words = sentence.split()
        words = [x for x in words if x not in STOP_WORDS and len(x) > 1]
        tagged = nltk.pos_tag(words)
        words = [lemmatizer.lemmatize(x[0], get_wordnet_pos(x[1])) for x in tagged]
        if not words: continue
        if len(words) < 2: continue
        traces.append(words)

    return traces


def get_wordnet_pos(treebank_tag):

    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN

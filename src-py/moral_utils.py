import glob
import nltk
import spacy
import moralstrength
import pandas as pd
import numpy as np
from moralstrength import lexicon_use as moral_lexicon
from nltk import word_tokenize
from nltk.corpus import stopwords

from moralstrength import lexicon_use as moral_lexicon
from moralstrength import data as moral_data

moral_founds = [
    'care',
    'fairness',
    'loyalty',
    'authority',
    'purity'
]

morals_map = {
    'care' : 'harm',
    'fairness': 'cheeting',
    'loyalty' : 'betrayal',
    'authority': 'subversion',
    'purity': 'degradation'
    
}


def get_moral_concepts(path='/workspace/ceph_data/moral-based-argumentation/Morality-in-Knowledge-Graphs/MFD-Linking/', preprocess=False):
    
    def get_concept(c_url):
        concept = c_url.split('/')[-1]
        if '_(' in concept:
            concept = concept.split('_(')[0]

        return ' '.join([x.lower() for x in concept.split('_')])

    moral_concepts = {}
    for moral in ['care', 'fairness', 'authority', 'loyalty', 'purity']:
        moral_entities = []
        linking_files = glob.glob(path+'*/{}.txt'.format(moral))
        for file in linking_files:
            if 'wordnet' in file:
                continue
            
            if preprocess:
                moral_entities+= [l.strip().lower() if 'http' not in l else get_concept(l.strip()) for l in open(file, encoding='utf8').readlines()]
            else:
                moral_entities+= [x.strip() for x in open(file, encoding='utf8').readlines()]

        moral_concepts[moral] = moral_entities
    return moral_concepts


def average_morals(morals_list):
    output= {x:0 for x in moral_founds}
    
    for x in morals_list:           
        for key in output.keys():
            output[key]+=x[key]
    
    for key in output.keys():
        output[key] = output[key]/len(morals_list)
    
    return output


def get_emfd_moral_dict():
    emfd_df = pd.read_csv('/workspace/ceph_data/moral-based-argumentation/eMFD/eMFD_wordlist.csv')
    emfd_df.columns = ['word', 'care', 'fairness', 'loyalty', 'authority',
           'purity', 'care_sent', 'fairness_sent', 'loyalty_sent',
               'authority_sent', 'sanctity_sent']
    
    morals = ['care', 'fairness', 'loyalty', 'authority', 'purity']
    emfd_df['word_moral_value'] = emfd_df.apply(lambda row: max(row[1:6]), axis=1)
    emfd_df['word_moral'] = emfd_df.apply(lambda row: morals[np.argmax(row[1:6])], axis=1)
    moral_words_df = emfd_df.groupby('word_moral').agg({'word': lambda word: list(word),
                                                       'word_moral_value': lambda v: list(v)}).reset_index()
    
    moral_dict = {}
    for moral in morals:
        words  = moral_words_df[moral_words_df.word_moral == moral]['word'].tolist()[0]
        scores = moral_words_df[moral_words_df.word_moral == moral]['word_moral_value'].tolist()[0]
        moral_dict[moral] = {x[0]:x[1] for x in zip(words, scores)}
    
    return moral_dict


moralstrength_dict = moral_data.read_moral_lex('original')
emfd_dict = get_emfd_moral_dict()


def get_moral_words(source, morals=None):
    if source == 'moralstrength':
        moral_dict = moralstrength_dict
    elif source == 'emfd':
        moral_dict = emfd_dict
    else:
        return None

    morals_words = []
    if morals !=None:
        for key, value in morals.items():
            moral_words= [(x[0], abs(x[1]-5)/5) for x in moral_dict[key].items()]
            moral_words= [(x[0], x[1]*value) for x in moral_words]
            
            morals_words += moral_words
    else:
        for key, value in moral_dict.items():
            moral_words= [(x[0], abs(x[1]-5)/5) for x in value.items()]
            moral_words= [(x[0], x[1]) for x in moral_words]
            
            morals_words += moral_words
    
    return morals_words


def text_to_tokens(text):
    return set([word for word in nltk.word_tokenize(text.lower()) if word not in stopwords.words('english')])

def text_overlap(text1, text2):
    tokens1 = text_to_tokens(text1)
    tokens2 = text_to_tokens(text2)
    
    return len(tokens1.intersection(tokens2))/len(tokens1.union(tokens2))


def moral_foundation_embedding(moral_words):
    moral_vecs = []
    for word in moral_words:
        if word.lower() in nlp.vocab:
            moral_vecs.append(nlp.vocab[word.lower()].vector)
    
    return np.mean(moral_vecs)
        
def embed_sentence(sentence):
    sent_vecs = []
    for word in text_to_tokens(sentence):
        if word in nlp.vocab:
            sent_vecs.append(nlp.vocab[word].vector)

    return np.mean(sent_vecs)

def moral_dist_of_text(text, binary=False, min_max=[5, 5]):
    '''
    Given a text, for each of the moral_foundation count number of words (if binary) that
    belong to that moral_foundation according to the moralstrength dictionary
    '''
    words = word_tokenize(text)
    dist_dict = {x:0 for x in moral_founds}
    
    for word in words:
            word_morals = moralstrength.word_moral_values(word)
            for key, value in word_morals.items():
                if value == -1:
                    continue

                if value >= min_max[0] and value <= min_max[1]: #skip words that are not strongly relevant
                    continue

                key = key+'+' if value > min_max[1] else key+'-'
                value = value if value > min_max[1] else value+5
                if binary:
                    dist_dict[key]+= 1
                else:
                    dist_dict[key]+= value
    return dist_dict

def evaluate_user_morals(df, clm_txt):
    df['pred_moral_founds'] = df[clm_txt].apply(lambda x: moral_dist_of_text(str(x)))
    
    #filter only users whith more than one answer
    users_with_more_than_one_claim = [x[0] for x in df.user.value_counts().to_dict().items() if x[1] > 1]
    df_users = df.groupby('user').agg({'pred_moral_founds': lambda x: average_morals(x), 'top_moral': lambda x: x.iloc[0]}).reset_index()
    df_users = df_users[df_users.user.isin(users_with_more_than_one_claim)]
    
    df_users['pred_top_moral'] = df_users.pred_moral_founds.apply(lambda x: sorted(x.items(), key=lambda m: -m[1])[0][0])
    
    acc = sum([x[0] == x[1] for x in zip(df_users['pred_top_moral'].tolist(), df_users['top_moral'].tolist())])/len(df_users)
    
    return acc, df_users

def user_bow_from_big_issues_stances_dict(user_bi_dict, pro_bows, con_bows, apply_mask=False):
    user_bow = []
    for bi in user_bi_dict.items():
        if bi[1] == 1 and bi[0] in con_bows:
            user_bow += con_bows[bi[0]]
        if bi[1] == 3 and bi[0] in pro_bows:
            user_bow += pro_bows[bi[0]]

    return list(filter(lambda x: x!='', set(user_bow)))

def get_weighted_bow(documents, vocabulary=None, vocab_size=1000):
    from sklearn.feature_extraction.text import TfidfVectorizer
    
    #make sure the corpus is unique
    corpus = set(documents)

    if vocabulary != None:
        vectorizer = TfidfVectorizer(use_idf=False, vocabulary=vocabulary)
    else:
        vectorizer = TfidfVectorizer(max_features=vocab_size, use_idf=False, stop_words='english')

    X = vectorizer.fit_transform(documents)
    features = vectorizer.get_feature_names()

    weighted_bow=[]
    for x in X.toarray():
        tmp_weighted_bow = []
        for i, word in enumerate(features):
            if x[i] > 0:
                tmp_tuple = (word, x[i])
                tmp_weighted_bow.append(tmp_tuple)
        weighted_bow.append(tmp_weighted_bow)

    return weighted_bow

def scale_word_scores(word_scores):
    if len(word_scores) == 0:
        return []

    words, scores = zip(*word_scores)
    scores = np.array([x[1] for x in word_scores])
    scaled_scores = list(np.interp(scores, (scores.min(), scores.max()), (0, 1)))
    resulted_word_scores =zip(words, scaled_scores)
    
    return list(resulted_word_scores)
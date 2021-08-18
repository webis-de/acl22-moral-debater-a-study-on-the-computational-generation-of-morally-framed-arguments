import collections
import joblib
import datasets
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.model_selection import KFold
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, accuracy_score, f1_score

import nltk
from nltk.translate import bleu_score
from nltk.translate.bleu_score import SmoothingFunction
from nltk.translate.meteor_score import meteor_score


import numpy as np

nltk.download('wordnet')
bertscore = datasets.load_metric('bertscore')

def perform_significance_tests(df, app1_name, app2_name, metrics):
            
    sig_report = {}
    for idx, measure in enumerate(metrics):
        all_data = np.array(list(zip(df['{}_{}'.format(app1_name, measure)].tolist(), df['{}_{}'.format(app2_name, measure)].tolist())))
        chunks = np.array_split(all_data, 5, axis=0)

        s1 = [x[:,0].mean() for x in chunks]
        s2 = [x[:,1].mean() for x in chunks]

        sig_report[measure] = {'@5%':check_sig(s2, s1, alpha=0.05), 
                               '%10': check_sig(s2, s1, alpha=0.1)
        }
        
    return sig_report

def check_sig(v1s, v2s, alpha=0.05):
    from scipy import stats

    diff = list(map(lambda x1 , x2: x1 - x2, v1s, v2s))
    is_normal = stats.shapiro(diff)[1] > alpha
    
    ttest = stats.ttest_rel(v1s, v2s) if is_normal else stats.wilcoxon(v1s, v2s)
    if ttest.statistic >=0:
        if (ttest.pvalue/2) <= alpha:
            return True
        else:
            return False
    else:
        return False

    
def eval_meteor(references, preds, best_match=False):
    references  = list(
        map(lambda item: [item.replace('<|endoftext|>', '')] if not isinstance(item, list) else [ref.replace('<|endoftext|>', '') for ref in item] , references))
    
    preds = list(map(lambda x: x.replace('<|endoftext|>', ''), preds))

    meteor_scores = [round(meteor_score(inst[0], inst[1]), 3) for inst in zip(references, preds)]

    return sum(meteor_scores)/len(meteor_scores), meteor_scores

def eval_bleu(references, preds, weights=None):
    references  = list(
        map(lambda item: [item.replace('<|endoftext|>', '').split()] if not isinstance(item, list) else [ref.replace('<|endoftext|>', '').split() for ref in item] , references))
    preds = list(map(lambda x: x.replace('<|endoftext|>', '').split(), preds))
    
    chencherry = SmoothingFunction()

    bleu_scores = [round(bleu_score.sentence_bleu(ref, pred, weights, smoothing_function=chencherry.method1), 3)
                    for ref, pred in zip(references, preds)]
    
#     if weights != None:
#         score = bleu_score.corpus_bleu(references, preds, weights=weights, smoothing_function=chencherry.method1)
#     else:
#         score = bleu_score.corpus_bleu(references, preds,  smoothing_function=chencherry.method1)

    score = sum(bleu_scores)/len(bleu_scores)
    
    return (score * 100), bleu_scores


def eval_bertscore(references, preds):
    references  = list(
        map(lambda item: [item.replace('<|endoftext|>', '')] if not isinstance(item, list) else [ref.replace('<|endoftext|>', '') for ref in item] , references))
    
    #references  = list(map(lambda x: x.replace('<|endoftext|>', ''), references))
    preds = list(map(lambda x: x.replace('<|endoftext|>', ''), preds))
    
    bertscore_scores = bertscore.compute(predictions=preds, references=references, lang='en', rescale_with_baseline=True, idf=False, batch_size=8)
    bert_precision = np.mean(bertscore_scores['precision'])
    bert_recall = np.mean(bertscore_scores['recall'])
    bert_f1 = np.mean(bertscore_scores['f1'])

    metrics = {
        'BERTScore-P': bert_precision,
        'BERTScore-R': bert_recall,
        'BERTScore-F1': bert_f1
    }

    metrics = {k: str(round(v, 3)) for k, v in metrics.items()}

    return metrics, bertscore_scores['precision'], bertscore_scores['recall'], bertscore_scores['f1']
    
def eval_preds(app_name, gt, preds):   
    
    bleu1, bleu1_scores= eval_bleu(gt, preds, weights=(1.0, 0, 0))
    bleu2, bleu2_scores= eval_bleu(gt, preds, weights=(0, 1, 0))
    bleu3, bleu3_scores= eval_bleu(gt, preds, weights=(0, 0, 1))
    meteor, meteor_scores= eval_meteor(gt, preds)
    bertscore, prec_scores, rec_scores, f1_scores = eval_bertscore(gt, preds)
    distinct_n, distinct_n_scores = eval_distinct(preds, 1)
    
    return [app_name, bleu1, bleu2, bleu3, meteor, bertscore['BERTScore-F1'], distinct_n], bleu1_scores, bleu2_scores, bleu3_scores, meteor_scores, prec_scores, rec_scores, f1_scores, distinct_n_scores

from transformers import BertTokenizer, BertForSequenceClassification
import torch
import spacy
import pandas as pd
import numpy as np
from tqdm import tqdm
from scipy import stats
from spacy.lang.en import English
from moralstrength.moralstrength import estimate_morals

sentencizer = English()
sentencizer.add_pipe(sentencizer.create_pipe('sentencizer'))

def load_model(path):
    tokenizer = BertTokenizer.from_pretrained(path)
    model = BertForSequenceClassification.from_pretrained(path, return_dict=True).cuda()
    return model, tokenizer


def preprocess(documents):
    doc_lengths = []
    sentences = []
    pbar = tqdm(enumerate(documents), total=len(documents))
    for i, document in pbar:
        pbar.set_description('|   -moral distribution preprocessing')
        doc = sentencizer(document)
        doc_sentences = [sent.text for sent in doc.sents]
        sentences += doc_sentences
        doc_lengths.append(len(list(doc.sents)))
    return doc_lengths, sentences

def postprocess(doc_lengths, scored_sentences):
    scored_documents = []
    current_index = 0
    for doc_length in doc_lengths:
        scored_document = np.mean(scored_sentences[current_index:current_index+doc_length], axis=0)
        scored_documents.append(scored_document)
        current_index += doc_length
    return scored_documents

def sigmoid(x):
    return 1 / (1 + np.exp(-x))
            

def moralstrength_lexicon(texts):
    result = estimate_morals(texts, process=True) # set to false if text is alredy pre-processed
    result = result.fillna(0)
    moral2id = {0: 'care', 1: 'fairness', 2: 'loyalty', 3: 'authority', 4: 'purity'}
    
    morals = []
    for i, row in result.iterrows():
        ids = [i for i, v in enumerate(row) if v > 8 or v < 2]
        morals.append([moral2id[j] for j in ids])

    return morals

def get_arg_morals_mbert(args, model_path):

    moral2id={0:'authority', 1: 'care', 2:'fairness', 3:'loyalty', 4:'purity'}
    model, tokenizer = load_model(model_path)
    output_morals = []
    
    for arg in args:
        input_tokens = tokenizer(arg, max_length=512, return_tensors='pt', truncation=True, padding=True, add_special_tokens=True)
        outputs = model(input_tokens['input_ids'].cuda())[0].detach().cpu().numpy()
        outputs = sigmoid(outputs)[0]
        morals  = [moral2id[i] for i, o in enumerate(outputs) if o > 0.5]
        output_morals.append(morals)
        

    return output_morals

def get_arg_morals(args, model_path):
    moral2id = {0: 'authority', 1: 'care', 2: 'fairness', 3: 'loyalty', 4: 'purity'}
    model, tokenizer = load_model(model_path)
    output_morals = []
    args_sents = [[sent.text for sent in sentencizer(arg).sents] for arg in args]
    
    for arg_sents in args_sents:
        if len(arg_sents) == 0:
            output_morals.append(set([]))
            continue

        input_tokens = tokenizer(arg_sents, max_length=512, return_tensors='pt', truncation=True, padding=True, add_special_tokens=True)
        outputs = model(input_tokens['input_ids'].cuda())[0].detach().cpu().numpy()
        scores  = list(np.exp(outputs) / np.exp(outputs).sum(-1, keepdims=True))
        morals  = [moral2id[np.argmax(s)] for s in scores if np.max(s) > 0.5]
        output_morals.append(set(morals))
        

    return output_morals
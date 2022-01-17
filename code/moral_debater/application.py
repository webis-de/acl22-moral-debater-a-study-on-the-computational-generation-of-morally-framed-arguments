from flask import Flask, render_template, url_for, request, Response
from moral_debater.debater import moral_debater
from moral_debater.classifier import bert_moral_classification
import torch

print(torch.__version__)
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("home.html")

@app.route("/submit/<input>", methods=["GET"])
def process_submit(input):
   
    moral_topic_array = input.split('$')
    moral_string = moral_topic_array[0]
    morals = moral_string.split('_') if moral_string.__contains__('_') else [moral_string]
    
    # topic, stance and query length
    input_list = moral_topic_array[1].split('_')
    topic = input_list[0]
    stance = input_list[1]
    query_size = int(input_list[2])
    claim_thresh = float(input_list[3])
    evidence_thresh = float(input_list[4])
    
    moral_dict = {'x':set(morals)}
    response = moral_debater.collect_narratives_via_classifier_stance([topic], moral_dict, query_size, stance, claim_thresh, evidence_thresh, old_narratives={})
    response_text='empty'
    if stance == 'pro':
        response_text = str(response[topic]['x_pro_narrative'])
    else:
        response_text = str(response[topic]['x_con_narrative'])
    
    empty_string = True  # marks that response_text is empty
#     for response_unit in response_list:
#         if empty_string is True:
#             response_text = response_unit
#             empty_string = False
#         else:
#             response_text = response_text + '\n\n' + response_unit

#     print(response[topic])
            
    response = Response(response_text, 200, mimetype='application/json')
    return response
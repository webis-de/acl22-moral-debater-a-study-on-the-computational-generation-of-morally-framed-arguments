from flask import Flask, render_template, url_for, request, Response
from moral_debater.debater.moral_debater import *


def create_app():

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        #DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )


    @app.route("/")
    def index():
        return render_template("home.html")


    @app.before_first_request
    def load_global_data():
        global moral_debater_client
        moral_debater_client = MoralDebater()

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
        response = moral_debater_client.collect_narratives_via_classifier(topic, moral_dict, query_size, stance, claim_thresh, evidence_thresh)
        response_text='empty'
        if stance == 'pro':
            response_text = response['x_pro_narrative']
        else:
            response_text = response['x_con_narrative']

                
        response = Response(response_text, 200, mimetype='application/json')
        return response


    return app

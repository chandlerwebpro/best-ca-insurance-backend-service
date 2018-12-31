import json
from pprint import pprint
import uuid

from flask import Flask
from flask import request
from flask import jsonify
from flask import make_response

import pika

app = Flask(__name__)

class InsuranceQuoteScraper(object):
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, parameters):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key='rpc_queue',
                                   properties=pika.BasicProperties(
                                         reply_to = self.callback_queue,
                                         correlation_id = self.corr_id,
                                         ),
                                   body=parameters)
        while self.response is None:
            self.connection.process_data_events()
        return self.response

    def close(self):
        self.connection.close()


@app.route("/step1", methods=['POST'])
def step1():
    form_state = {
        'form_step': 'step1',
        'form_session': request.form['form_session'],
        'form_fields': {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'email': request.form['email'],
            'contact_phone': request.form['contact_phone'],
            'phone_type': request.form['phone_type'],
            'zip_code': request.form['zip_code']
        }
    }

    form_state = json.dumps(form_state)
    print(form_state)
    insurance_quote_rpc = InsuranceQuoteScraper()
    result = insurance_quote_rpc.call(form_state)
    insurance_quote_rpc.close()
    result = str(result, 'utf-8')
    print('result from rpc server = ')
    print(result)
    return result
                    
@app.route("/pika-rpc-test")
def pika_rpc_test():
    response = fibonacci_rpc.call(30)
    return "[x] Requesting fib(30)\n [.] Got " + str(response)

# @app.route("/")
# def home():
#     return '<h2> Hello Froggy </h2>';
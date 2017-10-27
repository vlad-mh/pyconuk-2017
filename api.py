import time

from flask import Flask
from flask import jsonify
from flask import request
import blinker as _

from ddtrace import tracer
from ddtrace.contrib.flask import TraceMiddleware
tracer.configure(hostname='datadog')


from thoughts import thoughts


@tracer.wrap(name='think')
def think(subject):
    tracer.current_span().set_tag('subject', subject)

    time.sleep(0.5)
    return thoughts[subject]


app = Flask('API')
traced_app = TraceMiddleware(app, tracer, service='thinker-api')


@app.route('/think/')
def think_handler():
    with tracer.trace('flask.request', service='thinker-api', resource='api.think') as span: # REMOVEME
        response = {}
        for subject in request.args.getlist('subject', str):
            try:
                thought = think(subject)
                response[subject] = {
                    'error': False,
                    'quote': thought.quote,
                    'author': thought.author,
                }
            except KeyError:
                response[subject] = {
                    'error': True,
                    'reason': 'This subject is too complicated to be resumed in one sentence.'
                }
        return jsonify(response)

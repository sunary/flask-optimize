__author__ = 'sunary'


from flask_optimize import FlaskOptimize
from flask import Flask, request, render_template
import time


flask_app = Flask(__name__)
flask_optimize = FlaskOptimize(flask_app)


@flask_app.route('/')
@flask_optimize.optimize()
def index():
    return 'Using flask-optimize'


@flask_app.route('/html')
@flask_optimize.optimize()
def html():
    return '''
    <html>
    <body>
    The content of the body element is displayed in your browser.
    </body>
    </html>
    '''

@flask_app.route('/text')
@flask_optimize.optimize('text')
def text():
    return '''
    <html>
    <body>
    Data type response is text, so this content wasn't minified
    </body>
    </html>
    '''

@flask_app.route('/json')
@flask_optimize.optimize('json')
def json():
    return {'text': 'anything', 'other_values': [1, 2, 3, 4]}


@flask_app.route('/load_svg')
@flask_optimize.optimize()
def load_svg():
    return render_template('load_svg.html')


if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=5372, debug=False)

    time.sleep(5)
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')

    func()
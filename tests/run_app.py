__author__ = 'sunary'


from flask_optimize.optimize import FlaskOptimize
from flask import Flask, request, render_template
import time


flask_app = Flask(__name__)
flask_app.config['OPTIMIZE_ALL_RESPONSE'] = True    # switch by this option
flask_optimize = FlaskOptimize(flask_app)


@flask_app.route('/')
@flask_optimize.optimize()
def index():
    return 'Using flask-optimize'


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
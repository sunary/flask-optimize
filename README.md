# Flask-optimize

[![Build Status](https://travis-ci.org/sunary/flask-optimize.svg?branch=master)](https://travis-ci.org/sunary/flask-optimize)

- **Flask optimization using cache, minify html and gzip response**
- **Support limit decorator, redirect host and cross-site HTTP**

https://pypi.python.org/pypi/flask-optimize

## Python code usage
```python
from flask import Flask
from flask_optimize import FlaskOptimize

flask_app = Flask(__name__)
app.config['OPTIMIZE_ALL_RESPONSE'] = True    # switch by this option
flask_optimize = FlaskOptimize()
flask_optimize.init_app(app)  # full mode

@flask_app.route('/')
@flask_optimize.optimize()  # view mode
def index():
    return 'using Flask-optimize'
```

## Install
```shell
pip install flask-optimize
```

## Requirements: ##
* Python 2.x
* Python 3.x

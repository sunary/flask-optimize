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
flask_optimize = FlaskOptimize()

@flask_app.route('/')
@flask_optimize.optimize()
def index():
    return 'using Flask-optimize'
```

## Install
```shell
pip install flask-optimize
```
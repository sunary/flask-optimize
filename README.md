# Flask-optimize

[![Build Status](https://travis-ci.org/sunary/flask-optimize.svg?branch=master)](https://travis-ci.org/sunary/flask-optimize)

- **Flask optimization using cache, minify html and gzip response**
- **Support limit decorator, redirect host and cross-site HTTP**

https://pypi.python.org/pypi/flask-optimize

## Optimize parameters

### init_app:

**config:** Global config

Default:

```json
{
    "html": {"htmlmin": True,  "compress": True, "cache": "GET-84600"},
    "json": {"htmlmin": False, "compress": True, "cache": False},
    "text": {"htmlmin": False, "compress": True, "cache": 84600}
}
```

`html`, `json`, `text`: keys for data type of response, see detail below

**config_update:** update into default global config

### optimize

**dtype:** Data type of response, will get value corresponding with key in global config.

- `html` *(default)* 
- `text`
- `json`

**htmlmin:** Override `htmlmin` in config by key **dtype**

```
None: using default value from global config
True: enable minify html
False: disable
```

**compress:** Override `compress` in config by key **dtype**

```
None: using default value from global config
True: enable compress content (using gzip)
False: disable
```

**cache:** Override `cache` in config by key **dtype**

```
None: using default value from global config
GET-84600: enable for GET method only, cached time is 84600 seconds
False: disable
```


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

@flask_app.route('/html')
@flask_optimize.optimize()
def html():
    return '''
    <html>
    <body>
    Default data type is html.
    This content will be minified.
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

if __name__ == '__main__':
    flask_app.run('localhost', 8080, debug=True)
```

## Install

```shell
pip install flask-optimize
```

## Requirements: ##

* Python 2.x
* Python 3.x

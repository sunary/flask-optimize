# Flask-optimize

[![Build Status](https://travis-ci.org/sunary/flask-optimize.svg?branch=master)](https://travis-ci.org/sunary/flask-optimize)

Flask optimization: cache, minify HTML, and compress responses (gzip).

**PyPI:** https://pypi.python.org/pypi/flask-optimize

## Install

```shell
pip install flask-optimize
```

Requires Python 3.9+.

## Usage

```python
from flask import Flask
from flask_optimize import FlaskOptimize

app = Flask(__name__)
optimize = FlaskOptimize(app)

@app.route('/')
@optimize.optimize()
def index():
    return 'Using Flask-optimize'

@app.route('/html')
@optimize.optimize()
def html():
    return '<html><body>Minified content</body></html>'

@app.route('/json')
@optimize.optimize('json')
def json():
    return {'key': 'value'}
```

## Configuration

| Config | Options |
|--------|---------|
| `None` | Use defaults |
| `dict` | Custom config with `html`, `json`, `text` keys |
| Flask app | Use `app.config['FLASK_OPTIMIZE']` or defaults |

Default config:

```python
{
    'html': {'htmlmin': True,  'compress': True, 'cache': 'GET-84600'},
    'json': {'htmlmin': False, 'compress': True, 'cache': False},
    'text': {'htmlmin': False, 'compress': True, 'cache': 'GET-84600'},
    'trim_fragment': False,
}
```

### optimize decorator

| Param | Description |
|-------|--------------|
| `dtype` | `html` (default), `text`, or `json` |
| `htmlmin` | `None` (config), `True`, or `False` |
| `compress` | `None` (config), `True`, or `False` |
| `cache` | `None` (config), `False`, integer (seconds), or `'METHOD-seconds'` (e.g. `GET-3600`, `GET\|POST-600`) |

## Development

```shell
make install-dev   # Install with test deps
make test         # Run tests
make run          # Run demo app
make help         # List targets
```

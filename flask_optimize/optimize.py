__author__ = 'sunary'


import sys
from htmlmin.main import minify
from flask import request, Response, make_response, current_app, json, wrappers
from functools import update_wrapper
import gzip
import time


IS_PYTHON_3 = True
if sys.version_info[0] < 3:
    from StringIO import StringIO
    IS_PYTHON_3 = False
else:
    from io import BytesIO


class FlaskOptimize(object):

    _cache = {}
    _timestamp = {}

    def __init__(self,
                 config=None):
        """
        Global config for flask optimize foreach respond return type
        Args:
            app: flask app object
            config: global configure values
        """
        if config is None:
            config = {
                        'html': {'htmlmin': True,  'compress': True, 'cache': 'GET-84600'},
                        'json': {'htmlmin': False, 'compress': True, 'cache': False},
                        'text': {'htmlmin': False, 'compress': True, 'cache': 'GET-84600'}
                     }

        self.config = config

    def optimize(self,
                 dtype='html',
                 htmlmin=None,
                 compress=None,
                 cache=None):
        """
        Flask optimize respond using minify html, zip content and mem cache.
        Elastic optimization and create Cross-site HTTP requests if respond is json
        Args:
            dtype: response type:
                - `html` (default)
                - `text`
                - `json`
            htmlmin: minify html
                None (default): using global config,
                False: disable minify html
                True: enable minify html
            compress: send content in compress (gzip) format
                None (default): using global config,
                False: disable compress response,
                True: enable compress response
            cache: cache content in RAM
                None (default): using global config,
                False: disable cache,
                integer: cache all method with period
                string value: 'METHOD-seconds' to select METHOD and period cache, eg: 'GET-3600', 'GET|POST-600', ...
        Examples:
            @optimize(dtype='html', htmlmin=True, compress=True, cache='GET-84600')
        """

        def _decorating_wrapper(func):

            def _optimize_wrapper(*args, **kwargs):
                # default values:
                is_htmlmin = False
                is_compress = False
                period_cache = 0

                if self.config.get(dtype):
                    is_htmlmin = self.config.get(dtype)['htmlmin'] if (htmlmin is None) else htmlmin
                    is_compress = self.config.get(dtype)['compress'] if (compress is None) else compress
                    cache_agrs = self.config.get(dtype)['cache'] if (cache is None) else cache

                    if cache is False or cache == 0:
                        period_cache = 0
                    elif isinstance(cache_agrs, int):
                        period_cache = cache_agrs
                    elif isinstance(cache_agrs, (str, basestring)) and len(cache_agrs.split('-')) == 2:
                        try:
                            period_cache = int(cache_agrs.split('-')[1]) if (request.method in cache_agrs) else 0
                        except (KeyError, ValueError):
                            raise ValueError('Cache must be string with method and period cache split by "-"')
                    else:
                        raise ValueError('Cache must be False, int or string with method and period cache split by "-"')

                # init cached data
                now = time.time()
                key_cache = request.url

                if self._timestamp.get(key_cache) > now:
                    return self._cache[key_cache]

                resp = func(*args, **kwargs)

                if not isinstance(resp, wrappers.Response):
                    # crossdomain
                    if dtype == 'json':
                        resp = self.crossdomain(resp)

                    # min html
                    if is_htmlmin:
                        resp = self.validate(self.minifier, resp)

                    # compress
                    if is_compress:
                        resp = self.validate(self.compress, resp)

                # cache
                if period_cache > 0:
                    self._cache[key_cache] = resp
                    self._timestamp[key_cache] = now + period_cache

                return resp

            return update_wrapper(_optimize_wrapper, func)

        return _decorating_wrapper

    @staticmethod
    def validate(method, content):
        instances_compare = (str, Response) if IS_PYTHON_3 else (str, unicode, Response)
        if isinstance(content, instances_compare):
            return method(content)
        elif isinstance(content, tuple):
            if len(content) < 2:
                raise TypeError('Content must have larger than 2 elements')

            return method(content[0]), content[1]

        return content

    @staticmethod
    def minifier(content):
        if not IS_PYTHON_3 and isinstance(content, str):
            content = unicode(content, 'utf-8')

        return minify(content,
                      remove_comments=True,
                      reduce_empty_attributes=True,
                      remove_optional_attribute_quotes=False)

    @staticmethod
    def compress(content):
        """
        Compress str, unicode content using gzip
        """
        resp = Response()
        if isinstance(content, Response):
            resp = content
            content = resp.data

        if not IS_PYTHON_3 and isinstance(content, unicode):
            content = content.encode('utf8')

        if IS_PYTHON_3:
            gzip_buffer = BytesIO()
            gzip_file = gzip.GzipFile(fileobj=gzip_buffer, mode='wb')
            gzip_file.write(bytes(content, 'utf-8'))
        else:
            gzip_buffer = StringIO()
            gzip_file = gzip.GzipFile(fileobj=gzip_buffer, mode='wb')
            gzip_file.write(content)

        gzip_file.close()

        resp.data = gzip_buffer.getvalue()
        resp.headers['Content-Encoding'] = 'gzip'
        resp.headers['Vary'] = 'Accept-Encoding'
        resp.headers['Content-Length'] = len(resp.data)

        return resp

    @staticmethod
    def crossdomain(content):
        """
        Create decorator Cross-site HTTP requests
        see more at: http://flask.pocoo.org/snippets/56/
        """
        if isinstance(content, (dict, Response)):
            if isinstance(content, dict):
                content = json.jsonify(content)
                resp = make_response(content)
            elif isinstance(content, Response):
                resp = content

            h = resp.headers
            h['Access-Control-Allow-Origin'] = '*'
            h['Access-Control-Allow-Methods'] = current_app.make_default_options_response().headers['allow']
            h['Access-Control-Max-Age'] = '21600'

            return resp

        return content


if __name__ == '__main__':
    flask_optimize = FlaskOptimize()
    flask_optimize.optimize('html')
    flask_optimize.optimize('json')
    flask_optimize.optimize('text')

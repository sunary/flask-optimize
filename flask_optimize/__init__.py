__author__ = 'sunary'


from htmlmin.main import minify
from flask import request, Response, make_response, current_app, redirect, json, wrappers, url_for
from functools import update_wrapper
import gzip
import time

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class FlaskOptimize(object):

    _cache = {}
    _timestamp = {}

    def __init__(self, app=None, config=None, config_update={}, redis=None):
        ''' Global config for flask optimize foreach respond return type
        Args:
            app: flask app object
            config: global configure values
            config_update: update into default configure
            redis: redis client store limit requests if you enable it
        '''
        if config is None:
            config = {'html': {'htmlmin': True,  'izip': True, 'cache': 'GET-84600'},
                      'json': {'htmlmin': False, 'izip': True, 'cache': False},
                      'text': {'htmlmin': False, 'izip': True, 'cache': 84600},
                      'limit': [100, 60, 84600],
                      'redirect_host': [],
                      'exceed_msg': None}
        config.update(config_update)

        self.config = config
        self.redis = redis
        self.app = app

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        if app.config.get('OPTIMIZE_ALL_RESPONSE'):
            app.after_request(self.after_request)

    def after_request(self, response, type='html', htmlmin=None, izip=None):
        response.direct_passthrough = False

        app = self.app or current_app
        load_config = self.config[type]

        htmlmin_arg = load_config['htmlmin'] if (htmlmin is None) else htmlmin
        izip_arg = load_config['izip'] if (izip is None) else izip

        # crossdomain
        if response.mimetype == 'application/json':
            response = self.crossdomain(response)

        # min html
        if htmlmin_arg:
            try:
                content = response.data.decode('utf8')
                response.data = self.validate(minify, content).encode('utf8')
            except:
                pass

        # gzip
        if izip_arg:
            response = self.validate(self.zipper, response)

        return response

    def optimize(self, type='html', htmlmin=None, izip=None, cache=None, limit=False, redirect_host=True, exceed_msg=True):
        ''' Flask optimize respond using minify html, zip content and mem cache.
        Elastic optimization and create Cross-site HTTP requests if respond is json
        Args:
            type: respond return type
                -html
                -text
                -json
            htmlmin: minify html
                None is using global config, True is enable minify html
            izip: send content in zip format
                None is using global config, True is enable zip respond
            cache: cache content in RAM
                None is using global config, False or 0 to disable cache,
                integer value to set time cache (seconds),
                or string format: 'METHOD-seconds' to select METHOD cache, eg: 'GET-3600'
            limit: limit requests for each windows and set time temporary ban
                True if you want using default value,
                using this format [requests, window, ban expire] to set value,
                False is disable it
            redirect_host: you have 2 or more domains and want redirect all to one
                True if you want using default value,
                using this format [['host1', 'host2], 'host_redirect'] to set value,
                False is disable it
            exceed_msg: return temporary ban content
                True if you want using default value,
        Examples:
            @optimize(type='html', htmlmin=True, zip=True, cache='GET-84600')
        '''

        def _decorating_wrapper(func):

            def _optimize_wrapper(*args, **kwargs):
                try:
                    load_config = self.config[type]

                    htmlmin_arg = load_config['htmlmin'] if (htmlmin is None) else htmlmin
                    izip_arg = load_config['izip'] if (izip is None) else izip
                    cache_arg = load_config['cache'] if (cache is None) else cache

                    if isinstance(cache_arg, str) and request.method in cache_arg:
                        cache_arg = int(cache_arg.split('-')[1])
                    elif not isinstance(cache_arg, int):
                        cache_arg = 0

                    limit_arg = self.config['limit'] if (limit is True) else limit
                    redirect_host_arg = self.config['redirect_host'] if (redirect_host is True) else redirect_host
                    exceed_msg_arg = self.config['exceed_msg'] if (exceed_msg is True) else exceed_msg
                except:
                    raise 'Wrong input format'

                # limit by ip
                if limit_arg and self.redis:
                    limit_key = 'limitip-{}'.format(request.remote_addr)
                    ban_key = 'banip-{}'.format(request.remote_addr)

                    times_requested = int(self.redis.get(limit_key) or '0')
                    if times_requested >= limit_arg[0] or self.redis.get(ban_key):
                        if times_requested >= limit_arg[0]:
                            self.redis.delete(limit_key)
                            self.redis.set(ban_key, 1)
                            self.redis.expire(ban_key, limit_arg[2])

                        if self.config['exceed_msg']:
                            return redirect(url_for(exceed_msg_arg))
                        else:
                            return self.crossdomain({'status_code': 429})
                    else:
                        self.redis.incr(limit_key, 1)
                        self.redis.expire(limit_key, limit_arg[1])

                # redirect new host
                if redirect_host_arg:
                    for host in redirect_host_arg[0]:
                        if host in request.url_root:
                            redirect_url = request.url
                            redirect_url = redirect_url.replace(host, redirect_host_arg[1])
                            return redirect(redirect_url)

                # find cached value
                if cache_arg:
                    now = time.time()
                    key_cache = request.url

                    if self._timestamp.get(key_cache, now) > now:
                        return self._cache[key_cache]

                resp = func(*args, **kwargs)

                if not isinstance(resp, wrappers.Response):
                    # crossdomain
                    if type == 'json':
                        resp = self.crossdomain(resp)

                    # min html
                    if htmlmin_arg:
                        resp = self.validate(minify, resp)

                    # gzip
                    if izip_arg:
                        resp = self.validate(self.zipper, resp)

                # cache
                if cache_arg:
                    self._cache[key_cache] = resp
                    self._timestamp[key_cache] = now + cache_arg

                return resp

            return update_wrapper(_optimize_wrapper, func)

        return _decorating_wrapper

    @staticmethod
    def validate(method, content):
        if isinstance(content, (str, unicode, Response)):
            return method(content)
        elif isinstance(content, tuple):
            return method(content[0]), content[1]

        return content

    @staticmethod
    def zipper(content):
        ''' Zip str, unicode type content
        '''
        resp = Response()
        if isinstance(content, Response):
            resp = content
            content = resp.data

        if isinstance(content, unicode):
            content = content.encode('utf8')

        gzip_buffer = StringIO()
        gzip_file = gzip.GzipFile(mode='wb', fileobj=gzip_buffer)
        gzip_file.write(content)
        gzip_file.close()

        resp.data = gzip_buffer.getvalue()
        resp.headers['Content-Encoding'] = 'gzip'
        resp.headers['Vary'] = 'Accept-Encoding'
        resp.headers['Content-Length'] = len(resp.data)

        return resp

    @staticmethod
    def crossdomain(content):
        ''' create Cross-site HTTP requests
        '''
        if isinstance(content, (dict, Response)):
            if isinstance(content, dict):
                content = json.jsonify(content)
                resp = make_response(content)

            if isinstance(content, Response):
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

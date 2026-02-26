__author__ = "sunary"


import gzip
import time
from io import BytesIO
import minify_html
from flask import request, Response, make_response, current_app, json, wrappers
from functools import update_wrapper, partial


class FlaskOptimize(object):

    _cache = {}
    _timestamp = {}

    _default_config = {
        "html": {"htmlmin": True, "compress": True, "cache": "GET-84600"},
        "json": {"htmlmin": False, "compress": True, "cache": False},
        "text": {"htmlmin": False, "compress": True, "cache": "GET-84600"},
        "trim_fragment": False,
    }

    def __init__(self, config=None):
        """
        Global config for flask optimize foreach respond return type
        Args:
            config: global configure values (dict), or Flask app instance.
                   When Flask app is passed, uses app.config['FLASK_OPTIMIZE'] or defaults.
        """
        if config is None:
            self.config = self._default_config.copy()
        elif isinstance(config, dict) and "html" in config:
            self.config = config
        elif hasattr(config, "config"):
            # Flask app passed - use FLASK_OPTIMIZE from app.config or defaults
            self.config = config.config.get(
                "FLASK_OPTIMIZE", self._default_config.copy()
            )
        else:
            self.config = config or self._default_config.copy()

    def optimize(self, dtype="html", htmlmin=None, compress=None, cache=None):
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
                    is_htmlmin = (
                        self.config.get(dtype)["htmlmin"]
                        if htmlmin is None
                        else htmlmin
                    )
                    is_compress = (
                        self.config.get(dtype)["compress"]
                        if compress is None
                        else compress
                    )
                    cache_args = (
                        self.config.get(dtype)["cache"] if cache is None else cache
                    )

                    if cache_args is False or cache_args == 0:
                        period_cache = 0
                    elif isinstance(cache_args, int):
                        period_cache = cache_args
                    elif (
                        isinstance(cache_args, str) and len(cache_args.split("-")) == 2
                    ):
                        try:
                            methods_part, period_str = cache_args.split("-")
                            allowed_methods = methods_part.split("|")
                            if request.method in allowed_methods:
                                period_cache = int(period_str)
                            else:
                                period_cache = 0
                        except (KeyError, ValueError):
                            raise ValueError(
                                'Cache must be string with method and period cache split by "-"'
                            )
                    else:
                        raise ValueError(
                            'Cache must be False, int or string with method and period cache split by "-"'
                        )

                # init cached data
                now = time.time()
                key_cache = request.method + request.url
                if self.config.get("trim_fragment"):
                    key_cache = key_cache.split("#")[0]

                if period_cache > 0 and self._timestamp.get(key_cache, 0) > now:
                    cached = self._cache.get(key_cache)
                    if cached is not None:
                        return cached

                resp = func(*args, **kwargs)

                if not isinstance(resp, wrappers.Response):
                    # crossdomain
                    if dtype == "json":
                        resp = self.crossdomain(resp)

                    # min html
                    if is_htmlmin:
                        resp = self.validate(self.minifier, resp)

                    # compress
                    if is_compress:
                        content_type = {
                            "html": "text/html",
                            "json": "application/json",
                            "text": "text/plain",
                        }.get(dtype, "application/octet-stream")
                        resp = self.validate(
                            partial(self.compress, content_type=content_type), resp
                        )

                # cache
                if period_cache > 0:
                    self._evict_expired_cache(now)
                    self._cache[key_cache] = resp
                    self._timestamp[key_cache] = now + period_cache

                return resp

            return update_wrapper(_optimize_wrapper, func)

        return _decorating_wrapper

    @classmethod
    def _evict_expired_cache(cls, now):
        """Remove expired entries from cache to prevent unbounded growth."""
        expired = [k for k, expiry in cls._timestamp.items() if expiry <= now]
        for k in expired:
            cls._cache.pop(k, None)
            cls._timestamp.pop(k, None)

    @staticmethod
    def validate(method, content):
        instances_compare = (str, Response)
        if isinstance(content, instances_compare):
            return method(content)
        elif isinstance(content, tuple):
            if len(content) < 2:
                raise TypeError("Content must have at least 2 elements")

            result = (method(content[0]),)
            return result + content[1:]

        return content

    @staticmethod
    def minifier(content):
        return minify_html.minify(content, keep_comments=False)

    @staticmethod
    def compress(content, content_type=None):
        """
        Compress str content using gzip
        """
        resp = Response()
        if isinstance(content, Response):
            resp = content
            content = resp.data
        elif content_type:
            resp.headers["Content-Type"] = content_type

        if isinstance(content, str):
            content = content.encode("utf-8")

        gzip_buffer = BytesIO()
        with gzip.GzipFile(fileobj=gzip_buffer, mode="wb") as gzip_file:
            gzip_file.write(content)

        resp.data = gzip_buffer.getvalue()
        resp.headers["Content-Encoding"] = "gzip"
        resp.headers["Vary"] = "Accept-Encoding"
        resp.headers["Content-Length"] = len(resp.data)

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
            h["Access-Control-Allow-Origin"] = "*"
            h["Access-Control-Allow-Methods"] = (
                current_app.make_default_options_response().headers["allow"]
            )
            h["Access-Control-Max-Age"] = "21600"

            return resp

        return content


if __name__ == "__main__":
    flask_optimize = FlaskOptimize()
    flask_optimize.optimize("html")
    flask_optimize.optimize("json")
    flask_optimize.optimize("text")

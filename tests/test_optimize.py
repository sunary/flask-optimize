"""Tests for flask_optimize.optimize module."""

import gzip
import pytest

from flask import Flask, Response
from flask_optimize import FlaskOptimize


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    return Flask(__name__)


@pytest.fixture
def clear_cache():
    """Clear class-level cache before and after test."""
    FlaskOptimize._cache.clear()
    FlaskOptimize._timestamp.clear()
    yield
    FlaskOptimize._cache.clear()
    FlaskOptimize._timestamp.clear()


class TestFlaskOptimizeInit:
    """Tests for FlaskOptimize.__init__."""

    def test_init_with_none_uses_default_config(self):
        fo = FlaskOptimize()
        assert fo.config.get("html")["htmlmin"] is True
        assert fo.config.get("html")["compress"] is True
        assert fo.config.get("json")["cache"] is False

    def test_init_with_config_dict(self):
        config = {
            "html": {"htmlmin": False, "compress": False, "cache": False},
            "json": {"htmlmin": False, "compress": True, "cache": False},
            "text": {"htmlmin": False, "compress": True, "cache": False},
            "trim_fragment": True,
        }
        fo = FlaskOptimize(config)
        assert fo.config["html"]["htmlmin"] is False
        assert fo.config["trim_fragment"] is True

    def test_init_with_flask_app_uses_defaults(self, app):
        fo = FlaskOptimize(app)
        assert fo.config.get("html")["htmlmin"] is True

    def test_init_with_flask_app_uses_flask_optimize_config(self, app):
        app.config["FLASK_OPTIMIZE"] = {
            "html": {"htmlmin": False, "compress": False, "cache": False},
            "json": {"htmlmin": False, "compress": True, "cache": False},
            "text": {"htmlmin": False, "compress": True, "cache": False},
            "trim_fragment": True,
        }
        fo = FlaskOptimize(app)
        assert fo.config["html"]["htmlmin"] is False
        assert fo.config["trim_fragment"] is True


class TestValidate:
    """Tests for FlaskOptimize.validate."""

    def test_validate_with_string(self):
        def upper(s):
            return s.upper()

        result = FlaskOptimize.validate(upper, "hello")
        assert result == "HELLO"

    def test_validate_with_response(self):
        def add_header(content):
            content.headers["X-Custom"] = "yes"
            return content

        resp = Response("ok")
        result = FlaskOptimize.validate(add_header, resp)
        assert result.headers["X-Custom"] == "yes"

    def test_validate_with_tuple_two_elements(self):
        def double(x):
            return str(int(x) * 2)

        result = FlaskOptimize.validate(double, ("21", 200))
        assert result == ("42", 200)

    def test_validate_with_tuple_three_elements_preserves_headers(self):
        def double(x):
            return str(int(x) * 2)

        result = FlaskOptimize.validate(double, ("21", 200, {"X-Header": "value"}))
        assert result == ("42", 200, {"X-Header": "value"})

    def test_validate_with_tuple_raises_if_less_than_two_elements(self):
        def identity(x):
            return x

        with pytest.raises(TypeError, match="at least 2 elements"):
            FlaskOptimize.validate(identity, ("only_one",))

    def test_validate_with_other_type_returns_unchanged(self):
        def identity(x):
            return x

        result = FlaskOptimize.validate(identity, 42)
        assert result == 42


class TestMinifier:
    """Tests for FlaskOptimize.minifier."""

    def test_minifier_removes_comments(self):
        html = "<html><!-- comment --><body>text</body></html>"
        result = FlaskOptimize.minifier(html)
        assert "comment" not in result
        assert "text" in result

    def test_minifier_reduces_whitespace(self):
        html = "<html>  <body>   \n  content  </body>  </html>"
        result = FlaskOptimize.minifier(html)
        assert "content" in result


class TestCompress:
    """Tests for FlaskOptimize.compress."""

    def test_compress_string(self):
        content = "hello world"
        result = FlaskOptimize.compress(content, content_type="text/plain")
        assert result.headers["Content-Encoding"] == "gzip"
        assert result.headers["Content-Type"] == "text/plain"
        assert result.headers["Vary"] == "Accept-Encoding"

        # Decompress and verify
        decompressed = gzip.decompress(result.data)
        assert decompressed.decode("utf-8") == content

    def test_compress_response(self):
        resp = Response("original content")
        resp.headers["Content-Type"] = "text/html"
        result = FlaskOptimize.compress(resp)
        assert result.headers["Content-Encoding"] == "gzip"
        assert result.headers["Content-Type"] == "text/html"
        decompressed = gzip.decompress(result.data)
        assert decompressed.decode("utf-8") == "original content"

    def test_compress_without_content_type_for_string(self):
        result = FlaskOptimize.compress("data")
        assert result.headers["Content-Encoding"] == "gzip"
        assert (
            "Content-Type" not in result.headers
            or result.headers.get("Content-Type") != "text/html"
        )


class TestCrossdomain:
    """Tests for FlaskOptimize.crossdomain."""

    def test_crossdomain_with_dict(self, app):
        @app.route("/")
        def index():
            return FlaskOptimize.crossdomain({"key": "value"})

        with app.test_client() as client:
            resp = client.get("/")
            assert resp.headers["Access-Control-Allow-Origin"] == "*"
            assert "Access-Control-Allow-Methods" in resp.headers
            assert resp.headers["Access-Control-Max-Age"] == "21600"

    def test_crossdomain_with_response(self, app):
        @app.route("/")
        def index():
            return FlaskOptimize.crossdomain(Response("ok"))

        with app.test_client() as client:
            resp = client.get("/")
            assert resp.headers["Access-Control-Allow-Origin"] == "*"

    def test_crossdomain_with_other_returns_unchanged(self, app):
        with app.app_context():
            result = FlaskOptimize.crossdomain("plain string")
            assert result == "plain string"


class TestEvictExpiredCache:
    """Tests for FlaskOptimize._evict_expired_cache."""

    def test_evict_expired_cache_removes_expired_entries(self, clear_cache):
        now = 1000.0
        FlaskOptimize._cache["key1"] = "cached1"
        FlaskOptimize._timestamp["key1"] = 999.0  # expired
        FlaskOptimize._cache["key2"] = "cached2"
        FlaskOptimize._timestamp["key2"] = 1001.0  # not expired

        FlaskOptimize._evict_expired_cache(now)

        assert "key1" not in FlaskOptimize._cache
        assert "key1" not in FlaskOptimize._timestamp
        assert FlaskOptimize._cache["key2"] == "cached2"
        assert FlaskOptimize._timestamp["key2"] == 1001.0


class TestOptimizeDecorator:
    """Tests for FlaskOptimize.optimize decorator."""

    def test_optimize_html_minifies_and_compresses(self, app, clear_cache):
        fo = FlaskOptimize(
            {"html": {"htmlmin": True, "compress": True, "cache": False}}
        )

        @app.route("/html")
        @fo.optimize(dtype="html")
        def html_route():
            return "<html>  <body>  content  </body>  </html>"

        with app.test_client() as client:
            resp = client.get("/html", headers={"Accept-Encoding": "gzip"})
            assert resp.headers.get("Content-Encoding") == "gzip"
            # Minified content should have reduced whitespace
            data = gzip.decompress(resp.data).decode("utf-8")
            assert "content" in data

    def test_optimize_json_adds_cors_headers(self, app, clear_cache):
        fo = FlaskOptimize(
            {"json": {"htmlmin": False, "compress": True, "cache": False}}
        )

        @app.route("/json")
        @fo.optimize(dtype="json")
        def json_route():
            return {"data": "value"}

        with app.test_client() as client:
            resp = client.get("/json")
            assert resp.headers["Access-Control-Allow-Origin"] == "*"

    def test_optimize_cache_get_request(self, app, clear_cache):
        fo = FlaskOptimize(
            {"html": {"htmlmin": False, "compress": False, "cache": "GET-3600"}}
        )
        call_count = 0

        @app.route("/cached")
        @fo.optimize(dtype="html")
        def cached_route():
            nonlocal call_count
            call_count += 1
            return f"response-{call_count}"

        with app.test_client() as client:
            r1 = client.get("/cached")
            r2 = client.get("/cached")
            assert r1.data == r2.data
            assert call_count == 1

    def test_optimize_cache_post_not_cached_with_get_only(self, app, clear_cache):
        fo = FlaskOptimize(
            {"html": {"htmlmin": False, "compress": False, "cache": "GET-3600"}}
        )
        call_count = 0

        @app.route("/cached", methods=["GET", "POST"])
        @fo.optimize(dtype="html")
        def cached_route():
            nonlocal call_count
            call_count += 1
            return f"response-{call_count}"

        with app.test_client() as client:
            client.get("/cached")
            client.post("/cached")
            client.post("/cached")
            assert call_count == 3

    def test_optimize_cache_get_post_format(self, app, clear_cache):
        fo = FlaskOptimize(
            {"html": {"htmlmin": False, "compress": False, "cache": "GET|POST-3600"}}
        )
        call_count = 0

        @app.route("/cached", methods=["GET", "POST"])
        @fo.optimize(dtype="html")
        def cached_route():
            nonlocal call_count
            call_count += 1
            return f"response-{call_count}"

        with app.test_client() as client:
            client.get("/cached")
            client.get("/cached")
            client.post("/cached")
            client.post("/cached")
            assert call_count == 2

    def test_optimize_cache_disabled(self, app, clear_cache):
        fo = FlaskOptimize(
            {"html": {"htmlmin": False, "compress": False, "cache": False}}
        )
        call_count = 0

        @app.route("/nocache")
        @fo.optimize(dtype="html")
        def nocache_route():
            nonlocal call_count
            call_count += 1
            return "ok"

        with app.test_client() as client:
            client.get("/nocache")
            client.get("/nocache")
            assert call_count == 2

    def test_optimize_override_htmlmin(self, app, clear_cache):
        fo = FlaskOptimize(
            {"html": {"htmlmin": True, "compress": False, "cache": False}}
        )

        @app.route("/no-min")
        @fo.optimize(dtype="html", htmlmin=False)
        def no_min_route():
            return "<html>  <body>  preserve  </body>  </html>"

        with app.test_client() as client:
            resp = client.get("/no-min")
            # Should NOT be minified (override)
            assert "  " in resp.data.decode("utf-8")

    def test_optimize_returns_tuple_status_headers(self, app, clear_cache):
        fo = FlaskOptimize(
            {"html": {"htmlmin": False, "compress": False, "cache": False}}
        )

        @app.route("/tuple")
        @fo.optimize(dtype="html")
        def tuple_route():
            return "body", 201, {"X-Custom": "header"}

        with app.test_client() as client:
            resp = client.get("/tuple")
            assert resp.status_code == 201
            assert resp.headers.get("X-Custom") == "header"

    def test_optimize_invalid_cache_string_raises(self, app):
        fo = FlaskOptimize(
            {"html": {"htmlmin": False, "compress": False, "cache": "GET-abc"}}
        )

        @app.route("/bad")
        @fo.optimize(dtype="html")
        def bad_route():
            return "ok"

        with app.test_client() as client:
            resp = client.get("/bad")
            # 'GET-abc' causes ValueError when int('abc') fails
            assert resp.status_code == 500

    def test_optimize_trim_fragment_config(self):
        """trim_fragment config is applied; fragment not sent in HTTP so we only verify config."""
        fo = FlaskOptimize(
            {
                "html": {"htmlmin": False, "compress": False, "cache": False},
                "json": {"htmlmin": False, "compress": False, "cache": False},
                "text": {"htmlmin": False, "compress": False, "cache": False},
                "trim_fragment": True,
            }
        )
        assert fo.config["trim_fragment"] is True

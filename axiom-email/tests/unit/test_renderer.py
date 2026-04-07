"""Unit tests for axiom.email.templating.jinja2."""

import pytest

from axiom.email.exception import EmailRenderError
from axiom.email.templating.jinja2 import JinjaTemplateRenderer


class TestJinjaTemplateRenderer:
    def setup_method(self):
        self.renderer = JinjaTemplateRenderer()

    def test_render_variable(self):
        result = self.renderer.render("Hello {{ name }}!", {"name": "World"})
        assert result == "Hello World!"

    def test_render_conditional(self):
        tmpl = "{% if flag %}yes{% else %}no{% endif %}"
        assert self.renderer.render(tmpl, {"flag": True}) == "yes"
        assert self.renderer.render(tmpl, {"flag": False}) == "no"

    def test_render_filter(self):
        result = self.renderer.render("{{ name | upper }}", {"name": "hello"})
        assert result == "HELLO"

    def test_render_loop(self):
        result = self.renderer.render("{% for i in items %}{{ i }}{% endfor %}", {"items": [1, 2, 3]})
        assert result == "123"

    def test_render_empty_context(self):
        result = self.renderer.render("static text", {})
        assert result == "static text"

    def test_invalid_template_raises_render_error(self):
        with pytest.raises(EmailRenderError):
            self.renderer.render("{% for x in %}broken{% endfor %}", {})

    def test_undefined_variable_renders_empty(self):
        # Jinja2 by default renders undefined as empty string
        result = self.renderer.render("{{ undefined_var }}", {})
        assert result == ""

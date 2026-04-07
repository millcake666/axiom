"""axiom.email.templating.jinja2 — Jinja2-based email template renderer."""

from typing import Any

try:
    import jinja2
except ImportError as exc:
    raise ImportError(
        "jinja2 is required for JinjaTemplateRenderer. "
        "Install it with: pip install axiom-email[jinja2]"
    ) from exc

from axiom.email.exception import EmailRenderError


class JinjaTemplateRenderer:
    """Renders email templates from Jinja2 template strings."""

    def render(self, template: str, context: dict[str, Any]) -> str:
        """Render a Jinja2 template string with the given context.

        Args:
            template: Jinja2 template source string.
            context: Variables to inject into the template.

        Returns:
            Rendered string output.

        Raises:
            EmailRenderError: If the template fails to render.
        """
        try:
            tmpl = jinja2.Template(template)
            return tmpl.render(**context)
        except jinja2.TemplateError as exc:
            raise EmailRenderError(f"Template rendering failed: {exc}") from exc


__all__ = ["JinjaTemplateRenderer"]

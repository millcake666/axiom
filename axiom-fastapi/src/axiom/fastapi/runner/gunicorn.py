"""axiom.fastapi.runner.gunicorn — Gunicorn runner with UvicornWorker."""

try:
    import uvloop as _uvloop  # noqa: F401

    _LOOP = "uvloop"
except ImportError:
    _LOOP = "asyncio"

from pydantic import BaseModel


class GunicornSettings(BaseModel):
    """Settings for the gunicorn runner."""

    host: str = "0.0.0.0"  # noqa: S104  # nosec B104
    port: int = 8000
    workers: int = 1
    timeout: int = 30
    worker_class: str = "axiom.fastapi.runner.gunicorn.UvicornWorker"


try:
    from gunicorn.app.base import BaseApplication  # type: ignore[import-untyped]
    from uvicorn.workers import UvicornWorker as BaseUvicornWorker

    class UvicornWorker(BaseUvicornWorker):
        """Uvicorn worker configured with uvloop, httptools, and factory mode."""

        CONFIG_KWARGS = {
            "loop": _LOOP,
            "http": "httptools",
            "lifespan": "on",
            "factory": True,
            "proxy_headers": False,
        }

    class GunicornApplication(BaseApplication):  # type: ignore[misc]
        """Gunicorn application wrapper for axiom FastAPI apps."""

        def __init__(
            self,
            app: str,
            host: str,
            port: int,
            workers: int,
            worker_class: str = "axiom.fastapi.runner.gunicorn.UvicornWorker",
            timeout: int = 30,
            **kwargs: object,
        ) -> None:
            """Initialize GunicornApplication.

            Args:
                app: Import string for the ASGI application factory.
                host: Bind host.
                port: Bind port.
                workers: Number of worker processes.
                worker_class: Dotted path to worker class.
                timeout: Worker timeout in seconds.
                **kwargs: Additional gunicorn options.
            """
            self.app = app
            self.options = {
                "bind": f"{host}:{port}",
                "workers": workers,
                "worker_class": worker_class,
                "timeout": timeout,
                **kwargs,
            }
            super().__init__()

        def load_config(self) -> None:
            """Load gunicorn configuration from options."""
            for key, value in self.options.items():
                if key in self.cfg.settings and value is not None:
                    self.cfg.set(key.lower(), value)

        def load(self) -> str:
            """Return the application import string."""
            return self.app

except ImportError:
    pass


def run_gunicorn(app: str, settings: GunicornSettings) -> None:
    """Start the gunicorn server.

    Args:
        app: Import string for the ASGI application factory.
        settings: Gunicorn configuration.
    """
    GunicornApplication(  # type: ignore[name-defined]
        app=app,
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        worker_class=settings.worker_class,
        timeout=settings.timeout,
    ).run()

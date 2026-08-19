import os
from typing import Any

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django_application = get_asgi_application()


def build_application() -> Any:
    from apps.accounts.ws import CookieJWTWebSocketMiddleware
    from apps.comments.routing import websocket_urlpatterns
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.security.websocket import AllowedHostsOriginValidator

    return ProtocolTypeRouter(
        {
            "http": django_application,
            "websocket": AllowedHostsOriginValidator(
                CookieJWTWebSocketMiddleware(URLRouter(websocket_urlpatterns))
            ),
        }
    )


application = build_application()

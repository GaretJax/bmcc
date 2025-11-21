"""
ASGI config for edgar project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

# from django.core.asgi import get_asgi_application
# application = get_asgi_application()


# Workaround for this: https://github.com/encode/starlette/issues/664#issuecomment-698771946
from django.core.wsgi import get_wsgi_application

from a2wsgi import WSGIMiddleware


application = WSGIMiddleware(get_wsgi_application())

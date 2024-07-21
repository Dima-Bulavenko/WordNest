from typing import Callable

from django.contrib.messages import get_messages
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string

# Implementation of the middleware class was taken from
# https://danjacob.net/posts/htmx_messages/ tutorial


class HtmxMessagesMiddleware:
    """Adds messages to HTMX response"""

    _hx_redirect_headers = frozenset(
        {
            "HX-Location",
            "HX-Redirect",
            "HX-Refresh",
        }
    )

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self._get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Middleware implementation"""
        response = self._get_response(request)

        if not request.htmx:
            return response

        if set(response.headers) & self._hx_redirect_headers:
            return response

        if get_messages(request):
            response.write(
                render_to_string(
                    template_name="messages.html",
                    context={"hx_oob": True},
                    request=request,
                )
            )

        return response

import json
from pathlib import Path

from django.http import JsonResponse, Http404
from django.views import View
from django.views.generic import TemplateView

from dictionary.search_manager import TranslationAPI


class IndexView(TemplateView):
    template_name = Path("dictionary", "index.html")

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            title = "WordNest Online Dictionary"
        else:
            title = "Welcome"

        context_data["title"] = title
        return context_data

    def get_template_names(self):
        if not self.request.user.is_authenticated:
            result = [Path("welcome.html")]
        else:
            result = super().get_template_names()

        return result


class TranslationView(View):
    def post(self, request, *args, **kwargs):
        if self.is_ajax():
            data = json.loads(request.body.decode("utf-8"))
            client = TranslationAPI(**data)
            translation = client.translate()
            return JsonResponse(translation)
        raise Http404("Page not fount")

    def is_ajax(self) -> bool:
        """
        Checks if the request was made via AJAX.

        Returns:
            bool: True if the request was made via AJAX, False otherwise.
        """
        return self.request.headers.get("X-Requested-With") == "XMLHttpRequest"

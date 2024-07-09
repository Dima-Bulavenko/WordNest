import json
from pathlib import Path

from django.db import IntegrityError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import CreateView, DetailView, TemplateView

from dictionary.forms import DictionaryForm
from dictionary.models import Dictionary
from dictionary.search_manager import TranslationAPI


class IndexView(TemplateView):
    template_name = Path("dictionary", "index.html")

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            title = "WordNest Online Dictionary"
            context_data["dictionaries"] = self._get_dictionary()
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

    def _get_dictionary(self):
        return self.request.user.dictionaries.all()


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


class CreateDictionaryView(CreateView):
    model = Dictionary
    form_class = DictionaryForm
    template_name = "dictionary/dictionary_create.html"
    success_url = "/"

    def form_valid(self, form):
        form.instance.user = self.request.user
        try:
            return super().form_valid(form)
        except IntegrityError:
            form.add_error(
                None,
                "You already have a dictionary with these source and target languages.",
            )
            return render(self.request, self.template_name, {"form": form})


class DictionaryView(DetailView):
    model = Dictionary
    template_name = "dictionary/dictionary.html"
    context_object_name = "dictionary"

    def get_object(self):
        source = self.kwargs.get("source")
        target = self.kwargs.get("target")

        return get_object_or_404(
            self.request.user.dictionaries,
            source_language__code=source,
            target_language__code=target,
        )

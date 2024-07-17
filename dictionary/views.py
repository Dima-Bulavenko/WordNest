import json
from pathlib import Path

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView

from dictionary.forms import DictionaryForm
from dictionary.models import Dictionary
from dictionary.search_manager import translate
from wordnest.shortcuts import group_translations_by_from_word, normalize_string


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


class AJAXMixing:
    def setup(self, request, *args, **kwargs):
        if not self.is_ajax(request):
            raise Http404("Page not found")

        super().setup(request, *args, **kwargs)

    @staticmethod
    def is_ajax(request) -> bool:
        """
        Checks if the request was made via AJAX.

        Returns:
            bool: True if the request was made via AJAX, False otherwise.
        """
        return request.headers.get("X-Requested-With") == "XMLHttpRequest"


class TranslationView(AJAXMixing, View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body.decode("utf-8"))
        word = normalize_string(data.get("body"))
        from_lang = normalize_string(data.get("from_language"))
        to_lang = normalize_string(data.get("to_language"))
        user = request.user
        translation = translate(word, from_lang, to_lang, user)
        return JsonResponse(translation)


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


class DictionaryView(ListView):
    paginate_by = 25
    paginate_orphans = 10
    template_name = "dictionary/dictionary.html"
    context_object_name = "translations"

    def get_queryset(self):
        self.dictionary = self.get_object()
        search = self.request.GET.get("word")
        if search:
            search = normalize_string(search)
            queryset = self.dictionary.translations.filter(
                Q(from_word__word__startswith=search) |
                Q(to_word__word__startswith=search)
            )
        else:
            queryset = self.dictionary.translations.all()
        return group_translations_by_from_word(queryset)

    def get_template_names(self):
        names = []
        if self.request.htmx:
            names.append("dictionary/dictionary_word_list.html")
        else:
            names.append(self.template_name)
        return names

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["dictionary"] = self.dictionary
        context_data["query"] = self.request.GET.get("word", "")    
        return context_data
    
    def get_object(self):
        source = self.kwargs.get("source")
        target = self.kwargs.get("target")

        return get_object_or_404(
            self.request.user.dictionaries,
            source_language__code=source,
            target_language__code=target,
        )


class AddWordView(AJAXMixing, View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body.decode("utf-8"))
        try: 
            request.user.add_word_to_dictionary(
                data["source_language"], 
                data["target_language"], 
                data["word"], 
                data["translation"]
            )
            return HttpResponse()
        except ObjectDoesNotExist:
            return HttpResponseBadRequest()

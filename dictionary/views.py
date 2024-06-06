from pathlib import Path

from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = Path("dictionary", "index.html")
    extra_context = {"title": "WordNest Online Dictionary"}

    def get_template_names(self):
        if not self.request.user.is_authenticated:
            result = [Path("welcome.html")]
            self.extra_context["title"] = "Welcome"
        else:
            result = super().get_template_names()

        return result

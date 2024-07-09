from allauth.account.forms import LoginForm
from django import forms
from django.urls import NoReverseMatch, reverse
from django.utils.safestring import mark_safe

from dictionary.models import Dictionary


class LoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].help_text = None

    @property
    def forgot_pwd(self):
        try:
            reset_url = reverse("account_reset_password")
        except NoReverseMatch:
            pass
        else:
            forgot_txt = "Forgot your password?"
            return mark_safe(
                f'<div class="forgot_pwd align-center auth-link"><a href="{reset_url}">{forgot_txt}</a></div>'
            )


class DictionaryForm(forms.ModelForm):
    class Meta:
        select_attrs = {"class": "select_language"}
        model = Dictionary
        fields = ["source_language", "target_language"]
        widgets = {
            "source_language": forms.Select(attrs=select_attrs),
            "target_language": forms.Select(attrs=select_attrs),
        }

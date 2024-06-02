from allauth.account.forms import LoginForm
from django.urls import NoReverseMatch, reverse
from django.utils.safestring import mark_safe


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

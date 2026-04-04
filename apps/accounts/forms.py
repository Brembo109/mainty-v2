from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    SetPasswordForm,
)
from django.utils.translation import gettext_lazy as _

_FORM_INPUT_CLASS = "form-input"


class LoginForm(AuthenticationForm):
    """Login form with localised error messages and Vercel-dark CSS classes."""

    error_messages = {
        "invalid_login": _("Benutzername oder Passwort falsch."),
        "inactive": _("Dieses Konto ist deaktiviert."),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({
            "class": _FORM_INPUT_CLASS,
            "placeholder": "",
            "autofocus": True,
        })
        self.fields["password"].widget.attrs.update({
            "class": _FORM_INPUT_CLASS,
            "placeholder": "",
        })


def _apply_form_input_class(form):
    """Add the form-input CSS class to all fields of a form instance."""
    for field in form.fields.values():
        field.widget.attrs.setdefault("class", _FORM_INPUT_CLASS)


class StyledPasswordChangeForm(PasswordChangeForm):
    """PasswordChangeForm with Vercel-dark CSS classes on all fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_form_input_class(self)


class StyledSetPasswordForm(SetPasswordForm):
    """SetPasswordForm (used for reset + expired) with Vercel-dark CSS classes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_form_input_class(self)

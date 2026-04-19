from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    SetPasswordForm,
)
from django.utils.translation import gettext_lazy as _

from .constants import Role
from .models import User

_FORM_INPUT_CLASS = "form-input"
_FILTER_INPUT_CLASS = "filter-toolbar__inline-input"


class UserFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label=_("Suche"),
        widget=forms.TextInput(attrs={
            "class": _FILTER_INPUT_CLASS,
            "autocomplete": "off",
        }),
    )
    role = forms.ChoiceField(
        required=False,
        label=_("Rolle"),
        choices=[("", _("Alle Rollen"))] + Role.CHOICES,
        widget=forms.Select(attrs={"class": _FILTER_INPUT_CLASS}),
    )
    is_active = forms.ChoiceField(
        required=False,
        label=_("Status"),
        choices=[
            ("", _("Alle")),
            ("yes", _("Aktiv")),
            ("no", _("Inaktiv")),
        ],
        widget=forms.Select(attrs={"class": _FILTER_INPUT_CLASS}),
    )


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


class UserCreateForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=Role.CHOICES,
        label=_("Rolle"),
        widget=forms.Select(attrs={"class": _FORM_INPUT_CLASS}),
    )
    password1 = forms.CharField(
        label=_("Passwort"),
        widget=forms.PasswordInput(attrs={"class": _FORM_INPUT_CLASS}),
    )
    password2 = forms.CharField(
        label=_("Passwort bestätigen"),
        widget=forms.PasswordInput(attrs={"class": _FORM_INPUT_CLASS}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]
        widgets = {
            "username": forms.TextInput(attrs={"class": _FORM_INPUT_CLASS}),
            "email": forms.EmailInput(attrs={"class": _FORM_INPUT_CLASS}),
            "first_name": forms.TextInput(attrs={"class": _FORM_INPUT_CLASS}),
            "last_name": forms.TextInput(attrs={"class": _FORM_INPUT_CLASS}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", _("Die Passwörter stimmen nicht überein."))
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            user.set_role(self.cleaned_data["role"])
        else:
            _role = self.cleaned_data["role"]
            _orig_save_m2m = self.save_m2m

            def save_m2m():
                _orig_save_m2m()
                user.set_role(_role)

            self.save_m2m = save_m2m
        return user


class UserUpdateForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=Role.CHOICES,
        label=_("Rolle"),
        widget=forms.Select(attrs={"class": _FORM_INPUT_CLASS}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "is_active"]
        widgets = {
            "username": forms.TextInput(attrs={"class": _FORM_INPUT_CLASS}),
            "email": forms.EmailInput(attrs={"class": _FORM_INPUT_CLASS}),
            "first_name": forms.TextInput(attrs={"class": _FORM_INPUT_CLASS}),
            "last_name": forms.TextInput(attrs={"class": _FORM_INPUT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["role"].initial = self.instance.role

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            user.set_role(self.cleaned_data["role"])
        else:
            _role = self.cleaned_data["role"]
            _orig_save_m2m = self.save_m2m

            def save_m2m():
                _orig_save_m2m()
                user.set_role(_role)

            self.save_m2m = save_m2m
        return user


class AdminSetPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label=_("Neues Passwort"),
        widget=forms.PasswordInput(attrs={"class": _FORM_INPUT_CLASS}),
    )
    new_password2 = forms.CharField(
        label=_("Passwort bestätigen"),
        widget=forms.PasswordInput(attrs={"class": _FORM_INPUT_CLASS}),
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password1")
        p2 = cleaned_data.get("new_password2")
        if p1 and p2 and p1 != p2:
            self.add_error("new_password2", _("Die Passwörter stimmen nicht überein."))
        return cleaned_data

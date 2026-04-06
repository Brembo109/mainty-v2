from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),
    path("settings/", views.SettingsView.as_view(), name="settings"),
    path("settings/test-email/", views.SendTestEmailView.as_view(), name="settings-test-email"),
]

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),
    path("calendar/", views.CalendarView.as_view(), name="calendar"),
    path("calendar/day/", views.CalendarDayView.as_view(), name="calendar-day"),
    path("settings/", views.SettingsView.as_view(), name="settings"),
    path("settings/test-email/", views.SendTestEmailView.as_view(), name="settings-test-email"),
]

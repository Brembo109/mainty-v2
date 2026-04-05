from django.urls import path

from . import views

app_name = "qualification"

urlpatterns = [
    path("", views.QualificationCycleListView.as_view(), name="list"),
    path("new/", views.QualificationCycleCreateView.as_view(), name="create"),
    path("<int:pk>/", views.QualificationCycleDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.QualificationCycleUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.QualificationCycleDeleteView.as_view(), name="delete"),
    path("<int:pk>/sign/", views.QualificationSignView.as_view(), name="sign"),
]

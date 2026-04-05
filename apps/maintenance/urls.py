from django.urls import path

from . import views

app_name = "maintenance"

urlpatterns = [
    path("", views.MaintenancePlanListView.as_view(), name="list"),
    path("new/", views.MaintenancePlanCreateView.as_view(), name="create"),
    path("<int:pk>/", views.MaintenancePlanDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.MaintenancePlanUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.MaintenancePlanDeleteView.as_view(), name="delete"),
    path("<int:pk>/record/new/", views.MaintenanceRecordCreateView.as_view(), name="record_create"),
]

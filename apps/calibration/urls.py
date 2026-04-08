from django.urls import path

from . import views

app_name = "calibration"

urlpatterns = [
    path("", views.TestEquipmentListView.as_view(), name="list"),
    path("new/", views.TestEquipmentCreateView.as_view(), name="create"),
    path("<int:pk>/", views.TestEquipmentDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.TestEquipmentUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.TestEquipmentDeleteView.as_view(), name="delete"),
    path("<int:pk>/record/", views.CalibrationRecordCreateView.as_view(), name="record_create"),
]

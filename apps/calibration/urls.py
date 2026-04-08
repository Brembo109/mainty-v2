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
    path("<int:pk>/return/", views.CalibrationReturnFromLabView.as_view(), name="record_return"),
    path("<int:pk>/record/<int:record_pk>/edit/", views.CalibrationRecordUpdateView.as_view(), name="record_update"),
    path("<int:pk>/record/<int:record_pk>/delete/", views.CalibrationRecordDeleteView.as_view(), name="record_delete"),
]

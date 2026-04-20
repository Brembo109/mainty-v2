from django.urls import path

from . import views

app_name = "assets"

urlpatterns = [
    path("", views.AssetListView.as_view(), name="list"),
    path("new/", views.AssetCreateView.as_view(), name="create"),
    path("<int:pk>/", views.asset_detail, name="detail"),
    path("<int:pk>/overview/", views.asset_overview, name="detail_overview"),
    path("<int:pk>/maintenance/", views.asset_maintenance, name="detail_maintenance"),
    path("<int:pk>/qualification/", views.asset_qualification, name="detail_qualification"),
    path("<int:pk>/documents/", views.asset_documents, name="detail_documents"),
    path("<int:pk>/audit/", views.asset_audit, name="detail_audit"),
    path("<int:pk>/edit/", views.AssetUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.AssetDeleteView.as_view(), name="delete"),
]

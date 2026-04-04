from django.urls import path

from . import views

app_name = "contracts"

urlpatterns = [
    path("", views.ContractListView.as_view(), name="list"),
    path("new/", views.ContractCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ContractDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.ContractUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.ContractDeleteView.as_view(), name="delete"),
]

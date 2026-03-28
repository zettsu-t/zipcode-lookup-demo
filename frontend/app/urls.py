from django.urls import path
from . import views

urlpatterns = [
    path("sender/", views.SenderView.as_view(), name="sender"),
    path("guests/", views.GuestListView.as_view(), name="guest_list"),
    path("guests/new/", views.GuestCreateView.as_view(), name="guest_create"),
    path("guests/<int:pk>/edit/", views.GuestUpdateView.as_view(), name="guest_update"),
    path("guests/<int:pk>/delete/", views.GuestDeleteView.as_view(), name="guest_delete"),
    path("zip/lookup/", views.ZipLookupView.as_view(), name="zip_lookup"),
]

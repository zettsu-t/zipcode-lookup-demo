from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/sender/"), name="home"),
    path("", include("app.urls")),
]

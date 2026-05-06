from django.urls import path

from .views import InscriptionLandingView

app_name = "inscription"

urlpatterns = [
    path("", InscriptionLandingView.as_view(), name="landing"),
]

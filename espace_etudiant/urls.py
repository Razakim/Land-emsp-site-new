from django.urls import path

from .views import DashboardView

app_name = "espace_etudiant"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
]

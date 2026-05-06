from django.urls import path

from .views import ConcoursView, FaqView, FormationsView, HomeView, InstitutionView, JournalView, MediathequeView

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("institution/", InstitutionView.as_view(), name="institution"),
    path("formations/", FormationsView.as_view(), name="formations"),
    path("faq/", FaqView.as_view(), name="faq"),
    path("journal/", JournalView.as_view(), name="journal"),
    path("concours/", ConcoursView.as_view(), name="concours"),
    path("mediatheque/", MediathequeView.as_view(), name="mediatheque"),
]

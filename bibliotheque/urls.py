from django.urls import path

from .views import (
    BibliothequeView,
    DepotDocumentView,
    DocumentDetailView,
    DownloadDocumentView,
    MesDocumentsView,
    commentaire_create_view,
    toggle_favori_view,
)

app_name = "bibliotheque"

urlpatterns = [
    path("", BibliothequeView.as_view(), name="liste"),
    path("depot/", DepotDocumentView.as_view(), name="depot"),
    path("mes-documents/", MesDocumentsView.as_view(), name="mes_documents"),
    path("document/<int:pk>/", DocumentDetailView.as_view(), name="detail"),
    path("document/<int:pk>/download/", DownloadDocumentView.as_view(), name="download"),
    path("document/<int:pk>/favori/", toggle_favori_view, name="toggle_favori"),
    path("document/<int:pk>/commentaire/", commentaire_create_view, name="commentaire_create"),
]

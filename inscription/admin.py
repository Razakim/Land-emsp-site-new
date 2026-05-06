from django.contrib import admin

from .models import Dossier, Inscription


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ("nom_complet", "email", "filiere", "licence", "statut", "date_soumission")
    list_filter = ("statut", "filiere", "licence", "date_soumission")
    search_fields = ("prenom", "nom", "email", "telephone")


@admin.register(Dossier)
class DossierAdmin(admin.ModelAdmin):
    list_display = ("inscription", "documents_fournis", "documents_requis", "updated_at")
    search_fields = ("inscription__prenom", "inscription__nom", "inscription__email")

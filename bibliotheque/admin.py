from django.contrib import admin

from .models import (
    AnneeAcademique,
    Commentaire,
    Document,
    Favori,
    Filiere,
    Licence,
    Matiere,
    RechercheRecente,
    Semestre,
    Telechargement,
    TypeDocument,
)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("titre", "type_document", "filiere", "licence", "semestre", "valide", "telechargements_count", "created_at")
    list_filter = ("valide", "type_document", "filiere", "licence", "semestre", "annee_academique")
    search_fields = ("titre", "description", "matiere__nom", "contributeur__username")


admin.site.register(Filiere)
admin.site.register(Licence)
admin.site.register(Semestre)
admin.site.register(TypeDocument)
admin.site.register(Matiere)
admin.site.register(AnneeAcademique)
admin.site.register(Telechargement)
admin.site.register(Favori)
admin.site.register(Commentaire)
admin.site.register(RechercheRecente)

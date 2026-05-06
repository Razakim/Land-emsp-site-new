from django.contrib import admin

from .models import (
    Bulletin,
    CarTransport,
    CreneauAbsence,
    EtudiantProfile,
    Evenement,
    InscriptionTransport,
    Justification,
    NoteBulletin,
    Paiement,
    Presence,
    Professeur,
    Seance,
    Scolarite,
)


@admin.register(Professeur)
class ProfesseurAdmin(admin.ModelAdmin):
    list_display = ("nom_complet", "email", "actif", "updated_at")
    list_filter = ("actif",)
    search_fields = ("nom_complet", "email")
    filter_horizontal = ("matieres",)


@admin.register(CreneauAbsence)
class CreneauAbsenceAdmin(admin.ModelAdmin):
    list_display = ("libelle", "heure_debut", "heure_fin", "ordre", "actif")
    list_filter = ("actif",)
    ordering = ("ordre", "heure_debut")


@admin.register(Seance)
class SeanceAdmin(admin.ModelAdmin):
    list_display = ("date", "heure_debut", "heure_fin", "filiere", "matiere", "professeur")
    list_filter = ("date", "filiere", "professeur")
    search_fields = ("matiere__nom", "filiere__nom", "professeur__nom_complet")


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ("titre", "type", "date", "heure", "public_cible", "statut", "annule")
    list_filter = ("type", "annule", "date")
    search_fields = ("titre", "lieu", "public_cible")


@admin.register(EtudiantProfile)
class EtudiantProfileAdmin(admin.ModelAdmin):
    list_display = ("matricule", "utilisateur", "filiere", "licence", "semestre", "actif")
    list_filter = ("actif", "filiere", "licence", "semestre")
    search_fields = ("matricule", "utilisateur__first_name", "utilisateur__last_name", "utilisateur__email")


class NoteBulletinInline(admin.TabularInline):
    model = NoteBulletin
    extra = 0


@admin.register(Bulletin)
class BulletinAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "annee_academique", "semestre", "moyenne", "decision", "publie")
    list_filter = ("annee_academique", "semestre", "decision", "publie")
    search_fields = ("etudiant__matricule", "etudiant__utilisateur__first_name", "etudiant__utilisateur__last_name")
    inlines = [NoteBulletinInline]


@admin.register(NoteBulletin)
class NoteBulletinAdmin(admin.ModelAdmin):
    list_display = ("bulletin", "matiere", "professeur", "coefficient", "note_cc", "note_examen", "note_finale")
    list_filter = ("matiere", "professeur")


@admin.register(Scolarite)
class ScolariteAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "total_du", "date_echeance", "updated_at")
    search_fields = ("etudiant__matricule", "etudiant__utilisateur__first_name", "etudiant__utilisateur__last_name")


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ("scolarite", "montant", "moyen", "date", "reference", "statut")
    list_filter = ("statut", "moyen", "date")
    search_fields = ("reference", "scolarite__etudiant__matricule")


@admin.register(CarTransport)
class CarTransportAdmin(admin.ModelAdmin):
    list_display = ("nom", "immatriculation", "axe_principal", "chauffeur", "capacite", "actif", "updated_at")
    list_filter = ("actif", "axe_principal")
    search_fields = ("nom", "immatriculation", "chauffeur", "telephone_chauffeur")


@admin.register(InscriptionTransport)
class InscriptionTransportAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "axe", "car", "statut", "date_inscription")
    list_filter = ("axe", "statut", "date_inscription")
    search_fields = ("etudiant__matricule", "etudiant__utilisateur__first_name", "etudiant__utilisateur__last_name")


@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "matiere", "date", "creneau", "seance", "present", "updated_at")
    list_filter = ("present", "date", "matiere", "creneau", "seance")
    search_fields = ("etudiant__matricule", "etudiant__utilisateur__first_name", "etudiant__utilisateur__last_name")


@admin.register(Justification)
class JustificationAdmin(admin.ModelAdmin):
    list_display = ("presence", "statut", "created_at", "updated_at")
    list_filter = ("statut", "created_at")
    search_fields = ("presence__etudiant__matricule", "presence__etudiant__utilisateur__first_name", "presence__etudiant__utilisateur__last_name", "motif")

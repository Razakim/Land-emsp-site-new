from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from administration.models import EtudiantProfile
from bibliotheque.models import Filiere, Licence


class Inscription(models.Model):
    STATUT_EN_ATTENTE = "en_attente"
    STATUT_EN_COURS = "en_cours"
    STATUT_VALIDEE = "validee"
    STATUT_REFUSEE = "refusee"
    STATUT_INCOMPLETE = "incomplete"
    STATUT_CHOICES = (
        (STATUT_EN_ATTENTE, "En attente"),
        (STATUT_EN_COURS, "En cours"),
        (STATUT_VALIDEE, "Validee"),
        (STATUT_REFUSEE, "Refusee"),
        (STATUT_INCOMPLETE, "Incomplete"),
    )

    prenom = models.CharField(max_length=150)
    nom = models.CharField(max_length=150)
    email = models.EmailField()
    telephone = models.CharField(max_length=30, blank=True)
    filiere = models.ForeignKey(Filiere, on_delete=models.PROTECT, related_name="inscriptions")
    licence = models.ForeignKey(Licence, on_delete=models.PROTECT, related_name="inscriptions")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default=STATUT_EN_ATTENTE)
    date_soumission = models.DateTimeField(default=timezone.now)
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inscriptions_candidat",
    )
    etudiant_profile = models.OneToOneField(
        EtudiantProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inscription_source",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-date_soumission", "-created_at")

    def __str__(self):
        return f"{self.nom_complet} - {self.get_statut_display()}"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}".strip()

    def creer_compte_etudiant(self):
        user_model = get_user_model()
        email = self.email.strip().lower()
        user = self.utilisateur or user_model.objects.filter(email__iexact=email).first()

        if not user:
            base_username = email.split("@")[0] or f"{self.prenom}.{self.nom}".lower()
            username = base_username
            idx = 2
            while user_model.objects.filter(username=username).exists():
                username = f"{base_username}{idx}"
                idx += 1
            user = user_model(username=username, email=email)
            user.set_unusable_password()

        user.first_name = self.prenom.strip()
        user.last_name = self.nom.strip()
        user.email = email
        user.save()

        profile = self.etudiant_profile or getattr(user, "profil_etudiant", None)
        if not profile:
            profile = EtudiantProfile.objects.create(
                utilisateur=user,
                telephone=self.telephone,
                filiere=self.filiere,
                licence=self.licence,
                actif=True,
            )
        else:
            profile.telephone = self.telephone
            profile.filiere = self.filiere
            profile.licence = self.licence
            profile.actif = True
            profile.save()

        self.utilisateur = user
        self.etudiant_profile = profile
        self.statut = self.STATUT_VALIDEE
        self.save(update_fields=["utilisateur", "etudiant_profile", "statut", "updated_at"])
        return profile


class Dossier(models.Model):
    inscription = models.OneToOneField(Inscription, on_delete=models.CASCADE, related_name="dossier")
    documents_requis = models.PositiveSmallIntegerField(default=6)
    documents_fournis = models.PositiveSmallIntegerField(default=0)
    commentaire_interne = models.TextField(blank=True)
    motif_refus = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-inscription__date_soumission",)

    def __str__(self):
        return f"Dossier {self.inscription.nom_complet}"

    @property
    def documents_manquants(self):
        return max(self.documents_requis - self.documents_fournis, 0)

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Filiere(models.Model):
    CYCLE_LICENCE_PRO = "licence_pro"
    CYCLE_MASTER_PRO = "master_pro"
    CYCLE_CHOICES = (
        (CYCLE_LICENCE_PRO, "Licences professionnelles"),
        (CYCLE_MASTER_PRO, "Masters professionnels"),
    )

    nom = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    cycle = models.CharField(max_length=20, choices=CYCLE_CHOICES, default=CYCLE_LICENCE_PRO)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("nom",)
        verbose_name = "Filiere"
        verbose_name_plural = "Filieres"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom


class Licence(models.Model):
    code = models.CharField(max_length=20, unique=True)
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("ordre", "code")

    def __str__(self):
        mapping = {
            'L1': 'Licence 1',
            'L2': 'Licence 2',
            'L3': 'Licence 3',
            'M1': 'Master 1',
            'M2': 'Master 2',
        }
        return mapping.get(self.code, self.code)


class Semestre(models.Model):
    code = models.CharField(max_length=5, unique=True)
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("ordre", "code")

    def __str__(self):
        return f"Semestre {self.code}"


class TypeDocument(models.Model):
    code = models.CharField(max_length=20, unique=True)
    libelle = models.CharField(max_length=80)
    couleur = models.CharField(max_length=20, default="primary")

    class Meta:
        ordering = ("libelle",)

    def __str__(self):
        return self.libelle


class Matiere(models.Model):
    nom = models.CharField(max_length=120)
    code = models.CharField(max_length=30, blank=True)
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name="matieres")
    semestre = models.ForeignKey(Semestre, on_delete=models.SET_NULL, null=True, blank=True, related_name="matieres")
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("nom",)
        unique_together = ("nom", "filiere")

    def __str__(self):
        return f"{self.nom} ({self.filiere.nom})"


class AnneeAcademique(models.Model):
    libelle = models.CharField(max_length=20, unique=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("-libelle",)
        verbose_name = "Annee academique"
        verbose_name_plural = "Annees academiques"

    def __str__(self):
        return self.libelle


class Document(models.Model):
    titre = models.CharField(max_length=220)
    description = models.TextField(max_length=1000)
    fichier = models.FileField(upload_to="bibliotheque/documents/%Y/%m/")
    filiere = models.ForeignKey(Filiere, on_delete=models.PROTECT, related_name="documents")
    licence = models.ForeignKey(Licence, on_delete=models.PROTECT, related_name="documents")
    semestre = models.ForeignKey(Semestre, on_delete=models.PROTECT, related_name="documents")
    matiere = models.ForeignKey(Matiere, on_delete=models.PROTECT, related_name="documents")
    type_document = models.ForeignKey(TypeDocument, on_delete=models.PROTECT, related_name="documents")
    annee_academique = models.ForeignKey(AnneeAcademique, on_delete=models.PROTECT, related_name="documents")
    contributeur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents_deposes",
    )
    reserve_auth = models.BooleanField(default=True)
    valide = models.BooleanField(default=False)
    motif_refus = models.CharField(max_length=255, blank=True)
    telechargements_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.titre

    @property
    def extension(self):
        return self.fichier.name.rsplit(".", 1)[-1].upper() if "." in self.fichier.name else ""

    @property
    def taille_mo(self):
        try:
            return round(self.fichier.size / (1024 * 1024), 2)
        except Exception:
            return 0


class Telechargement(models.Model):
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="telechargements_bibliotheque",
    )
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="telechargements")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class Favori(models.Model):
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favoris_bibliotheque",
    )
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="favoris")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("utilisateur", "document")
        ordering = ("-created_at",)


class Commentaire(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="commentaires")
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="commentaires_bibliotheque",
    )
    contenu = models.TextField(max_length=1200)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="reponses")
    likes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class RechercheRecente(models.Model):
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recherches_bibliotheque",
    )
    requete = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

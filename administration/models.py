from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from decimal import Decimal

from bibliotheque.models import Matiere
from bibliotheque.models import AnneeAcademique, Filiere, Licence, Semestre

User = get_user_model()


def current_academic_entry_year():
    return timezone.now().year


def _student_sequence_letters(index):
    n = max(index - 1, 0)
    letters = ""
    for _ in range(3):
        n, r = divmod(n, 26)
        letters = chr(65 + r) + letters
    return letters


def _student_matricule_from_user(user, year, suffix_index=0):
    first = slugify((user.first_name or user.username or "etudiant").strip()).replace("-", ".") or "etudiant"
    last = slugify((user.last_name or "emsp").strip()).replace("-", ".") or "emsp"
    suffix = f".{suffix_index}" if suffix_index else ""
    return f"{first}.{last}{suffix}@fsmenum{year}.emsp.int".lower()


class Professeur(models.Model):
    nom_complet = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=30, blank=True)
    matieres = models.ManyToManyField(Matiere, related_name="professeurs", blank=True)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("nom_complet",)

    def __str__(self):
        return self.nom_complet


class CreneauAbsence(models.Model):
    libelle = models.CharField(max_length=120)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    ordre = models.PositiveSmallIntegerField(default=0)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ("ordre", "heure_debut")
        unique_together = ("heure_debut", "heure_fin")

    def __str__(self):
        return f"{self.libelle} ({self.heure_debut.strftime('%H:%M')} - {self.heure_fin.strftime('%H:%M')})"


class Seance(models.Model):
    filiere = models.ForeignKey(Filiere, on_delete=models.PROTECT, related_name="seances")
    matiere = models.ForeignKey(Matiere, on_delete=models.PROTECT, related_name="seances")
    professeur = models.ForeignKey(Professeur, on_delete=models.PROTECT, related_name="seances")
    salle = models.CharField(max_length=80, blank=True)
    date = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("date", "heure_debut", "matiere__nom")
        unique_together = ("filiere", "matiere", "professeur", "date", "heure_debut", "heure_fin")
        verbose_name = "Seance"
        verbose_name_plural = "Seances"

    def __str__(self):
        return f"{self.matiere.nom} - {self.filiere.nom} - {self.date} ({self.heure_debut:%H:%M}-{self.heure_fin:%H:%M})"


class Evenement(models.Model):
    TYPE_CONFERENCE = "conference"
    TYPE_EXAMEN = "examen"
    TYPE_CONCOURS = "concours"
    TYPE_ACTIVITE = "activite"
    TYPE_AUTRE = "autre"
    TYPE_CHOICES = (
        (TYPE_CONFERENCE, "Conference"),
        (TYPE_EXAMEN, "Examen"),
        (TYPE_CONCOURS, "Concours"),
        (TYPE_ACTIVITE, "Activite"),
        (TYPE_AUTRE, "Autre"),
    )

    titre = models.CharField(max_length=180)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_CONFERENCE)
    date = models.DateField()
    heure = models.TimeField()
    lieu = models.CharField(max_length=180)
    public_cible = models.CharField(max_length=180, default="Tous")
    description = models.TextField(max_length=2000, blank=True)
    annule = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("date", "heure", "titre")

    @property
    def statut(self):
        if self.annule:
            return "annule"
        event_dt = timezone.make_aware(timezone.datetime.combine(self.date, self.heure))
        return "passe" if event_dt < timezone.now() else "a_venir"

    @property
    def statut_label(self):
        return {"a_venir": "A venir", "passe": "Passe", "annule": "Annule"}.get(self.statut, self.statut)

    def __str__(self):
        return f"{self.titre} - {self.date}"


class EtudiantProfile(models.Model):
    utilisateur = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profil_etudiant")
    matricule = models.CharField(max_length=120, unique=True, blank=True)
    annee_entree = models.PositiveSmallIntegerField(default=current_academic_entry_year)
    telephone = models.CharField(max_length=30, blank=True)
    photo = models.ImageField(upload_to="etudiants/photos/", blank=True, null=True)
    filiere = models.ForeignKey(Filiere, on_delete=models.SET_NULL, null=True, blank=True, related_name="etudiants")
    licence = models.ForeignKey(Licence, on_delete=models.SET_NULL, null=True, blank=True, related_name="etudiants")
    semestre = models.ForeignKey(Semestre, on_delete=models.SET_NULL, null=True, blank=True, related_name="etudiants")
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("matricule",)

    def __str__(self):
        full_name = self.utilisateur.get_full_name().strip()
        return f"{self.matricule} - {full_name or self.utilisateur.username}"

    @property
    def nom_complet(self):
        full_name = self.utilisateur.get_full_name().strip()
        return full_name or self.utilisateur.username

    def save(self, *args, **kwargs):
        if not self.matricule:
            next_index = 0
            matricule = _student_matricule_from_user(self.utilisateur, self.annee_entree, next_index)
            while EtudiantProfile.objects.filter(matricule=matricule).exclude(pk=self.pk).exists():
                next_index += 1
                matricule = _student_matricule_from_user(self.utilisateur, self.annee_entree, next_index)
            self.matricule = matricule
        super().save(*args, **kwargs)

    @property
    def taux_assiduite(self):
        total = self.presences.count()
        if total == 0:
            return 100
        presents = self.presences.filter(present=True).count()
        return round((presents / total) * 100)


class Presence(models.Model):
    etudiant = models.ForeignKey(EtudiantProfile, on_delete=models.CASCADE, related_name="presences")
    matiere = models.ForeignKey(Matiere, on_delete=models.PROTECT, related_name="presences")
    date = models.DateField(default=timezone.localdate)
    creneau = models.ForeignKey(CreneauAbsence, on_delete=models.PROTECT, related_name="presences")
    seance = models.ForeignKey(Seance, on_delete=models.SET_NULL, null=True, blank=True, related_name="presences")
    present = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-date", "creneau__ordre", "etudiant__matricule")
        unique_together = ("etudiant", "matiere", "date", "creneau")

    def __str__(self):
        statut = "present" if self.present else "absent"
        return f"{self.etudiant.matricule} - {self.matiere.nom} - {self.date} - {statut}"


class Justification(models.Model):
    STATUT_EN_ATTENTE = "en_attente"
    STATUT_ACCEPTEE = "acceptee"
    STATUT_REFUSEE = "refusee"
    STATUT_CHOICES = (
        (STATUT_EN_ATTENTE, "En attente"),
        (STATUT_ACCEPTEE, "Acceptee"),
        (STATUT_REFUSEE, "Refusee"),
    )

    presence = models.ForeignKey(Presence, on_delete=models.CASCADE, related_name="justifications")
    motif = models.TextField(max_length=1000)
    piece_jointe = models.FileField(upload_to="presences/justifications/%Y/%m/", blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default=STATUT_EN_ATTENTE)
    commentaire = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Justification {self.presence.etudiant.matricule} - {self.get_statut_display()}"


class Bulletin(models.Model):
    DECISION_ADMIS = "admis"
    DECISION_RATTRAPAGE = "rattrapage"
    DECISION_AJOURNE = "ajourne"
    DECISION_CHOICES = (
        (DECISION_ADMIS, "Admis"),
        (DECISION_RATTRAPAGE, "Rattrapage"),
        (DECISION_AJOURNE, "Ajourne"),
    )

    etudiant = models.ForeignKey(EtudiantProfile, on_delete=models.CASCADE, related_name="bulletins")
    annee_academique = models.ForeignKey(AnneeAcademique, on_delete=models.PROTECT, related_name="bulletins")
    semestre = models.ForeignKey(Semestre, on_delete=models.PROTECT, related_name="bulletins")
    moyenne = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default=DECISION_AJOURNE)
    appreciation = models.CharField(max_length=255, blank=True)
    publie = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-annee_academique__libelle", "semestre__ordre")
        unique_together = ("etudiant", "annee_academique", "semestre")

    def __str__(self):
        return f"{self.etudiant.matricule} - {self.annee_academique.libelle} - {self.semestre.code}"

    @property
    def mention(self):
        if self.moyenne >= Decimal("16"):
            return "Tres bien"
        if self.moyenne >= Decimal("14"):
            return "Bien"
        if self.moyenne >= Decimal("12"):
            return "Assez bien"
        if self.moyenne >= Decimal("10"):
            return "Passable"
        return "Insuffisant"

    def recalculer_moyenne(self):
        notes_qs = self.notes.all()
        total_coeff = sum(note.coefficient for note in notes_qs)
        if total_coeff <= 0:
            moyenne = Decimal("0.00")
        else:
            total_points = sum((note.note_finale or Decimal("0.00")) * Decimal(note.coefficient) for note in notes_qs)
            moyenne = (total_points / Decimal(total_coeff)).quantize(Decimal("0.01"))

        if moyenne >= Decimal("10"):
            decision = self.DECISION_ADMIS
        elif moyenne >= Decimal("8"):
            decision = self.DECISION_RATTRAPAGE
        else:
            decision = self.DECISION_AJOURNE

        self.moyenne = moyenne
        self.decision = decision
        self.save(update_fields=["moyenne", "decision", "updated_at"])


class NoteBulletin(models.Model):
    bulletin = models.ForeignKey(Bulletin, on_delete=models.CASCADE, related_name="notes")
    matiere = models.ForeignKey(Matiere, on_delete=models.PROTECT, related_name="notes_bulletins")
    professeur = models.ForeignKey(Professeur, on_delete=models.SET_NULL, null=True, blank=True, related_name="notes_bulletins")
    coefficient = models.PositiveSmallIntegerField(default=1)
    note_cc = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("0.00"))
    note_examen = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("0.00"))
    note_finale = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("0.00"))
    observation = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("matiere__nom",)
        unique_together = ("bulletin", "matiere")

    def __str__(self):
        return f"{self.bulletin} - {self.matiere.nom}"

    def save(self, *args, **kwargs):
        cc = self.note_cc or Decimal("0.00")
        examen = self.note_examen or Decimal("0.00")
        self.note_finale = (cc * Decimal("0.40") + examen * Decimal("0.60")).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)
        self.bulletin.recalculer_moyenne()

    def delete(self, *args, **kwargs):
        bulletin = self.bulletin
        super().delete(*args, **kwargs)
        bulletin.recalculer_moyenne()


class Scolarite(models.Model):
    etudiant = models.OneToOneField(EtudiantProfile, on_delete=models.CASCADE, related_name="scolarite")
    total_du = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    date_echeance = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("etudiant__matricule",)

    @property
    def total_paye(self):
        return self.paiements.filter(statut=Paiement.STATUT_VERIFIE).aggregate(total=models.Sum("montant"))["total"] or Decimal("0.00")

    @property
    def reste_a_payer(self):
        return max(self.total_du - self.total_paye, Decimal("0.00"))

    @property
    def statut(self):
        if self.total_paye >= self.total_du and self.total_du > 0:
            return "complet"
        if self.total_paye > 0:
            return "partiel"
        return "impaye"

    @property
    def statut_label(self):
        return {"complet": "Complet", "partiel": "Partiel", "impaye": "Impaye"}.get(self.statut, self.statut)

    @property
    def dernier_paiement(self):
        return self.paiements.order_by("-date", "-created_at").first()

    def __str__(self):
        return f"{self.etudiant.matricule} - {self.total_du}"


class Paiement(models.Model):
    MOYEN_ESPECES = "especes"
    MOYEN_WAVE = "wave"
    MOYEN_ORANGE = "orange_money"
    MOYEN_VIREMENT = "virement"
    MOYEN_CARTE = "carte"
    MOYEN_CHOICES = (
        (MOYEN_ESPECES, "Especes"),
        (MOYEN_WAVE, "Wave"),
        (MOYEN_ORANGE, "Orange Money"),
        (MOYEN_VIREMENT, "Virement"),
        (MOYEN_CARTE, "Carte bancaire"),
    )

    STATUT_EN_ATTENTE = "en_attente"
    STATUT_VERIFIE = "verifie"
    STATUT_REJETE = "rejete"
    STATUT_CHOICES = (
        (STATUT_EN_ATTENTE, "En attente"),
        (STATUT_VERIFIE, "Verifie"),
        (STATUT_REJETE, "Rejete"),
    )

    scolarite = models.ForeignKey(Scolarite, on_delete=models.CASCADE, related_name="paiements")
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    moyen = models.CharField(max_length=20, choices=MOYEN_CHOICES, default=MOYEN_ESPECES)
    date = models.DateField(default=timezone.localdate)
    reference = models.CharField(max_length=80, unique=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default=STATUT_EN_ATTENTE)
    commentaire = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-date", "-created_at")

    def __str__(self):
        return f"{self.scolarite.etudiant.matricule} - {self.montant} - {self.reference}"


class CarTransport(models.Model):
    AXE_COCODY = "cocody"
    AXE_YOPOUGON = "yopougon"
    AXE_BINGERVILLE = "bingerville"
    AXE_ABOBO = "abobo"
    AXE_BASSAM = "bassam"
    AXE_CHOICES = (
        (AXE_COCODY, "Cocody"),
        (AXE_YOPOUGON, "Yopougon"),
        (AXE_BINGERVILLE, "Bingerville"),
        (AXE_ABOBO, "Abobo"),
        (AXE_BASSAM, "Bassam"),
    )

    nom = models.CharField(max_length=120)
    immatriculation = models.CharField(max_length=40, unique=True)
    axe_principal = models.CharField(max_length=20, choices=AXE_CHOICES, default=AXE_COCODY)
    chauffeur = models.CharField(max_length=120, blank=True)
    telephone_chauffeur = models.CharField(max_length=30, blank=True)
    capacite = models.PositiveSmallIntegerField(default=20)
    actif = models.BooleanField(default=True)
    observations = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("nom", "immatriculation")
        verbose_name = "Car de transport"
        verbose_name_plural = "Cars de transport"

    def __str__(self):
        return f"{self.nom} ({self.immatriculation})"


class InscriptionTransport(models.Model):
    STATUT_EN_ATTENTE = "en_attente"
    STATUT_VALIDEE = "validee"
    STATUT_SUSPENDUE = "suspendue"
    STATUT_CHOICES = (
        (STATUT_EN_ATTENTE, "En attente"),
        (STATUT_VALIDEE, "Validee"),
        (STATUT_SUSPENDUE, "Suspendue"),
    )

    etudiant = models.ForeignKey(EtudiantProfile, on_delete=models.CASCADE, related_name="inscriptions_transport")
    axe = models.CharField(max_length=20, choices=CarTransport.AXE_CHOICES)
    car = models.ForeignKey(CarTransport, on_delete=models.SET_NULL, null=True, blank=True, related_name="inscriptions")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default=STATUT_EN_ATTENTE)
    date_inscription = models.DateField(auto_now_add=True)
    commentaire = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        unique_together = ("etudiant", "axe")
        verbose_name = "Inscription transport"
        verbose_name_plural = "Inscriptions transport"

    def __str__(self):
        return f"{self.etudiant.matricule} - {self.get_axe_display()}"

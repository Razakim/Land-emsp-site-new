from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from bibliotheque.models import AnneeAcademique, Filiere, Licence, Matiere

from .models import Bulletin, CarTransport, CreneauAbsence, EtudiantProfile, Evenement, InscriptionTransport, NoteBulletin, Paiement, Professeur, Seance, Scolarite

User = get_user_model()


class FiliereForm(forms.ModelForm):
    class Meta:
        model = Filiere
        fields = ("nom", "cycle", "active")


class LicenceForm(forms.ModelForm):
    class Meta:
        model = Licence
        fields = ("code", "ordre")


class MatiereForm(forms.ModelForm):
    class Meta:
        model = Matiere
        fields = ("nom", "code", "filiere", "semestre", "active")


class AnneeAcademiqueForm(forms.ModelForm):
    class Meta:
        model = AnneeAcademique
        fields = ("libelle", "active")


class ProfesseurForm(forms.ModelForm):
    class Meta:
        model = Professeur
        fields = ("nom_complet", "email", "telephone", "matieres", "actif")
        widgets = {
            "matieres": forms.SelectMultiple(attrs={"size": 8}),
        }


class CreneauAbsenceForm(forms.ModelForm):
    class Meta:
        model = CreneauAbsence
        fields = ("libelle", "heure_debut", "heure_fin", "ordre", "actif")


class SeanceForm(forms.ModelForm):
    class Meta:
        model = Seance
        fields = ("filiere", "matiere", "professeur", "salle", "date", "heure_debut", "heure_fin")
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "heure_debut": forms.TimeInput(attrs={"type": "time"}),
            "heure_fin": forms.TimeInput(attrs={"type": "time"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        filiere = cleaned_data.get("filiere")
        matiere = cleaned_data.get("matiere")
        heure_debut = cleaned_data.get("heure_debut")
        heure_fin = cleaned_data.get("heure_fin")

        if filiere and matiere and matiere.filiere_id != filiere.id:
            self.add_error("matiere", "Cette matiere n'appartient pas a la filiere selectionnee.")

        if heure_debut and heure_fin and heure_fin <= heure_debut:
            self.add_error("heure_fin", "L'heure de fin doit etre posterieure a l'heure de debut.")

        return cleaned_data


class EvenementForm(forms.ModelForm):
    class Meta:
        model = Evenement
        fields = ("titre", "type", "date", "heure", "lieu", "public_cible", "description", "annule")
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "heure": forms.TimeInput(attrs={"type": "time"}),
        }


class EtudiantProfileForm(forms.ModelForm):
    prenom = forms.CharField(max_length=150)
    nom = forms.CharField(max_length=150)
    email = forms.EmailField()
    matricule = forms.CharField(max_length=120, required=False)

    class Meta:
        model = EtudiantProfile
        fields = ("matricule", "telephone", "photo", "filiere", "licence", "semestre", "actif")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["prenom"].initial = self.instance.utilisateur.first_name
            self.fields["nom"].initial = self.instance.utilisateur.last_name
            self.fields["email"].initial = self.instance.utilisateur.email

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.utilisateur_id)
        if qs.exists():
            raise forms.ValidationError("Cet email est deja utilise.")
        return email

    def clean_matricule(self):
        matricule = (self.cleaned_data.get("matricule") or "").strip().lower()
        if not matricule:
            return ""
        qs = EtudiantProfile.objects.filter(matricule__iexact=matricule)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ce matricule est deja utilise.")
        return matricule

    def save(self, commit=True):
        profile = super().save(commit=False)
        is_create = not bool(profile.pk)

        if is_create:
            base_username = self.cleaned_data["email"].split("@")[0].strip() or self.cleaned_data["matricule"].lower()
            username = base_username
            idx = 2
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{idx}"
                idx += 1
            user = User(username=username)
            user.set_unusable_password()
            profile.utilisateur = user
        else:
            user = profile.utilisateur

        user.first_name = self.cleaned_data["prenom"].strip()
        user.last_name = self.cleaned_data["nom"].strip()
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()
            profile.save()
            self.save_m2m()

        return profile


class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "username")

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("L'adresse email est obligatoire.")
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Cet email est deja utilise.")
        return email


class BulletinForm(forms.ModelForm):
    class Meta:
        model = Bulletin
        fields = ("annee_academique", "semestre", "appreciation", "publie")


class NoteBulletinForm(forms.ModelForm):
    class Meta:
        model = NoteBulletin
        fields = ("matiere", "professeur", "coefficient", "note_cc", "note_examen", "observation")


class PaiementForm(forms.ModelForm):
    etudiant = forms.ModelChoiceField(queryset=EtudiantProfile.objects.none())

    class Meta:
        model = Paiement
        fields = ("etudiant", "montant", "moyen", "date", "reference")
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["etudiant"].queryset = EtudiantProfile.objects.select_related("utilisateur").order_by("matricule")

    def save(self, commit=True):
        etudiant = self.cleaned_data["etudiant"]
        scolarite, _ = Scolarite.objects.get_or_create(etudiant=etudiant)
        paiement = super().save(commit=False)
        paiement.scolarite = scolarite
        if commit:
            paiement.save()
        return paiement


class CarTransportForm(forms.ModelForm):
    class Meta:
        model = CarTransport
        fields = (
            "nom",
            "immatriculation",
            "axe_principal",
            "chauffeur",
            "telephone_chauffeur",
            "capacite",
            "actif",
            "observations",
        )


class InscriptionTransportForm(forms.ModelForm):
    class Meta:
        model = InscriptionTransport
        fields = ("etudiant", "axe", "car", "statut", "commentaire")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["etudiant"].queryset = EtudiantProfile.objects.select_related("utilisateur").order_by("matricule")
        self.fields["car"].queryset = CarTransport.objects.filter(actif=True).order_by("axe_principal", "nom")


class UserRoleForm(forms.ModelForm):
    ROLE_ADMINISTRATION = "Administration"
    ROLE_SECRETARIAT = "Secretariat"
    ROLE_PROFESSEUR = "Professeur"
    ROLE_UTILISATEUR = "Utilisateur"
    ROLE_CHOICES = (
        (ROLE_ADMINISTRATION, "Administration"),
        (ROLE_SECRETARIAT, "Secretariat"),
        (ROLE_PROFESSEUR, "Professeur"),
        (ROLE_UTILISATEUR, "Utilisateur"),
    )

    password = forms.CharField(widget=forms.PasswordInput, required=False)
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password", "role", "is_active")

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        role = self.cleaned_data["role"]
        if password:
            user.set_password(password)
        elif not user.pk:
            user.set_unusable_password()
        user.is_staff = role in {self.ROLE_ADMINISTRATION, self.ROLE_SECRETARIAT}
        if commit:
            user.save()
            Group.objects.get_or_create(name=role)[0].user_set.add(user)
            for group in Group.objects.exclude(name=role).filter(
                name__in=[choice[0] for choice in self.ROLE_CHOICES]
            ):
                group.user_set.remove(user)
        return user

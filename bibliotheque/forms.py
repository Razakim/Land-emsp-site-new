from django import forms

from .models import Commentaire, Document, Matiere


class DepotDocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            "titre",
            "description",
            "type_document",
            "filiere",
            "licence",
            "semestre",
            "matiere",
            "annee_academique",
            "fichier",
            "reserve_auth",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4, "maxlength": 300}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

        self.fields["reserve_auth"].widget = forms.CheckboxInput(attrs={"class": "form-check-input"})
        self.fields["reserve_auth"].help_text = "Cocher pour reserver le telechargement aux utilisateurs connectes."

        if "filiere" in self.data:
            try:
                filiere_id = int(self.data.get("filiere"))
                self.fields["matiere"].queryset = Matiere.objects.filter(filiere_id=filiere_id, active=True).order_by("nom")
            except (TypeError, ValueError):
                self.fields["matiere"].queryset = Matiere.objects.none()
        else:
            self.fields["matiere"].queryset = Matiere.objects.filter(active=True).order_by("nom")

    def clean_description(self):
        value = (self.cleaned_data.get("description") or "").strip()
        if len(value) > 300:
            raise forms.ValidationError("La description ne doit pas depasser 300 caracteres.")
        return value

    def clean_fichier(self):
        uploaded = self.cleaned_data.get("fichier")
        if not uploaded:
            return uploaded

        allowed_extensions = {".pdf", ".docx", ".pptx", ".xlsx"}
        filename = uploaded.name.lower()
        extension = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""
        if extension not in allowed_extensions:
            raise forms.ValidationError("Format non supporte. Utilisez PDF, DOCX, PPTX ou XLSX.")

        max_size = 10 * 1024 * 1024
        if uploaded.size > max_size:
            raise forms.ValidationError("Le fichier depasse 10 Mo.")

        return uploaded

    def clean(self):
        cleaned = super().clean()
        filiere = cleaned.get("filiere")
        matiere = cleaned.get("matiere")
        if filiere and matiere and matiere.filiere_id != filiere.id:
            self.add_error("matiere", "La matiere selectionnee ne correspond pas a la filiere.")
        return cleaned


class CommentaireForm(forms.ModelForm):
    class Meta:
        model = Commentaire
        fields = ["contenu"]
        widgets = {
            "contenu": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control",
                    "placeholder": "Ajouter votre commentaire...",
                }
            )
        }

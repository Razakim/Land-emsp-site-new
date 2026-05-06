from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, TemplateView

from .forms import CommentaireForm, DepotDocumentForm
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


class BibliothequeView(TemplateView):
    template_name = "bibliotheque/liste.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documents = (
            Document.objects.filter(valide=True)
            .select_related(
                "filiere",
                "licence",
                "semestre",
                "matiere",
                "type_document",
                "annee_academique",
                "contributeur",
            )
            .order_by("-created_at")
        )

        q = (self.request.GET.get("q") or "").strip()
        filiere = self.request.GET.get("filiere") or ""
        licence = self.request.GET.get("licence") or ""
        semestre = self.request.GET.get("semestre") or ""
        matiere = self.request.GET.get("matiere") or ""
        annee = self.request.GET.get("annee") or ""
        sort = self.request.GET.get("sort") or "recent"
        type_ids = [value for value in self.request.GET.getlist("type") if value]

        if q:
            documents = documents.filter(
                Q(titre__icontains=q)
                | Q(description__icontains=q)
                | Q(matiere__nom__icontains=q)
                | Q(contributeur__username__icontains=q)
                | Q(contributeur__first_name__icontains=q)
                | Q(contributeur__last_name__icontains=q)
            )
            if self.request.user.is_authenticated:
                RechercheRecente.objects.create(utilisateur=self.request.user, requete=q[:120])

        if filiere:
            documents = documents.filter(filiere_id=filiere)
        if licence:
            documents = documents.filter(licence_id=licence)
        if semestre:
            documents = documents.filter(semestre_id=semestre)
        if matiere:
            documents = documents.filter(matiere_id=matiere)
        if annee:
            documents = documents.filter(annee_academique_id=annee)
        if type_ids:
            documents = documents.filter(type_document_id__in=type_ids)

        if sort == "downloads":
            documents = documents.order_by("-telechargements_count", "-created_at")
        elif sort == "rated":
            documents = documents.annotate(nb_commentaires=Count("commentaires")).order_by("-nb_commentaires", "-created_at")
        else:
            documents = documents.order_by("-created_at")

        paginator = Paginator(documents, 15)
        page_obj = paginator.get_page(self.request.GET.get("page"))

        matieres_qs = Matiere.objects.filter(active=True).order_by("nom")
        if filiere:
            matieres_qs = matieres_qs.filter(filiere_id=filiere)

        recent_searches = []
        if self.request.user.is_authenticated:
            seen = set()
            for item in RechercheRecente.objects.filter(utilisateur=self.request.user)[:12]:
                if item.requete in seen:
                    continue
                recent_searches.append(item.requete)
                seen.add(item.requete)
                if len(recent_searches) >= 6:
                    break

        context.update(
            {
                "page_obj": page_obj,
                "documents": page_obj.object_list,
                "total_documents": Document.objects.filter(valide=True).count(),
                "total_filieres": Filiere.objects.filter(active=True).count(),
                "total_contributeurs": Document.objects.filter(valide=True).values("contributeur_id").distinct().count(),
                "filieres": Filiere.objects.filter(active=True).order_by("nom"),
                "licences": Licence.objects.all(),
                "semestres": Semestre.objects.all(),
                "types_documents": TypeDocument.objects.all(),
                "matieres": matieres_qs,
                "annees": AnneeAcademique.objects.filter(active=True).order_by("-libelle"),
                "recent_searches": recent_searches,
                "query": q,
                "selected_filiere": filiere,
                "selected_licence": licence,
                "selected_semestre": semestre,
                "selected_matiere": matiere,
                "selected_annee": annee,
                "selected_sort": sort,
                "selected_types": type_ids,
            }
        )
        return context


class DocumentDetailView(DetailView):
    model = Document
    template_name = "bibliotheque/detail.html"
    context_object_name = "document"

    def get_queryset(self):
        return Document.objects.select_related(
            "filiere",
            "licence",
            "semestre",
            "matiere",
            "type_document",
            "annee_academique",
            "contributeur",
        )

    def get_object(self, queryset=None):
        doc = super().get_object(queryset)
        if doc.valide:
            return doc
        user = self.request.user
        if user.is_authenticated and (user == doc.contributeur or user.is_staff):
            return doc
        raise Http404("Document indisponible.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doc = context["document"]
        similar_docs = (
            Document.objects.filter(valide=True, matiere=doc.matiere)
            .exclude(pk=doc.pk)
            .select_related("type_document", "semestre")
            .order_by("-created_at")[:4]
        )
        same_author = (
            Document.objects.filter(valide=True, contributeur=doc.contributeur)
            .exclude(pk=doc.pk)
            .order_by("-created_at")[:3]
        )
        commentaires = (
            Commentaire.objects.filter(document=doc, parent__isnull=True)
            .select_related("utilisateur")
            .prefetch_related("reponses__utilisateur")
            .order_by("-created_at")
        )
        is_favori = False
        if self.request.user.is_authenticated:
            is_favori = Favori.objects.filter(utilisateur=self.request.user, document=doc).exists()

        context.update(
            {
                "similar_docs": similar_docs,
                "same_author_docs": same_author,
                "commentaires": commentaires,
                "comment_form": CommentaireForm(),
                "is_favori": is_favori,
                "can_download": self.request.user.is_authenticated or not doc.reserve_auth,
                "is_pdf": doc.fichier.name.lower().endswith(".pdf"),
            }
        )
        return context


@method_decorator(login_required, name="dispatch")
class DepotDocumentView(TemplateView):
    template_name = "bibliotheque/depot.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"form": DepotDocumentForm()})

    def post(self, request, *args, **kwargs):
        form = DepotDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.contributeur = request.user
            document.valide = False
            document.save()
            messages.success(request, "Ton document a ete soumis pour validation.")
            return redirect("bibliotheque:mes_documents")
        return render(request, self.template_name, {"form": form})


@method_decorator(login_required, name="dispatch")
class MesDocumentsView(TemplateView):
    template_name = "bibliotheque/mes_documents.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tab = self.request.GET.get("tab") or "depots"

        depots = Document.objects.filter(contributeur=user).select_related(
            "type_document",
            "semestre",
            "filiere",
        )
        telecharges = Telechargement.objects.filter(utilisateur=user).select_related("document", "document__type_document")
        favoris = Favori.objects.filter(utilisateur=user).select_related("document", "document__type_document")

        context.update(
            {
                "active_tab": tab,
                "depots": depots,
                "telecharges": telecharges,
                "favoris": favoris,
            }
        )
        return context


@method_decorator(login_required, name="dispatch")
class DownloadDocumentView(View):
    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk, valide=True)
        if document.reserve_auth and not request.user.is_authenticated:
            return redirect(f"{reverse('accounts:login')}?next={request.path}")

        if not document.fichier:
            raise Http404("Fichier introuvable.")

        Document.objects.filter(pk=document.pk).update(telechargements_count=F("telechargements_count") + 1)
        Telechargement.objects.create(utilisateur=request.user, document=document)

        filename = document.fichier.name.rsplit("/", 1)[-1]
        return FileResponse(document.fichier.open("rb"), as_attachment=True, filename=filename)


@login_required
def toggle_favori_view(request, pk):
    document = get_object_or_404(Document, pk=pk, valide=True)
    favorite = Favori.objects.filter(utilisateur=request.user, document=document)
    if favorite.exists():
        favorite.delete()
        messages.info(request, "Document retire de vos favoris.")
    else:
        Favori.objects.create(utilisateur=request.user, document=document)
        messages.success(request, "Document ajoute aux favoris.")
    return redirect("bibliotheque:detail", pk=document.pk)


@login_required
def commentaire_create_view(request, pk):
    document = get_object_or_404(Document, pk=pk, valide=True)
    if request.method != "POST":
        return redirect("bibliotheque:detail", pk=pk)

    form = CommentaireForm(request.POST)
    if form.is_valid():
        commentaire = form.save(commit=False)
        commentaire.document = document
        commentaire.utilisateur = request.user
        commentaire.save()
        messages.success(request, "Commentaire publie.")
    else:
        messages.error(request, "Impossible d'ajouter le commentaire.")
    return redirect("bibliotheque:detail", pk=pk)

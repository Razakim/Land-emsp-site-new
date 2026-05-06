import csv
import io
from datetime import time, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.deletion import ProtectedError
from django.db.models.functions import TruncMonth
from django.db.utils import OperationalError, ProgrammingError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from bibliotheque.models import AnneeAcademique, Document, Filiere, Licence, Matiere, Semestre
from inscription.models import Dossier, Inscription

from .forms import (
    AnneeAcademiqueForm,
    AdminProfileForm,
    BulletinForm,
    CarTransportForm,
    CreneauAbsenceForm,
    EtudiantProfileForm,
    EvenementForm,
    FiliereForm,
    InscriptionTransportForm,
    LicenceForm,
    MatiereForm,
    NoteBulletinForm,
    PaiementForm,
    ProfesseurForm,
    SeanceForm,
    UserRoleForm,
)
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
from .services.pdf_bulletin import render_bulletin_pdf_bytes

User = get_user_model()
ADMIN_PAGE_SIZE = 20


def _safe_queryset(model, order_fields=()):
    try:
        qs = model.objects.all()
        return qs.order_by(*order_fields) if order_fields else qs
    except (OperationalError, ProgrammingError):
        return model.objects.none()


def _paginate(request, items, page_size=ADMIN_PAGE_SIZE):
    paginator = Paginator(items, page_size)
    page_obj = paginator.get_page(request.GET.get("page"))
    query = request.GET.copy()
    query.pop("page", None)
    return page_obj, query.urlencode()


def _seed_reference_if_needed():
    try:
        if not Filiere.objects.exists():
            filieres = [
                "LOGISTIQUE ET NUMERIQUE",
                "FINANCE DIGITALE",
                "MARKETING",
                "DIGITALISATION DES SERVICES",
                "GESTION DES ACTIVITES REGLEMENTAIRES",
            ]
            for nom in filieres:
                Filiere.objects.get_or_create(nom=nom, defaults={"cycle": Filiere.CYCLE_LICENCE_PRO, "active": True})

        if not AnneeAcademique.objects.exists():
            for libelle in ("2023-2024", "2024-2025", "2025-2026", "2026-2027"):
                AnneeAcademique.objects.get_or_create(libelle=libelle, defaults={"active": libelle == "2026-2027"})

        if not Semestre.objects.exists():
            for idx, code in enumerate(("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"), start=1):
                Semestre.objects.get_or_create(code=code, defaults={"ordre": idx})

        if not Licence.objects.exists():
            defaults = (("L1", 1), ("L2", 2), ("L3", 3), ("M1", 4), ("M2", 5))
            for code, ordre in defaults:
                Licence.objects.get_or_create(code=code, defaults={"ordre": ordre})
    except (OperationalError, ProgrammingError):
        return


def _to_bool(value):
    return str(value).lower() in {"1", "true", "on", "yes"}


def _compute_rank_for_bulletin(bulletin):
    cohort = list(
        Bulletin.objects.filter(
            annee_academique=bulletin.annee_academique,
            semestre=bulletin.semestre,
            etudiant__filiere=bulletin.etudiant.filiere,
            etudiant__licence=bulletin.etudiant.licence,
        )
        .select_related("etudiant")
        .order_by("-moyenne", "etudiant__matricule")
    )
    if not cohort:
        return None, 0

    rank = 0
    last_moyenne = None
    for idx, item in enumerate(cohort, start=1):
        if last_moyenne is None or item.moyenne != last_moyenne:
            rank = idx
            last_moyenne = item.moyenne
        if item.id == bulletin.id:
            return rank, len(cohort)

    return None, len(cohort)


def _seances_from_filters(request):
    filiere_id = (request.GET.get("filiere") or "").strip()
    professeur_id = (request.GET.get("professeur") or "").strip()
    week_start = _week_start_from_request(request)
    week_end = week_start + timedelta(days=6)

    seances = Seance.objects.select_related("filiere", "matiere", "professeur").order_by("date", "heure_debut")
    seances = seances.filter(date__gte=week_start, date__lte=week_end)
    if filiere_id:
        seances = seances.filter(filiere_id=filiere_id)
    if professeur_id:
        seances = seances.filter(professeur_id=professeur_id)

    return seances, {"filiere": filiere_id, "professeur": professeur_id, "semaine": week_start.isoformat()}


def _format_seance_rows(seances):
    return [
        [
            seance.date.strftime("%d/%m/%Y"),
            seance.heure_debut.strftime("%H:%M"),
            seance.heure_fin.strftime("%H:%M"),
            seance.filiere.nom,
            seance.matiere.nom,
            seance.professeur.nom_complet,
        ]
        for seance in seances
    ]


def _week_start_from_request(request):
    raw = (request.GET.get("semaine") or "").strip()
    if raw:
        try:
            selected = timezone.datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            selected = timezone.localdate()
    else:
        selected = timezone.localdate()
    return selected - timedelta(days=selected.weekday())


def _emploi_du_temps_grid(seances, week_start):
    days = [week_start + timedelta(days=offset) for offset in range(6)]
    day_labels = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
    month_labels = [
        "Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Decembre",
    ]
    slots = [
        {"label": "08 h 00 - 10 h 00", "start": time(8, 0), "end": time(10, 0), "kind": "course"},
        {"label": "Pause 10 h 00 - 10 h 15", "start": None, "end": None, "kind": "pause"},
        {"label": "10 h 15 - 12 h 15", "start": time(10, 15), "end": time(12, 15), "kind": "course"},
        {"label": "Pause-Dejeuner", "start": None, "end": None, "kind": "pause"},
        {"label": "13 h 15 - 15 h 15", "start": time(13, 15), "end": time(15, 15), "kind": "course"},
        {"label": "Pause 15 h 15 - 15 h 30", "start": None, "end": None, "kind": "pause"},
        {"label": "15 h 30 - 16 h 30", "start": time(15, 30), "end": time(16, 30), "kind": "course"},
    ]
    grid = []
    seances_list = list(seances)
    for slot in slots:
        cells = []
        if slot["kind"] == "course":
            for day in days:
                cell_items = []
                for seance in seances_list:
                    if seance.date != day:
                        continue
                    if seance.heure_debut < slot["end"] and seance.heure_fin > slot["start"]:
                        cell_items.append(seance)
                cells.append(cell_items)
        else:
            cells = [[] for _ in days]
        grid.append({"slot": slot["label"], "kind": slot["kind"], "cells": cells})
    academic_week_start = timezone.datetime(2026, 4, 6).date()
    academic_week_number = max(((week_start - academic_week_start).days // 7) + 1, 1)
    return {
        "week_start": week_start,
        "week_end": days[-1],
        "week_start_label": day_labels[0],
        "week_end_label": day_labels[-1],
        "week_number": academic_week_number,
        "days": [
            {"date": day, "label": day_labels[index], "month_label": month_labels[day.month - 1]}
            for index, day in enumerate(days)
        ],
        "slots": slots,
        "rows": grid,
    }


def _money(value):
    return value or Decimal("0.00")


def _document_queryset_for_tab(tab):
    documents = Document.objects.select_related("type_document", "filiere", "contributeur").order_by("-created_at")
    if tab == "valides":
        return documents.filter(valide=True)
    if tab == "refuses":
        return documents.filter(valide=False).exclude(motif_refus="")
    return documents.filter(valide=False, motif_refus="")


def _user_role(user):
    if user.is_superuser:
        return "Administration"
    group_names = set(user.groups.values_list("name", flat=True))
    for role in ("Administration", "Secretariat", "Professeur", "Utilisateur"):
        if role in group_names:
            return role
    if user.is_staff:
        return "Administration"
    return "Utilisateur"


class AdminContextMixin(LoginRequiredMixin):
    login_url = "/accounts/login/"

    def get_context_data(self, **kwargs):
        _seed_reference_if_needed()
        context = super().get_context_data(**kwargs)
        user = self.request.user
        admin_name = user.get_full_name().strip() or user.username if user.is_authenticated else "Administration"
        admin_role = _user_role(user) if user.is_authenticated else "Administration"
        filieres_qs = _safe_queryset(Filiere, ("nom",))
        context.update(
            {
                "admin_display_name": admin_name,
                "admin_role": admin_role,
                "filieres": filieres_qs.filter(cycle=Filiere.CYCLE_LICENCE_PRO),
                "toutes_filieres": filieres_qs,
                "filieres_licence": filieres_qs.filter(cycle=Filiere.CYCLE_LICENCE_PRO),
                "filieres_master": filieres_qs.filter(cycle=Filiere.CYCLE_MASTER_PRO),
                "licences": _safe_queryset(Licence, ("ordre", "code")),
                "matieres": _safe_queryset(Matiere, ("nom",)),
                "annees_academiques": _safe_queryset(AnneeAcademique, ("-libelle",)),
                "semestres": _safe_queryset(Semestre, ("ordre", "code")),
                "professeurs": _safe_queryset(Professeur, ("nom_complet",)),
                "etudiants": _safe_queryset(EtudiantProfile, ("matricule",)).select_related("utilisateur", "filiere"),
                "seances": _safe_queryset(Seance, ("date", "heure_debut")),
                "cars_transport": _safe_queryset(CarTransport, ("nom", "immatriculation")),
                "inscriptions_transport": _safe_queryset(InscriptionTransport, ("-created_at",)).select_related("etudiant__utilisateur", "car"),
                "creneaux_absence": _safe_queryset(CreneauAbsence, ("ordre", "heure_debut")),
            }
        )
        try:
            context["notes_incompletes_count"] = NoteBulletin.objects.filter(
                Q(note_cc=0) | Q(note_examen=0)
            ).count()
            context["badge_inscriptions_count"] = Inscription.objects.filter(statut=Inscription.STATUT_EN_ATTENTE).count()
            context["badge_paiements_count"] = Paiement.objects.filter(statut=Paiement.STATUT_EN_ATTENTE).count()
            context["badge_bibliotheque_count"] = Document.objects.filter(valide=False, motif_refus="").count()
            context["admin_search_url"] = reverse("administration:global_search")
        except (OperationalError, ProgrammingError):
            context["notes_incompletes_count"] = 0
            context["badge_inscriptions_count"] = 0
            context["badge_paiements_count"] = 0
            context["badge_bibliotheque_count"] = 0
            context["admin_search_url"] = reverse("administration:global_search")
        return context


class AdminProfileView(AdminContextMixin, TemplateView):
    template_name = "administration/profil_admin.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_form"] = AdminProfileForm(instance=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        form = AdminProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil administrateur mis a jour.")
            return redirect("administration:profil_admin")
        messages.error(request, f"Erreur de validation: {form.errors.as_text()}")
        return redirect("administration:profil_admin")


class DashboardView(AdminContextMixin, TemplateView):
    template_name = "administration/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context["kpi_documents_attente"] = Document.objects.filter(valide=False).count()
            context["kpi_documents_valides"] = Document.objects.filter(valide=True).count()
            context["kpi_contributeurs"] = Document.objects.values("contributeur_id").distinct().count()
            context["kpi_total_matieres"] = Matiere.objects.filter(active=True).count()
            context["kpi_total_filieres"] = Filiere.objects.filter(active=True).count()
            context["kpi_total_etudiants"] = EtudiantProfile.objects.filter(actif=True).count()
            context["kpi_total_professeurs"] = Professeur.objects.filter(actif=True).count()
            context["kpi_total_cars"] = CarTransport.objects.filter(actif=True).count()
            context["kpi_total_inscriptions_transport"] = InscriptionTransport.objects.count()
            context["kpi_dossiers_attente"] = Inscription.objects.filter(statut=Inscription.STATUT_EN_ATTENTE).count()
            context["kpi_paiements_attente"] = Paiement.objects.filter(statut=Paiement.STATUT_EN_ATTENTE).count()
            context["kpi_assiduite_alertes"] = sum(
                1 for etudiant in EtudiantProfile.objects.filter(actif=True) if etudiant.taux_assiduite < 75
            )

            now = timezone.now()
            month_labels_fr = ["Jan", "Fev", "Mar", "Avr", "Mai", "Juin", "Juil", "Aout", "Sep", "Oct", "Nov", "Dec"]
            month_slots = []
            for offset in range(5, -1, -1):
                total_months = (now.year * 12 + now.month - 1) - offset
                year = total_months // 12
                month = (total_months % 12) + 1
                month_slots.append({"key": f"{year}-{month:02d}", "label": f"{month_labels_fr[month - 1]} {year}"})

            start_year, start_month_num = [int(value) for value in month_slots[0]["key"].split("-")]
            start_date = timezone.datetime(
                start_year,
                start_month_num,
                1,
                tzinfo=timezone.get_current_timezone(),
            )

            etudiants_by_month = {
                f'{item["month"].year}-{item["month"].month:02d}': item["total"]
                for item in (
                    EtudiantProfile.objects.filter(created_at__gte=start_date)
                    .annotate(month=TruncMonth("created_at"))
                    .values("month")
                    .annotate(total=Count("id"))
                )
            }
            documents_by_month = {
                f'{item["month"].year}-{item["month"].month:02d}': item["total"]
                for item in (
                    Document.objects.filter(created_at__gte=start_date)
                    .annotate(month=TruncMonth("created_at"))
                    .values("month")
                    .annotate(total=Count("id"))
                )
            }

            statut_counts = {
                item["statut"]: item["total"]
                for item in InscriptionTransport.objects.values("statut").annotate(total=Count("id"))
            }
            transport_status_labels = {
                InscriptionTransport.STATUT_EN_ATTENTE: "En attente",
                InscriptionTransport.STATUT_VALIDEE: "Validees",
                InscriptionTransport.STATUT_SUSPENDUE: "Suspendues",
            }

            filieres_top = list(
                Filiere.objects.filter(active=True)
                .annotate(total=Count("etudiants", filter=Q(etudiants__actif=True)))
                .order_by("-total", "nom")[:6]
            )

            capacite_totale = CarTransport.objects.filter(actif=True).aggregate(total=Count("id"))
            total_places = sum(car.capacite for car in CarTransport.objects.filter(actif=True))
            inscriptions_validees = statut_counts.get(InscriptionTransport.STATUT_VALIDEE, 0)
            occupation_pct = 0
            if total_places > 0:
                occupation_pct = min(round((inscriptions_validees / total_places) * 100), 100)

            context["dashboard_chart_data"] = {
                "labels_months": [slot["label"] for slot in month_slots],
                "series_etudiants": [etudiants_by_month.get(slot["key"], 0) for slot in month_slots],
                "series_documents": [documents_by_month.get(slot["key"], 0) for slot in month_slots],
                "documents_split": [context["kpi_documents_valides"], context["kpi_documents_attente"]],
                "transport_status_labels": [transport_status_labels[key] for key in transport_status_labels],
                "transport_status_values": [statut_counts.get(key, 0) for key in transport_status_labels],
                "filieres_labels": [item.nom for item in filieres_top] or ["Aucune filiere"],
                "filieres_values": [item.total for item in filieres_top] or [0],
                "transport_occupation": occupation_pct,
                "transport_disponibles": max(total_places - inscriptions_validees, 0),
                "transport_places_total": total_places,
                "cars_count": capacite_totale["total"] or 0,
            }
            recent_inscriptions = [
                {
                    "type": "primary",
                    "titre": f"Inscription {item.get_statut_display()} - {item.nom_complet}",
                    "date": item.updated_at,
                }
                for item in Inscription.objects.order_by("-updated_at")[:3]
            ]
            recent_paiements = [
                {
                    "type": "success",
                    "titre": f"Paiement recu - {item.scolarite.etudiant.nom_complet} - {item.montant:,.0f} FCFA",
                    "date": item.created_at,
                }
                for item in Paiement.objects.select_related("scolarite__etudiant__utilisateur").order_by("-created_at")[:3]
            ]
            recent_notes = [
                {
                    "type": "warning",
                    "titre": f"Notes saisies - {item.matiere.nom} - {item.bulletin.etudiant.matricule}",
                    "date": item.created_at,
                }
                for item in NoteBulletin.objects.select_related("matiere", "bulletin__etudiant").order_by("-created_at")[:3]
            ]
            context["activites_recentes"] = sorted(
                recent_inscriptions + recent_paiements + recent_notes,
                key=lambda item: item["date"],
                reverse=True,
            )[:5]
        except (OperationalError, ProgrammingError):
            context["kpi_documents_attente"] = 0
            context["kpi_documents_valides"] = 0
            context["kpi_contributeurs"] = 0
            context["kpi_total_matieres"] = 0
            context["kpi_total_filieres"] = 0
            context["kpi_total_etudiants"] = 0
            context["kpi_total_professeurs"] = 0
            context["kpi_total_cars"] = 0
            context["kpi_total_inscriptions_transport"] = 0
            context["kpi_dossiers_attente"] = 0
            context["kpi_paiements_attente"] = 0
            context["kpi_assiduite_alertes"] = 0
            context["activites_recentes"] = []
            context["dashboard_chart_data"] = {
                "labels_months": [],
                "series_etudiants": [],
                "series_documents": [],
                "documents_split": [0, 0],
                "transport_status_labels": ["En attente", "Validees", "Suspendues"],
                "transport_status_values": [0, 0, 0],
                "filieres_labels": ["Aucune filiere"],
                "filieres_values": [0],
                "transport_occupation": 0,
                "transport_disponibles": 0,
                "transport_places_total": 0,
                "cars_count": 0,
            }
        return context


class EtudiantsListeView(AdminContextMixin, TemplateView):
    template_name = "administration/etudiants_liste.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = (self.request.GET.get("q") or "").strip()
        filiere_id = (self.request.GET.get("filiere") or "").strip()
        licence_id = (self.request.GET.get("licence") or "").strip()
        matricule = (self.request.GET.get("matricule") or "").strip()

        etudiants = EtudiantProfile.objects.select_related("utilisateur", "filiere", "licence", "semestre")

        if q:
            etudiants = etudiants.filter(
                Q(matricule__icontains=q)
                | Q(utilisateur__first_name__icontains=q)
                | Q(utilisateur__last_name__icontains=q)
                | Q(utilisateur__email__icontains=q)
            )
        if filiere_id:
            etudiants = etudiants.filter(filiere_id=filiere_id)
        if licence_id:
            etudiants = etudiants.filter(licence_id=licence_id)
        if matricule:
            etudiants = etudiants.filter(matricule__icontains=matricule)

        etudiants = etudiants.order_by("utilisateur__last_name", "utilisateur__first_name", "matricule")
        page_obj, page_query = _paginate(self.request, etudiants)

        context.update(
            {
                "etudiants": page_obj.object_list,
                "page_obj": page_obj,
                "page_query": page_query,
                "filters": {
                    "q": q,
                    "filiere": filiere_id,
                    "licence": licence_id,
                    "matricule": matricule,
                },
                "etudiant_form": EtudiantProfileForm(),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        object_id = request.POST.get("object_id")

        if action == "create_etudiant":
            form = EtudiantProfileForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, "Etudiant cree avec succes.")
            else:
                messages.error(request, f"Erreur de validation: {form.errors.as_text()}")
            return redirect("administration:etudiants_liste")

        if action == "update_etudiant":
            etudiant = get_object_or_404(EtudiantProfile, pk=object_id)
            form = EtudiantProfileForm(request.POST, request.FILES, instance=etudiant)
            if form.is_valid():
                form.save()
                messages.success(request, "Etudiant modifie avec succes.")
            else:
                messages.error(request, f"Erreur de validation: {form.errors.as_text()}")
            return redirect("administration:etudiants_liste")

        if action == "delete_etudiant":
            etudiant = get_object_or_404(EtudiantProfile, pk=object_id)
            user = etudiant.utilisateur
            etudiant.delete()
            if user and not user.is_superuser and not user.is_staff:
                user.delete()
            messages.success(request, "Etudiant supprime avec succes.")
            return redirect("administration:etudiants_liste")

        messages.error(request, "Action non reconnue.")
        return redirect("administration:etudiants_liste")


class EtudiantDetailView(AdminContextMixin, TemplateView):
    template_name = "administration/etudiant_detail.html"

    def _get_etudiant(self):
        etudiant_id = self.kwargs.get("etudiant_id") or self.request.GET.get("id")
        if etudiant_id:
            return get_object_or_404(
                EtudiantProfile.objects.select_related("utilisateur", "filiere", "licence", "semestre"),
                pk=etudiant_id,
            )
        return EtudiantProfile.objects.select_related("utilisateur", "filiere", "licence", "semestre").first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        etudiant = self._get_etudiant()
        if not etudiant:
            context["etudiant"] = None
            context["bulletins"] = []
            return context

        bulletins = (
            Bulletin.objects.filter(etudiant=etudiant)
            .select_related("annee_academique", "semestre")
            .prefetch_related("notes__matiere", "notes__professeur")
            .order_by("-annee_academique__libelle", "semestre__ordre")
        )

        context.update(
            {
                "etudiant": etudiant,
                "bulletins": bulletins,
                "bulletin_form": BulletinForm(),
                "note_form": NoteBulletinForm(),
                "etudiant_form": EtudiantProfileForm(instance=etudiant),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        etudiant = self._get_etudiant()
        if not etudiant:
            messages.error(request, "Aucun etudiant disponible.")
            return redirect("administration:etudiants_liste")

        action = request.POST.get("action")
        object_id = request.POST.get("object_id")

        if action == "update_etudiant":
            form = EtudiantProfileForm(request.POST, request.FILES, instance=etudiant)
            if form.is_valid():
                form.save()
                messages.success(request, "Profil etudiant mis a jour.")
            else:
                messages.error(request, f"Erreur de validation: {form.errors.as_text()}")
            return redirect("administration:etudiant_detail", etudiant_id=etudiant.id)

        if action == "create_bulletin":
            form = BulletinForm(request.POST)
            if form.is_valid():
                bulletin = form.save(commit=False)
                bulletin.etudiant = etudiant
                bulletin.save()
                messages.success(request, "Bulletin cree avec succes.")
            else:
                messages.error(request, f"Erreur de validation bulletin: {form.errors.as_text()}")
            return redirect("administration:etudiant_detail", etudiant_id=etudiant.id)

        if action == "update_bulletin":
            bulletin = get_object_or_404(Bulletin, pk=object_id, etudiant=etudiant)
            form = BulletinForm(request.POST, instance=bulletin)
            if form.is_valid():
                form.save()
                messages.success(request, "Bulletin mis a jour.")
            else:
                messages.error(request, f"Erreur de validation bulletin: {form.errors.as_text()}")
            return redirect("administration:etudiant_detail", etudiant_id=etudiant.id)

        if action == "delete_bulletin":
            bulletin = get_object_or_404(Bulletin, pk=object_id, etudiant=etudiant)
            bulletin.delete()
            messages.success(request, "Bulletin supprime.")
            return redirect("administration:etudiant_detail", etudiant_id=etudiant.id)

        if action == "create_note":
            bulletin = get_object_or_404(Bulletin, pk=request.POST.get("bulletin_id"), etudiant=etudiant)
            form = NoteBulletinForm(request.POST)
            if form.is_valid():
                note = form.save(commit=False)
                note.bulletin = bulletin
                note.save()
                messages.success(request, "Note ajoutee au bulletin.")
            else:
                messages.error(request, f"Erreur de validation note: {form.errors.as_text()}")
            return redirect("administration:etudiant_detail", etudiant_id=etudiant.id)

        if action == "update_note":
            note = get_object_or_404(NoteBulletin.objects.select_related("bulletin"), pk=object_id, bulletin__etudiant=etudiant)
            form = NoteBulletinForm(request.POST, instance=note)
            if form.is_valid():
                form.save()
                messages.success(request, "Note mise a jour.")
            else:
                messages.error(request, f"Erreur de validation note: {form.errors.as_text()}")
            return redirect("administration:etudiant_detail", etudiant_id=etudiant.id)

        if action == "delete_note":
            note = get_object_or_404(NoteBulletin.objects.select_related("bulletin"), pk=object_id, bulletin__etudiant=etudiant)
            note.delete()
            messages.success(request, "Note supprimee.")
            return redirect("administration:etudiant_detail", etudiant_id=etudiant.id)

        messages.error(request, "Action non reconnue.")
        return redirect("administration:etudiant_detail", etudiant_id=etudiant.id)


class ProfesseursView(AdminContextMixin, TemplateView):
    template_name = "administration/professeurs.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = (self.request.GET.get("q") or "").strip()
        professeurs = Professeur.objects.prefetch_related("matieres__filiere")
        if q:
            professeurs = professeurs.filter(
                Q(nom_complet__icontains=q) | Q(email__icontains=q) | Q(telephone__icontains=q)
            )
        context.update({"professeurs": professeurs.order_by("nom_complet"), "q": q, "professeur_form": ProfesseurForm()})
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        object_id = request.POST.get("object_id")

        if action == "create_professeur":
            form = ProfesseurForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Professeur ajoute avec succes.")
            else:
                messages.error(request, f"Erreur de validation: {form.errors.as_text()}")
            return redirect("administration:professeurs")

        if action == "update_professeur":
            professeur = get_object_or_404(Professeur, pk=object_id)
            form = ProfesseurForm(request.POST, instance=professeur)
            if form.is_valid():
                form.save()
                messages.success(request, "Professeur modifie avec succes.")
            else:
                messages.error(request, f"Erreur de validation: {form.errors.as_text()}")
            return redirect("administration:professeurs")

        if action == "delete_professeur":
            professeur = get_object_or_404(Professeur, pk=object_id)
            professeur.delete()
            messages.success(request, "Professeur supprime avec succes.")
            return redirect("administration:professeurs")

        messages.error(request, "Action non reconnue.")
        return redirect("administration:professeurs")


class InscriptionsView(AdminContextMixin, TemplateView):
    template_name = "administration/inscriptions.html"

    status_tabs = (
        (Inscription.STATUT_EN_ATTENTE, "En attente"),
        (Inscription.STATUT_EN_COURS, "En cours"),
        (Inscription.STATUT_VALIDEE, "Valides"),
        (Inscription.STATUT_REFUSEE, "Refuses"),
        (Inscription.STATUT_INCOMPLETE, "Incomplets"),
    )

    def _filtered_dossiers(self):
        statut = self.request.GET.get("statut") or Inscription.STATUT_EN_ATTENTE
        dossiers = Dossier.objects.select_related("inscription__filiere", "inscription__licence")
        if statut:
            dossiers = dossiers.filter(inscription__statut=statut)
        return dossiers.order_by("-inscription__date_soumission")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        statut = self.request.GET.get("statut") or Inscription.STATUT_EN_ATTENTE
        counts = {
            item["statut"]: item["total"]
            for item in Inscription.objects.values("statut").annotate(total=Count("id"))
        }
        dossiers = self._filtered_dossiers()
        page_obj, page_query = _paginate(self.request, dossiers)
        context.update(
            {
                "active_statut": statut,
                "status_tabs": [
                    {"code": code, "label": label, "count": counts.get(code, 0)}
                    for code, label in self.status_tabs
                ],
                "dossiers": page_obj.object_list,
                "page_obj": page_obj,
                "page_query": page_query,
                "en_attente_count": counts.get(Inscription.STATUT_EN_ATTENTE, 0),
            }
        )
        return context

    def get(self, request, *args, **kwargs):
        if request.GET.get("export") == "1":
            return self._export_csv()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        dossier = get_object_or_404(Dossier.objects.select_related("inscription"), pk=request.POST.get("object_id"))
        action = request.POST.get("action")

        if action == "validate_dossier":
            dossier.inscription.creer_compte_etudiant()
            messages.success(request, "Dossier valide et compte etudiant cree ou mis a jour.")
            return redirect("administration:inscriptions")

        if action == "refuse_dossier":
            dossier.inscription.statut = Inscription.STATUT_REFUSEE
            dossier.inscription.save(update_fields=["statut", "updated_at"])
            messages.success(request, "Dossier refuse.")
            return redirect("administration:inscriptions")

        if action == "mark_incomplete":
            dossier.inscription.statut = Inscription.STATUT_INCOMPLETE
            dossier.inscription.save(update_fields=["statut", "updated_at"])
            messages.success(request, "Dossier marque comme incomplet.")
            return redirect("administration:dossier_detail", dossier_id=dossier.id)

        messages.error(request, "Action non reconnue.")
        return redirect("administration:inscriptions")

    def _export_csv(self):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="dossiers_inscription.csv"'
        response.write("\ufeff")
        writer = csv.writer(response)
        writer.writerow(["Candidat", "Email", "Telephone", "Filiere", "Niveau", "Statut", "Date soumission", "Documents fournis", "Documents manquants"])
        for dossier in self._filtered_dossiers():
            inscription = dossier.inscription
            writer.writerow(
                [
                    inscription.nom_complet,
                    inscription.email,
                    inscription.telephone,
                    inscription.filiere.nom,
                    str(inscription.licence),
                    inscription.get_statut_display(),
                    inscription.date_soumission.strftime("%d/%m/%Y"),
                    dossier.documents_fournis,
                    dossier.documents_manquants,
                ]
            )
        return response


class DossierDetailView(AdminContextMixin, TemplateView):
    template_name = "administration/dossier_detail.html"

    def _get_dossier(self):
        dossier_id = self.kwargs.get("dossier_id") or self.request.GET.get("id")
        if dossier_id:
            return get_object_or_404(
                Dossier.objects.select_related("inscription__filiere", "inscription__licence"),
                pk=dossier_id,
            )
        return Dossier.objects.select_related("inscription__filiere", "inscription__licence").first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dossier"] = self._get_dossier()
        return context

    def post(self, request, *args, **kwargs):
        dossier = self._get_dossier()
        if not dossier:
            messages.error(request, "Aucun dossier disponible.")
            return redirect("administration:inscriptions")

        action = request.POST.get("action")
        dossier.commentaire_interne = request.POST.get("commentaire_interne", dossier.commentaire_interne)
        dossier.motif_refus = request.POST.get("motif_refus", dossier.motif_refus)
        dossier.save()

        if action == "validate_dossier":
            dossier.inscription.creer_compte_etudiant()
            messages.success(request, "Dossier valide et compte etudiant cree ou mis a jour.")
            return redirect("administration:dossier_detail", dossier_id=dossier.id)

        if action == "refuse_dossier":
            dossier.inscription.statut = Inscription.STATUT_REFUSEE
            dossier.inscription.save(update_fields=["statut", "updated_at"])
            messages.success(request, "Dossier refuse.")
            return redirect("administration:dossier_detail", dossier_id=dossier.id)

        if action == "mark_incomplete":
            dossier.inscription.statut = Inscription.STATUT_INCOMPLETE
            dossier.inscription.save(update_fields=["statut", "updated_at"])
            messages.success(request, "Dossier marque comme incomplet.")
            return redirect("administration:dossier_detail", dossier_id=dossier.id)

        if action == "save_comment":
            messages.success(request, "Commentaire interne enregistre.")
            return redirect("administration:dossier_detail", dossier_id=dossier.id)

        messages.error(request, "Action non reconnue.")
        return redirect("administration:dossier_detail", dossier_id=dossier.id)


class PaiementsView(AdminContextMixin, TemplateView):
    template_name = "administration/paiements.html"

    def _filters(self):
        return {
            "filiere": (self.request.GET.get("filiere") or "").strip(),
            "statut": (self.request.GET.get("statut") or "").strip(),
            "moyen": (self.request.GET.get("moyen") or "").strip(),
            "periode_debut": (self.request.GET.get("periode_debut") or "").strip(),
            "periode_fin": (self.request.GET.get("periode_fin") or "").strip(),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = self._filters()
        for etudiant in EtudiantProfile.objects.filter(actif=True):
            Scolarite.objects.get_or_create(etudiant=etudiant)

        scolarites = Scolarite.objects.select_related("etudiant__utilisateur", "etudiant__filiere").prefetch_related("paiements")
        paiements = Paiement.objects.select_related("scolarite__etudiant")

        if filters["filiere"]:
            scolarites = scolarites.filter(etudiant__filiere_id=filters["filiere"])
            paiements = paiements.filter(scolarite__etudiant__filiere_id=filters["filiere"])
        if filters["moyen"]:
            scolarites = scolarites.filter(paiements__moyen=filters["moyen"]).distinct()
            paiements = paiements.filter(moyen=filters["moyen"])
        if filters["periode_debut"]:
            paiements = paiements.filter(date__gte=filters["periode_debut"])
        if filters["periode_fin"]:
            paiements = paiements.filter(date__lte=filters["periode_fin"])

        rows = []
        for scolarite in scolarites:
            total_paye = scolarite.total_paye
            reste = scolarite.reste_a_payer
            statut = scolarite.statut
            if filters["statut"] and statut != filters["statut"]:
                continue
            rows.append(
                {
                    "scolarite": scolarite,
                    "etudiant": scolarite.etudiant,
                    "total_paye": total_paye,
                    "reste": reste,
                    "statut": statut,
                    "statut_label": scolarite.statut_label,
                    "dernier_paiement": scolarite.dernier_paiement,
                    "historique": scolarite.paiements.order_by("-date", "-created_at")[:10],
                }
            )

        now = timezone.localdate()
        month_start = now.replace(day=1)
        recettes_annuelles = Paiement.objects.filter(statut=Paiement.STATUT_VERIFIE, date__year=now.year).aggregate(total=Sum("montant"))["total"]
        recettes_mois = Paiement.objects.filter(statut=Paiement.STATUT_VERIFIE, date__gte=month_start).aggregate(total=Sum("montant"))["total"]
        reste_a_payer = sum((row["reste"] for row in rows), Decimal("0.00"))
        etudiants_retard = sum(1 for row in rows if row["reste"] > 0 and row["scolarite"].date_echeance and row["scolarite"].date_echeance < now)

        page_obj, page_query = _paginate(self.request, rows)

        context.update(
            {
                "filters": filters,
                "paiement_form": PaiementForm(),
                "paiement_moyens": Paiement.MOYEN_CHOICES,
                "paiement_statuts": (("complet", "Complet"), ("partiel", "Partiel"), ("impaye", "Impaye")),
                "paiements_rows": page_obj.object_list,
                "page_obj": page_obj,
                "page_query": page_query,
                "paiements_en_attente": Paiement.objects.filter(statut=Paiement.STATUT_EN_ATTENTE).select_related(
                    "scolarite__etudiant__utilisateur"
                ),
                "kpi_recettes_annuelles": _money(recettes_annuelles),
                "kpi_recettes_mois": _money(recettes_mois),
                "kpi_reste_a_payer": reste_a_payer,
                "kpi_etudiants_retard": etudiants_retard,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "create_paiement":
            form = PaiementForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Paiement enregistre et place en attente de verification.")
            else:
                messages.error(request, f"Erreur de validation: {form.errors.as_text()}")
            return redirect("administration:paiements")

        if action in {"verify_paiement", "reject_paiement"}:
            paiement = get_object_or_404(Paiement, pk=request.POST.get("object_id"))
            paiement.statut = Paiement.STATUT_VERIFIE if action == "verify_paiement" else Paiement.STATUT_REJETE
            paiement.save(update_fields=["statut", "updated_at"])
            messages.success(request, "Statut du paiement mis a jour.")
            return redirect("administration:paiements")

        messages.error(request, "Action non reconnue.")
        return redirect("administration:paiements")


class TransportCarsView(AdminContextMixin, TemplateView):
    template_name = "administration/transport_cars.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["car_form"] = CarTransportForm()
        context["inscription_transport_form"] = InscriptionTransportForm()
        context["etudiants"] = EtudiantProfile.objects.select_related("utilisateur").order_by("matricule")
        context["axes_transport"] = CarTransport.AXE_CHOICES
        context["inscriptions_par_axe"] = {
            axe_code: InscriptionTransport.objects.filter(axe=axe_code).count()
            for axe_code, _ in CarTransport.AXE_CHOICES
        }
        context["axes_cards"] = [
            {"code": axe_code, "label": axe_label, "count": context["inscriptions_par_axe"].get(axe_code, 0)}
            for axe_code, axe_label in CarTransport.AXE_CHOICES
        ]
        cars = list(context["cars_transport"])
        for car in cars:
            car.places_occupees = car.inscriptions.filter(statut=InscriptionTransport.STATUT_VALIDEE).count()
            car.places_disponibles = max(car.capacite - car.places_occupees, 0)
        cars_page, cars_query = _paginate(self.request, cars)
        inscriptions_page, inscriptions_query = _paginate(
            self.request,
            InscriptionTransport.objects.select_related("etudiant__utilisateur", "car").order_by("-created_at"),
        )
        context["cars_transport"] = cars_page.object_list
        context["cars_page_obj"] = cars_page
        context["cars_page_query"] = cars_query
        context["inscriptions_transport"] = inscriptions_page.object_list
        context["transport_inscriptions_page_obj"] = inscriptions_page
        context["transport_inscriptions_page_query"] = inscriptions_query
        total_places = sum(car.capacite for car in cars if car.actif)
        places_occupees = sum(car.places_occupees for car in cars if car.actif)
        context["transport_kpis"] = {
            "cars_actifs": sum(1 for car in cars if car.actif),
            "inscriptions": InscriptionTransport.objects.count(),
            "cars_inactifs": sum(1 for car in cars if not car.actif),
            "occupation_pct": round((places_occupees / total_places) * 100) if total_places else 0,
            "places_occupees": places_occupees,
            "total_places": total_places,
        }
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        object_id = request.POST.get("object_id")

        if action == "create_car":
            form = CarTransportForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Car enregistre avec succes.")
            else:
                messages.error(request, f"Erreur de validation: {form.errors.as_text()}")
            return redirect("administration:transport_cars")

        if action == "update_car":
            car = get_object_or_404(CarTransport, pk=object_id)
            form = CarTransportForm(request.POST, instance=car)
            if form.is_valid():
                form.save()
                messages.success(request, "Car mis a jour avec succes.")
            else:
                messages.error(request, f"Erreur de validation: {form.errors.as_text()}")
            return redirect("administration:transport_cars")

        if action == "delete_car":
            car = get_object_or_404(CarTransport, pk=object_id)
            car.delete()
            messages.success(request, "Car supprime avec succes.")
            return redirect("administration:transport_cars")

        if action == "create_inscription_transport":
            form = InscriptionTransportForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Inscription transport enregistree avec succes.")
            else:
                messages.error(request, f"Erreur de validation: {form.errors.as_text()}")
            return redirect("administration:transport_cars")

        if action == "update_inscription_transport":
            inscription = get_object_or_404(InscriptionTransport, pk=object_id)
            form = InscriptionTransportForm(request.POST, instance=inscription)
            if form.is_valid():
                form.save()
                messages.success(request, "Inscription transport mise a jour.")
            else:
                messages.error(request, f"Erreur de validation: {form.errors.as_text()}")
            return redirect("administration:transport_cars")

        if action == "delete_inscription_transport":
            inscription = get_object_or_404(InscriptionTransport, pk=object_id)
            inscription.delete()
            messages.success(request, "Inscription transport supprimee.")
            return redirect("administration:transport_cars")

        messages.error(request, "Action non reconnue.")
        return redirect("administration:transport_cars")


class NotesView(AdminContextMixin, TemplateView):
    template_name = "administration/notes.html"

    def _filters(self):
        return {
            "filiere": (self.request.GET.get("filiere") or self.request.POST.get("filiere") or "").strip(),
            "licence": (self.request.GET.get("licence") or self.request.POST.get("licence") or "").strip(),
            "semestre": (self.request.GET.get("semestre") or self.request.POST.get("semestre") or "").strip(),
            "annee_academique": (self.request.GET.get("annee_academique") or self.request.POST.get("annee_academique") or "").strip(),
            "matiere": (self.request.GET.get("matiere") or self.request.POST.get("matiere") or "").strip(),
            "matricule": (self.request.GET.get("matricule") or self.request.POST.get("matricule") or "").strip(),
        }

    def _redirect_with_filters(self, filters):
        query = "&".join(f"{key}={value}" for key, value in filters.items() if value)
        suffix = f"?{query}" if query else ""
        return redirect(f"{reverse('administration:notes')}{suffix}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = self._filters()
        filiere_id = filters["filiere"]
        licence_id = filters["licence"]
        semestre_id = filters["semestre"]
        annee_id = filters["annee_academique"]
        matiere_id = filters["matiere"]
        matricule = filters["matricule"]

        try:
            matieres = Matiere.objects.filter(active=True).select_related("filiere").prefetch_related("professeurs")
            all_matieres = matieres
            etudiants = EtudiantProfile.objects.filter(actif=True)
            bulletins = Bulletin.objects.select_related("etudiant__utilisateur", "annee_academique", "semestre")

            if filiere_id:
                matieres = matieres.filter(filiere_id=filiere_id)
                etudiants = etudiants.filter(filiere_id=filiere_id)
                bulletins = bulletins.filter(etudiant__filiere_id=filiere_id)
            if licence_id:
                etudiants = etudiants.filter(licence_id=licence_id)
                bulletins = bulletins.filter(etudiant__licence_id=licence_id)
            if semestre_id:
                etudiants = etudiants.filter(semestre_id=semestre_id)
                bulletins = bulletins.filter(semestre_id=semestre_id)
            if annee_id:
                bulletins = bulletins.filter(annee_academique_id=annee_id)

            selected_matiere = Matiere.objects.filter(pk=matiere_id).select_related("filiere").first() if matiere_id else None
            selected_semestre = Semestre.objects.filter(pk=semestre_id).first() if semestre_id else None
            selected_annee = AnneeAcademique.objects.filter(pk=annee_id).first() if annee_id else None
            notes_entry_rows = []
            if selected_matiere and selected_semestre and selected_annee:
                bulletins_for_entry = Bulletin.objects.filter(
                    etudiant__in=etudiants,
                    annee_academique=selected_annee,
                    semestre=selected_semestre,
                ).select_related("etudiant")
                bulletin_by_student = {item.etudiant_id: item for item in bulletins_for_entry}
                notes = NoteBulletin.objects.filter(
                    bulletin__in=bulletins_for_entry,
                    matiere=selected_matiere,
                ).select_related("professeur")
                note_by_bulletin = {item.bulletin_id: item for item in notes}
                for etudiant in etudiants.select_related("utilisateur").order_by("utilisateur__last_name", "utilisateur__first_name", "matricule")[:20]:
                    bulletin = bulletin_by_student.get(etudiant.id)
                    notes_entry_rows.append({
                        "etudiant": etudiant,
                        "bulletin": bulletin,
                        "note": note_by_bulletin.get(bulletin.id) if bulletin else None,
                    })

            expected_count = bulletins.count() if annee_id or semestre_id else etudiants.count()
            matieres_stats = list(matieres.order_by("nom")[:50])
            for matiere in matieres_stats:
                notes_qs = NoteBulletin.objects.filter(matiere=matiere)
                if filiere_id:
                    notes_qs = notes_qs.filter(bulletin__etudiant__filiere_id=filiere_id)
                if licence_id:
                    notes_qs = notes_qs.filter(bulletin__etudiant__licence_id=licence_id)
                if semestre_id:
                    notes_qs = notes_qs.filter(bulletin__semestre_id=semestre_id)
                if annee_id:
                    notes_qs = notes_qs.filter(bulletin__annee_academique_id=annee_id)

                total_notes = notes_qs.values("bulletin_id").distinct().count()
                matiere.cc_saisi = expected_count > 0 and total_notes >= expected_count
                matiere.exam_saisi = expected_count > 0 and total_notes >= expected_count
                matiere.notes_saisies_count = total_notes
                matiere.notes_attendues_count = expected_count
                matiere.saisie_complete = matiere.cc_saisi and matiere.exam_saisi

            context["matieres_stats"] = matieres_stats
            context["bulletins_recent"] = (
                bulletins.select_related("etudiant__utilisateur", "annee_academique", "semestre")
                .order_by("-updated_at")[:20]
            )
            context["filieres"] = Filiere.objects.filter(active=True).order_by("nom")
            context["matieres_pour_saisie"] = all_matieres.order_by("nom")
            context["notes_entry_rows"] = notes_entry_rows
            context["selected_matiere"] = selected_matiere
            context["filters"] = filters
        except (OperationalError, ProgrammingError):
            context["matieres_stats"] = []
            context["bulletins_recent"] = []
            context["notes_entry_rows"] = []
            context["filters"] = filters
        return context

    def post(self, request, *args, **kwargs):
        filters = self._filters()
        action = request.POST.get("action")
        if action != "save_notes":
            messages.error(request, "Action non reconnue.")
            return self._redirect_with_filters(filters)

        matiere = get_object_or_404(Matiere, pk=filters["matiere"])
        semestre = get_object_or_404(Semestre, pk=filters["semestre"])
        annee = get_object_or_404(AnneeAcademique, pk=filters["annee_academique"])
        publish = _to_bool(request.POST.get("publie"))
        saved = 0
        etudiants = EtudiantProfile.objects.filter(pk__in=request.POST.getlist("etudiant_ids")).select_related("utilisateur")
        for etudiant in etudiants:
            cc_raw = (request.POST.get(f"note_cc_{etudiant.id}") or "").strip()
            exam_raw = (request.POST.get(f"note_examen_{etudiant.id}") or "").strip()
            coeff_raw = (request.POST.get(f"coefficient_{etudiant.id}") or "1").strip()
            professeur_id = (request.POST.get(f"professeur_{etudiant.id}") or "").strip()
            if not cc_raw and not exam_raw:
                continue
            bulletin, _ = Bulletin.objects.get_or_create(
                etudiant=etudiant,
                annee_academique=annee,
                semestre=semestre,
                defaults={"publie": publish},
            )
            if publish and not bulletin.publie:
                bulletin.publie = True
                bulletin.save(update_fields=["publie", "updated_at"])
            note, _ = NoteBulletin.objects.get_or_create(
                bulletin=bulletin,
                matiere=matiere,
                defaults={"coefficient": int(coeff_raw or 1)},
            )
            note.coefficient = int(coeff_raw or 1)
            note.note_cc = Decimal(cc_raw or "0")
            note.note_examen = Decimal(exam_raw or "0")
            note.professeur_id = professeur_id or None
            note.save()
            saved += 1
        messages.success(request, f"{saved} note(s) enregistree(s).")
        return self._redirect_with_filters(filters)


class NotesSaisieView(AdminContextMixin, TemplateView):
    template_name = "administration/notes_saisie.html"

    def _filters(self):
        return {
            "filiere": (self.request.GET.get("filiere") or self.request.POST.get("filiere") or "").strip(),
            "licence": (self.request.GET.get("licence") or self.request.POST.get("licence") or "").strip(),
            "semestre": (self.request.GET.get("semestre") or self.request.POST.get("semestre") or "").strip(),
            "annee_academique": (self.request.GET.get("annee_academique") or self.request.POST.get("annee_academique") or "").strip(),
            "matiere": (self.request.GET.get("matiere") or self.request.POST.get("matiere") or "").strip(),
        }

    def _redirect_with_filters(self, filters):
        query = "&".join(f"{key}={value}" for key, value in filters.items() if value)
        suffix = f"?{query}" if query else ""
        return redirect(f"{reverse('administration:notes_saisie')}{suffix}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = self._filters()
        selected_matiere = Matiere.objects.filter(pk=filters["matiere"]).select_related("filiere").first() if filters["matiere"] else None
        selected_semestre = Semestre.objects.filter(pk=filters["semestre"]).first() if filters["semestre"] else None
        selected_annee = AnneeAcademique.objects.filter(pk=filters["annee_academique"]).first() if filters["annee_academique"] else None

        etudiants = EtudiantProfile.objects.select_related("utilisateur", "filiere", "licence").filter(actif=True)
        if filters["filiere"]:
            etudiants = etudiants.filter(filiere_id=filters["filiere"])
        if filters["licence"]:
            etudiants = etudiants.filter(licence_id=filters["licence"])

        rows = []
        if selected_matiere and selected_semestre and selected_annee:
            bulletins = Bulletin.objects.filter(
                etudiant__in=etudiants,
                annee_academique=selected_annee,
                semestre=selected_semestre,
            ).select_related("etudiant")
            bulletin_by_student = {item.etudiant_id: item for item in bulletins}
            notes = NoteBulletin.objects.filter(
                bulletin__in=bulletins,
                matiere=selected_matiere,
            ).select_related("bulletin", "professeur")
            note_by_bulletin = {item.bulletin_id: item for item in notes}
            for etudiant in etudiants.order_by("utilisateur__last_name", "utilisateur__first_name", "matricule"):
                bulletin = bulletin_by_student.get(etudiant.id)
                note = note_by_bulletin.get(bulletin.id) if bulletin else None
                rows.append({"etudiant": etudiant, "bulletin": bulletin, "note": note})

        context.update(
            {
                "filters": filters,
                "selected_matiere": selected_matiere,
                "selected_semestre": selected_semestre,
                "selected_annee": selected_annee,
                "notes_rows": rows,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        filters = self._filters()
        action = request.POST.get("action")
        matiere = get_object_or_404(Matiere, pk=filters["matiere"])
        semestre = get_object_or_404(Semestre, pk=filters["semestre"])
        annee = get_object_or_404(AnneeAcademique, pk=filters["annee_academique"])

        if action == "delete_note_saisie":
            note = get_object_or_404(NoteBulletin, pk=request.POST.get("note_id"))
            note.delete()
            messages.success(request, "Note retiree du bulletin.")
            return self._redirect_with_filters(filters)

        if action == "save_notes":
            publish = _to_bool(request.POST.get("publie"))
            etudiants = EtudiantProfile.objects.filter(pk__in=request.POST.getlist("etudiant_ids")).select_related("utilisateur")
            saved = 0
            for etudiant in etudiants:
                cc_raw = (request.POST.get(f"note_cc_{etudiant.id}") or "").strip()
                exam_raw = (request.POST.get(f"note_examen_{etudiant.id}") or "").strip()
                coeff_raw = (request.POST.get(f"coefficient_{etudiant.id}") or "1").strip()
                professeur_id = (request.POST.get(f"professeur_{etudiant.id}") or "").strip()
                if not cc_raw and not exam_raw:
                    continue
                bulletin, _ = Bulletin.objects.get_or_create(
                    etudiant=etudiant,
                    annee_academique=annee,
                    semestre=semestre,
                    defaults={"publie": publish},
                )
                if publish and not bulletin.publie:
                    bulletin.publie = True
                    bulletin.save(update_fields=["publie", "updated_at"])
                note, _ = NoteBulletin.objects.get_or_create(
                    bulletin=bulletin,
                    matiere=matiere,
                    defaults={"coefficient": int(coeff_raw or 1)},
                )
                note.coefficient = int(coeff_raw or 1)
                note.note_cc = Decimal(cc_raw or "0")
                note.note_examen = Decimal(exam_raw or "0")
                note.professeur_id = professeur_id or None
                note.save()
                saved += 1
            messages.success(request, f"{saved} note(s) enregistree(s) sur les bulletins.")
            return self._redirect_with_filters(filters)

        messages.error(request, "Action non reconnue.")
        return self._redirect_with_filters(filters)


class PresencesView(AdminContextMixin, TemplateView):
    template_name = "administration/presences.html"

    def _filters(self):
        return {
            "filiere": (self.request.GET.get("filiere") or self.request.POST.get("filiere") or "").strip(),
            "matiere": (self.request.GET.get("matiere") or self.request.POST.get("matiere") or "").strip(),
            "date": (self.request.GET.get("date") or self.request.POST.get("date") or str(timezone.localdate())).strip(),
            "creneau": (self.request.GET.get("creneau") or self.request.POST.get("creneau") or "").strip(),
        }

    def _presence_rows(self, filters, create_missing=False):
        if not all((filters["filiere"], filters["matiere"], filters["date"], filters["creneau"])):
            return []

        creneau = CreneauAbsence.objects.filter(pk=filters["creneau"]).first()
        seance = None
        if creneau:
            seance = (
                Seance.objects.filter(
                    filiere_id=filters["filiere"],
                    matiere_id=filters["matiere"],
                    date=filters["date"],
                    heure_debut=creneau.heure_debut,
                    heure_fin=creneau.heure_fin,
                )
                .order_by("professeur__nom_complet")
                .first()
            )

        etudiants = EtudiantProfile.objects.filter(actif=True, filiere_id=filters["filiere"]).select_related(
            "utilisateur", "filiere", "licence", "semestre"
        )
        rows = []
        for etudiant in etudiants.order_by("utilisateur__last_name", "utilisateur__first_name", "matricule"):
            lookup = {
                "etudiant": etudiant,
                "matiere_id": filters["matiere"],
                "date": filters["date"],
                "creneau_id": filters["creneau"],
            }
            if create_missing:
                presence, created = Presence.objects.get_or_create(defaults={"present": True, "seance": seance}, **lookup)
                if not created and seance and presence.seance_id != seance.id:
                    presence.seance = seance
                    presence.save(update_fields=["seance", "updated_at"])
            else:
                presence = Presence.objects.filter(**lookup).first()
            rows.append({"etudiant": etudiant, "presence": presence, "present": True if presence is None else presence.present})
        return rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = self._filters()
        page_obj, page_query = _paginate(self.request, self._presence_rows(filters, create_missing=False))
        context["filters"] = filters
        context["presence_rows"] = page_obj.object_list
        context["page_obj"] = page_obj
        context["page_query"] = page_query
        context["justifications_en_attente"] = (
            Justification.objects.filter(statut=Justification.STATUT_EN_ATTENTE)
            .select_related("presence__etudiant__utilisateur", "presence__matiere", "presence__creneau")
            .order_by("-created_at")
        )
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")

        if action == "save_presences":
            filters = self._filters()
            if not all((filters["filiere"], filters["matiere"], filters["date"], filters["creneau"])):
                messages.error(request, "Selectionnez une filiere, une matiere, une date et un creneau.")
                return redirect("administration:presences")

            present_ids = set(request.POST.getlist("present_etudiants"))
            for row in self._presence_rows(filters, create_missing=True):
                presence = row["presence"]
                presence.present = str(row["etudiant"].id) in present_ids
                presence.save(update_fields=["present", "updated_at"])

            messages.success(request, "Presences enregistrees avec succes.")
            return redirect(
                f"{request.path}?filiere={filters['filiere']}&matiere={filters['matiere']}&date={filters['date']}&creneau={filters['creneau']}"
            )

        if action in {"accept_justification", "refuse_justification"}:
            justification = get_object_or_404(Justification.objects.select_related("presence"), pk=request.POST.get("object_id"))
            if action == "accept_justification":
                justification.statut = Justification.STATUT_ACCEPTEE
                justification.presence.present = True
                justification.presence.save(update_fields=["present", "updated_at"])
                messages.success(request, "Justification acceptee.")
            else:
                justification.statut = Justification.STATUT_REFUSEE
                messages.success(request, "Justification refusee.")
            justification.save(update_fields=["statut", "updated_at"])
            return redirect("administration:presences")

        messages.error(request, "Action non reconnue.")
        return redirect("administration:presences")


class EmploisDuTempsView(AdminContextMixin, TemplateView):
    template_name = "administration/emplois_du_temps.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seances, filters = _seances_from_filters(self.request)
        seances_list = list(seances)
        week_start = timezone.datetime.strptime(filters["semaine"], "%Y-%m-%d").date()
        context["filters"] = filters
        context["selected_filiere_timetable"] = Filiere.objects.filter(pk=filters["filiere"]).first() if filters["filiere"] else None
        context["seance_form"] = SeanceForm()
        context["seances_filtrees"] = seances_list
        context["emploi_grid"] = _emploi_du_temps_grid(seances_list, week_start)
        context["previous_week"] = (week_start - timedelta(days=7)).isoformat()
        context["next_week"] = (week_start + timedelta(days=7)).isoformat()
        context["calendar_events"] = [
            {
                "id": seance.id,
                "title": f"{seance.matiere.nom} - {seance.professeur.nom_complet}",
                "start": f"{seance.date.isoformat()}T{seance.heure_debut.strftime('%H:%M:%S')}",
                "end": f"{seance.date.isoformat()}T{seance.heure_fin.strftime('%H:%M:%S')}",
                "extendedProps": {
                    "filiere": seance.filiere.nom,
                    "matiere": seance.matiere.nom,
                    "professeur": seance.professeur.nom_complet,
                    "salle": seance.salle,
                },
            }
            for seance in seances_list
        ]
        context["export_query"] = self.request.GET.urlencode()
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "create_seance":
            form = SeanceForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Seance creee avec succes.")
            else:
                messages.error(request, f"Erreur de validation: {form.errors.as_text()}")
            return redirect("administration:emplois_du_temps")

        if action == "update_seance":
            seance = get_object_or_404(Seance, pk=request.POST.get("object_id"))
            form = SeanceForm(request.POST, instance=seance)
            if form.is_valid():
                form.save()
                messages.success(request, "Seance mise a jour avec succes.")
            else:
                messages.error(request, f"Erreur de validation: {form.errors.as_text()}")
            return redirect("administration:emplois_du_temps")

        messages.error(request, "Action non reconnue.")
        return redirect("administration:emplois_du_temps")


class EmploisDuTempsExcelView(AdminContextMixin, View):
    def get(self, request, *args, **kwargs):
        seances, _ = _seances_from_filters(request)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Emploi du temps"
        headers = ["Date", "Debut", "Fin", "Filiere", "Matiere", "Professeur"]
        sheet.append(headers)
        for row in _format_seance_rows(seances):
            sheet.append(row)
        for column_cells in sheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            sheet.column_dimensions[column_cells[0].column_letter].width = max(max_length + 2, 12)

        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="emploi_du_temps.xlsx"'
        return response


class EmploisDuTempsPdfView(AdminContextMixin, View):
    def get(self, request, *args, **kwargs):
        seances, filters = _seances_from_filters(request)
        week_start = timezone.datetime.strptime(filters["semaine"], "%Y-%m-%d").date()
        grid = _emploi_du_temps_grid(list(seances), week_start)
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=landscape(A4), rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
        styles = getSampleStyleSheet()
        title = "FS MENUM - EMPLOI DU TEMPS"
        subtitle = f"Semaine du {grid['week_start'].strftime('%d/%m/%Y')} au {grid['week_end'].strftime('%d/%m/%Y')}"
        data = [["Heures"] + [f"{day['label']}\n{day['date'].strftime('%d/%m')}" for day in grid["days"]]]
        for row in grid["rows"]:
            cells = [row["slot"]]
            for items in row["cells"]:
                if items:
                    cells.append(
                        "\n\n".join(
                            f"{item.matiere.nom}\n{item.filiere.nom}\n{item.professeur.nom_complet}" for item in items
                        )
                    )
                elif row["kind"] == "pause":
                    cells.append(row["slot"])
                else:
                    cells.append("")
            data.append(cells)
        table = Table(data, repeatRows=1, colWidths=[2.3 * cm] + [4.05 * cm] * 6)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f7a4b")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#f2f8f4")),
                    ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#34453a")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.6),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ROWBACKGROUNDS", (1, 1), (-1, -1), [colors.white, colors.HexColor("#fbfbfc")]),
                ]
            )
        )
        doc.build([Paragraph(title, styles["Title"]), Paragraph(subtitle, styles["Heading3"]), Spacer(1, 12), table])
        output.seek(0)
        response = HttpResponse(output.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="emploi_du_temps.pdf"'
        return response


class EvenementsView(AdminContextMixin, TemplateView):
    template_name = "administration/evenements.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_obj, page_query = _paginate(self.request, Evenement.objects.order_by("date", "heure"))
        context["evenement_form"] = EvenementForm()
        context["evenements"] = page_obj.object_list
        context["page_obj"] = page_obj
        context["page_query"] = page_query
        context["evenement_types"] = Evenement.TYPE_CHOICES
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        object_id = request.POST.get("object_id")

        if action == "create_evenement":
            form = EvenementForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Evenement publie avec succes.")
            else:
                messages.error(request, f"Erreur de validation: {form.errors.as_text()}")
            return redirect("administration:evenements")

        if action == "update_evenement":
            evenement = get_object_or_404(Evenement, pk=object_id)
            form = EvenementForm(request.POST, instance=evenement)
            if form.is_valid():
                form.save()
                messages.success(request, "Evenement mis a jour.")
            else:
                messages.error(request, f"Erreur de validation: {form.errors.as_text()}")
            return redirect("administration:evenements")

        if action == "delete_evenement":
            get_object_or_404(Evenement, pk=object_id).delete()
            messages.success(request, "Evenement supprime.")
            return redirect("administration:evenements")

        if action == "cancel_evenement":
            evenement = get_object_or_404(Evenement, pk=object_id)
            evenement.annule = True
            evenement.save(update_fields=["annule", "updated_at"])
            messages.success(request, "Evenement annule.")
            return redirect("administration:evenements")

        messages.error(request, "Action non reconnue.")
        return redirect("administration:evenements")


class BibliothequeModerationView(AdminContextMixin, TemplateView):
    template_name = "administration/bibliotheque_moderation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tab = self.request.GET.get("tab") or "attente"
        try:
            context["active_tab"] = tab
            context["documents_moderation"] = _document_queryset_for_tab(tab)
            context["documents_counts"] = {
                "attente": _document_queryset_for_tab("attente").count(),
                "valides": _document_queryset_for_tab("valides").count(),
                "refuses": _document_queryset_for_tab("refuses").count(),
            }
        except (OperationalError, ProgrammingError):
            context["active_tab"] = tab
            context["documents_moderation"] = []
            context["documents_counts"] = {"attente": 0, "valides": 0, "refuses": 0}
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        document = get_object_or_404(Document, pk=request.POST.get("object_id"))

        if action == "validate_document":
            document.valide = True
            document.motif_refus = ""
            document.save(update_fields=["valide", "motif_refus", "updated_at"])
            messages.success(request, "Document valide et publie.")
            return redirect("administration:bibliotheque_moderation")

        if action == "refuse_document":
            motif = (request.POST.get("motif_refus") or "").strip()
            if not motif:
                messages.error(request, "Le motif de refus est obligatoire.")
                return redirect("administration:bibliotheque_moderation")
            document.valide = False
            document.motif_refus = motif
            document.save(update_fields=["valide", "motif_refus", "updated_at"])
            messages.success(request, "Document refuse.")
            return redirect("administration:bibliotheque_moderation")

        messages.error(request, "Action non reconnue.")
        return redirect("administration:bibliotheque_moderation")


class UtilisateursView(AdminContextMixin, TemplateView):
    template_name = "administration/utilisateurs.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            users_qs = User.objects.prefetch_related("groups").order_by("-last_login", "username")
            page_obj, page_query = _paginate(self.request, users_qs)
            users = list(page_obj.object_list)
            for user in users:
                user.role_admin = _user_role(user)
            context["utilisateurs"] = users
            context["page_obj"] = page_obj
            context["page_query"] = page_query
            context["user_form"] = UserRoleForm()
            context["roles_disponibles"] = UserRoleForm.ROLE_CHOICES
        except (OperationalError, ProgrammingError):
            context["utilisateurs"] = []
            context["roles_disponibles"] = UserRoleForm.ROLE_CHOICES
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "create_user":
            form = UserRoleForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Compte utilisateur cree avec succes.")
            else:
                messages.error(request, f"Erreur de validation: {form.errors.as_text()}")
            return redirect("administration:utilisateurs")

        if action == "toggle_user":
            user = get_object_or_404(User, pk=request.POST.get("object_id"))
            user.is_active = not user.is_active
            user.save(update_fields=["is_active"])
            messages.success(request, "Statut utilisateur mis a jour.")
            return redirect("administration:utilisateurs")

        if action == "update_user":
            user = get_object_or_404(User, pk=request.POST.get("object_id"))
            form = UserRoleForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, "Utilisateur modifie avec succes.")
            else:
                messages.error(request, f"Erreur de validation: {form.errors.as_text()}")
            return redirect("administration:utilisateurs")

        messages.error(request, "Action non reconnue.")
        return redirect("administration:utilisateurs")


class GlobalSearchView(AdminContextMixin, View):
    def get(self, request, *args, **kwargs):
        q = (request.GET.get("q") or "").strip()
        if not q:
            return redirect("administration:dashboard")

        etudiant = (
            EtudiantProfile.objects.select_related("utilisateur")
            .filter(
                Q(matricule__icontains=q)
                | Q(utilisateur__first_name__icontains=q)
                | Q(utilisateur__last_name__icontains=q)
                | Q(utilisateur__email__icontains=q)
            )
            .order_by("matricule")
            .first()
        )
        if etudiant:
            return redirect("administration:etudiant_detail", etudiant_id=etudiant.id)

        messages.info(request, "Aucun etudiant ne correspond a cette recherche.")
        return redirect(f"{reverse('administration:etudiants_liste')}?q={q}")


class ParametresView(AdminContextMixin, TemplateView):
    template_name = "administration/parametres.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "filiere_form": FiliereForm(),
                "licence_form": LicenceForm(),
                "matiere_form": MatiereForm(),
                "annee_form": AnneeAcademiqueForm(),
                "professeur_form": ProfesseurForm(),
                "creneau_form": CreneauAbsenceForm(),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        object_id = request.POST.get("object_id")

        forms_config = {
            "create_filiere": (FiliereForm, Filiere, None),
            "update_filiere": (FiliereForm, Filiere, object_id),
            "create_licence": (LicenceForm, Licence, None),
            "update_licence": (LicenceForm, Licence, object_id),
            "create_matiere": (MatiereForm, Matiere, None),
            "update_matiere": (MatiereForm, Matiere, object_id),
            "create_annee": (AnneeAcademiqueForm, AnneeAcademique, None),
            "update_annee": (AnneeAcademiqueForm, AnneeAcademique, object_id),
            "create_professeur": (ProfesseurForm, Professeur, None),
            "update_professeur": (ProfesseurForm, Professeur, object_id),
            "create_creneau": (CreneauAbsenceForm, CreneauAbsence, None),
            "update_creneau": (CreneauAbsenceForm, CreneauAbsence, object_id),
        }

        delete_config = {
            "delete_filiere": Filiere,
            "delete_licence": Licence,
            "delete_matiere": Matiere,
            "delete_annee": AnneeAcademique,
            "delete_professeur": Professeur,
            "delete_creneau": CreneauAbsence,
        }

        if action in forms_config:
            form_class, model, pk = forms_config[action]
            instance = get_object_or_404(model, pk=pk) if pk else None
            form = form_class(request.POST, instance=instance)
            if form.is_valid():
                obj = form.save()
                if model is AnneeAcademique and obj.active:
                    AnneeAcademique.objects.exclude(pk=obj.pk).update(active=False)
                messages.success(request, "Enregistrement effectue avec succes.")
            else:
                messages.error(request, f"Erreur de validation: {form.errors.as_text()}")
            return redirect("administration:parametres")

        if action in delete_config:
            model = delete_config[action]
            obj = get_object_or_404(model, pk=object_id)
            try:
                obj.delete()
                messages.success(request, "Suppression effectuee avec succes.")
            except ProtectedError:
                messages.error(request, "Suppression impossible: cet element est utilise ailleurs.")
            return redirect("administration:parametres")

        messages.error(request, "Action non reconnue.")
        return redirect("administration:parametres")


class ParametresTarifsView(AdminContextMixin, TemplateView):
    template_name = "administration/parametres_tarifs.html"


class ParametresPaiementsView(AdminContextMixin, TemplateView):
    template_name = "administration/parametres_paiements.html"


class BulletinPdfByMatriculeView(AdminContextMixin, View):
    def get(self, request, *args, **kwargs):
        matricule = (request.GET.get("matricule") or "").strip()
        if not matricule:
            return HttpResponse("Matricule manquant.", status=400, content_type="text/plain; charset=utf-8")

        etudiant = (
            EtudiantProfile.objects.select_related("utilisateur", "filiere", "licence", "semestre")
            .filter(matricule__iexact=matricule)
            .first()
        )
        if not etudiant:
            return HttpResponse("Aucun etudiant trouve avec ce matricule.", status=404, content_type="text/plain; charset=utf-8")

        bulletin = (
            Bulletin.objects.filter(etudiant=etudiant)
            .select_related("annee_academique", "semestre", "etudiant__filiere", "etudiant__licence")
            .prefetch_related("notes__matiere", "notes__professeur")
            .order_by("-annee_academique__libelle", "-semestre__ordre", "-updated_at")
            .first()
        )
        if not bulletin:
            return HttpResponse(
                "Aucun bulletin disponible pour cet etudiant.",
                status=404,
                content_type="text/plain; charset=utf-8",
            )

        rang, total_classement = _compute_rank_for_bulletin(bulletin)
        pdf_bytes = render_bulletin_pdf_bytes(bulletin, rang, total_classement)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="bulletin_{etudiant.matricule}.pdf"'
        return response

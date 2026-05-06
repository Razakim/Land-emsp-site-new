from io import BytesIO
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _fmt_decimal(value):
    if value is None:
        return "-"
    return f"{value:.2f}"


def _mention_note(note):
    try:
        valeur = float(note)
    except Exception:
        return "-"
    if valeur >= 16:
        return "Tres bien"
    if valeur >= 14:
        return "Bien"
    if valeur >= 12:
        return "Assez bien"
    if valeur >= 10:
        return "Passable"
    return "Insuffisant"


def render_bulletin_pdf_bytes(bulletin, rang, total_classement):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.4 * cm,
        rightMargin=1.4 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    title = styles["Title"]
    title.fontSize = 16
    title.leading = 20

    story = []
    story.append(Paragraph("Ecole de Management et des Sciences Professionnelles (EMSP)", styles["Heading2"]))
    story.append(Paragraph("Bulletin de notes", title))
    story.append(Spacer(1, 0.35 * cm))

    etudiant = bulletin.etudiant
    photo_flowable = ""
    if etudiant.photo:
        try:
            photo_path = Path(etudiant.photo.path)
            if photo_path.exists():
                photo_flowable = Image(str(photo_path), width=2.6 * cm, height=2.6 * cm)
        except Exception:
            photo_flowable = ""

    info_data = [
        ["Photo", photo_flowable, "Matricule", etudiant.matricule],
        ["Nom", etudiant.nom_complet, "Filiere", etudiant.filiere.nom if etudiant.filiere else "-"],
        ["Niveau", etudiant.licence.code if etudiant.licence else "-", "Semestre / Annee", f"{bulletin.semestre.code} - {bulletin.annee_academique.libelle}"],
    ]
    info_table = Table(info_data, colWidths=[3.0 * cm, 6.2 * cm, 3.0 * cm, 6.2 * cm], rowHeights=[2.9 * cm, None, None])
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f2f8f4")),
                ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f2f8f4")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#4a6655")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 0.45 * cm))

    notes_data = [["Matiere", "Coeff", "CC", "Examen", "Finale", "Mention"]]
    for note in bulletin.notes.select_related("matiere").all():
        notes_data.append(
            [
                note.matiere.nom,
                str(note.coefficient),
                _fmt_decimal(note.note_cc),
                _fmt_decimal(note.note_examen),
                _fmt_decimal(note.note_finale),
                _mention_note(note.note_finale),
            ]
        )

    if len(notes_data) == 1:
        notes_data.append(["Aucune note disponible", "-", "-", "-", "-", "-"])

    notes_table = Table(notes_data, colWidths=[7.1 * cm, 1.6 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm, 2.5 * cm])
    notes_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f7a4b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#4a6655")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fcf9")]),
            ]
        )
    )
    story.append(notes_table)
    story.append(Spacer(1, 0.45 * cm))

    rang_label = f"{rang}/{total_classement}" if rang is not None and total_classement > 0 else "-"
    synthese_data = [
        ["Moyenne generale", _fmt_decimal(bulletin.moyenne)],
        ["Decision", bulletin.get_decision_display()],
        ["Rang", rang_label],
        ["Appreciation", bulletin.appreciation or "-"],
    ]
    synthese_table = Table(synthese_data, colWidths=[4.8 * cm, 12.0 * cm])
    synthese_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f2f8f4")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#4a6655")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(synthese_table)
    story.append(Spacer(1, 0.35 * cm))
    story.append(Paragraph(f"Document genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}", normal))

    doc.build(story)
    pdf_value = buffer.getvalue()
    buffer.close()
    return pdf_value

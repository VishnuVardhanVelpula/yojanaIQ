"""
Generate data/schemes.pdf — one page per AP Government scheme.
Run from inside ap_scheme_rag/ folder:
    python create_schemes_pdf.py
"""

import json
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable
)

# ── Load schemes ─────────────────────────────────────────────────────────────
base_dir = os.path.dirname(os.path.abspath(__file__))
schemes_path = os.path.join(base_dir, "data", "schemes.json")
output_path  = os.path.join(base_dir, "data", "schemes.pdf")

with open(schemes_path, "r", encoding="utf-8") as f:
    schemes = json.load(f)

# ── Styles ────────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

INDIGO  = colors.HexColor("#3730a3")
TEAL    = colors.HexColor("#0d9488")
SLATE   = colors.HexColor("#334155")
LIGHT   = colors.HexColor("#f1f5f9")
WHITE   = colors.white

title_style = ParagraphStyle(
    "SchemeTitle",
    parent=styles["Title"],
    fontSize=18,
    textColor=WHITE,
    spaceAfter=4,
    fontName="Helvetica-Bold",
)
category_style = ParagraphStyle(
    "Category",
    parent=styles["Normal"],
    fontSize=10,
    textColor=colors.HexColor("#a5f3fc"),
    spaceAfter=0,
    fontName="Helvetica",
)
label_style = ParagraphStyle(
    "Label",
    parent=styles["Normal"],
    fontSize=9,
    textColor=TEAL,
    fontName="Helvetica-Bold",
    spaceBefore=6,
    spaceAfter=2,
)
value_style = ParagraphStyle(
    "Value",
    parent=styles["Normal"],
    fontSize=10,
    textColor=SLATE,
    fontName="Helvetica",
    spaceAfter=2,
    leading=14,
)
benefit_style = ParagraphStyle(
    "Benefit",
    parent=styles["Normal"],
    fontSize=11,
    textColor=colors.HexColor("#1e293b"),
    fontName="Helvetica-Bold",
    spaceAfter=4,
    leading=15,
)
id_style = ParagraphStyle(
    "SchemeID",
    parent=styles["Normal"],
    fontSize=8,
    textColor=colors.HexColor("#94a3b8"),
    fontName="Helvetica",
    spaceAfter=0,
)

def fmt_list(lst):
    """Join a list nicely; 'any' becomes 'All'."""
    if not lst:
        return "All"
    if "any" in [x.lower() for x in lst]:
        return "All"
    return ", ".join(lst)

def income_str(val):
    if val >= 10_00_000:
        return f"Rs.{val/1_00_000:.1f}L"
    return f"Rs.{val:,}"

# ── Build PDF ─────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    output_path,
    pagesize=A4,
    leftMargin=15*mm,
    rightMargin=15*mm,
    topMargin=12*mm,
    bottomMargin=12*mm,
)

story = []
W = A4[0] - 30*mm   # usable width

for idx, s in enumerate(schemes):
    # ── Header banner ────────────────────────────────────────────────────────
    header_data = [[
        Paragraph(s["name"], title_style),
        Paragraph(s["category"], category_style),
    ]]
    header_table = Table(header_data, colWidths=[W * 0.65, W * 0.35])
    header_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), INDIGO),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",(0, 0), (-1, -1), 10),
        ("TOPPADDING",  (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0,0), (-1, -1), 10),
        ("ALIGN",       (1, 0), (1, 0),  "RIGHT"),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [INDIGO]),
    ]))
    story.append(header_table)
    story.append(Paragraph(f"Scheme ID: {s['id']}", id_style))
    story.append(Spacer(1, 6))

    # ── Benefit highlight box ─────────────────────────────────────────────────
    benefit_data = [[Paragraph(f"Benefit: {s['benefits']}", benefit_style)]]
    benefit_table = Table(benefit_data, colWidths=[W])
    benefit_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), LIGHT),
        ("LEFTPADDING",  (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING",   (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0), (-1,-1), 8),
        ("BOX",          (0,0), (-1,-1), 1, TEAL),
    ]))
    story.append(benefit_table)
    story.append(Spacer(1, 8))

    # ── Eligibility grid ─────────────────────────────────────────────────────
    def cell(label, value):
        return [Paragraph(label, label_style), Paragraph(str(value), value_style)]

    age_range = f"{s['min_age']} – {s['max_age']} years"
    elig_rows = [
        cell("Age Range",           age_range),
        cell("Max Annual Income",   income_str(s["max_income"])),
        cell("Gender",              fmt_list(s["eligible_gender"])),
        cell("Caste",               fmt_list(s["eligible_caste"])),
        cell("Religion",            fmt_list(s["eligible_religion"])),
        cell("Occupation",          fmt_list(s["eligible_occupation"])),
        cell("Special Eligibility", fmt_list(s["eligible_for"])),
    ]

    # Two-column layout
    left_rows  = elig_rows[:4]
    right_rows = elig_rows[4:]

    def make_col(rows):
        data = []
        for lbl, val in rows:
            data.append([lbl])
            data.append([val])
        return data

    # Flatten into a two-column table
    max_r = max(len(left_rows), len(right_rows))
    grid_data = []
    for i in range(max_r):
        lbl_l = left_rows[i][0]  if i < len(left_rows)  else Paragraph("", label_style)
        val_l = left_rows[i][1]  if i < len(left_rows)  else Paragraph("", value_style)
        lbl_r = right_rows[i][0] if i < len(right_rows) else Paragraph("", label_style)
        val_r = right_rows[i][1] if i < len(right_rows) else Paragraph("", value_style)
        grid_data.append([lbl_l, lbl_r])
        grid_data.append([val_l, val_r])

    half = W / 2 - 3*mm
    elig_table = Table(grid_data, colWidths=[half, half], hAlign="LEFT")
    elig_table.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 1),
    ]))
    story.append(Paragraph("Eligibility Criteria", ParagraphStyle(
        "EligHeader", parent=styles["Heading2"],
        fontSize=11, textColor=INDIGO, spaceBefore=4, spaceAfter=4,
        fontName="Helvetica-Bold"
    )))
    story.append(elig_table)
    story.append(Spacer(1, 8))

    # ── Documents required ────────────────────────────────────────────────────
    story.append(Paragraph("Documents Required", ParagraphStyle(
        "DocHeader", parent=styles["Heading2"],
        fontSize=11, textColor=INDIGO, spaceBefore=4, spaceAfter=4,
        fontName="Helvetica-Bold"
    )))
    docs_text = " • ".join(s.get("documents", []))
    story.append(Paragraph(docs_text or "—", value_style))
    story.append(Spacer(1, 8))

    # ── Application Steps ─────────────────────────────────────────────────────
    if "application_steps" in s and s["application_steps"]:
        story.append(Paragraph("Application Steps", ParagraphStyle(
            "StepHeader", parent=styles["Heading2"],
            fontSize=11, textColor=INDIGO, spaceBefore=4, spaceAfter=4,
            fontName="Helvetica-Bold"
        )))
        for step in s["application_steps"]:
            story.append(Paragraph(step, value_style))
        story.append(Spacer(1, 8))

    # ── Quick Info ─────────────────────────────────────────────────────────────
    def add_meta(label, val):
        if val and val != "N/A":
            story.append(Paragraph(f"<b>{label}:</b> {val}", value_style))

    story.append(Paragraph("Additional Information", ParagraphStyle(
        "AddInfoHeader", parent=styles["Heading2"],
        fontSize=11, textColor=INDIGO, spaceBefore=4, spaceAfter=4,
        fontName="Helvetica-Bold"
    )))
    
    add_meta("How to Apply", s.get("apply_at"))
    add_meta("Apply Portal", s.get("apply_portal"))
    add_meta("Status Check Portal", s.get("status_check_portal"))
    add_meta("Offline Office", s.get("offline_office"))
    add_meta("Processing Time", s.get("processing_time"))
    add_meta("Helpline", s.get("helpline"))
    if "exclusions" in s and s["exclusions"]:
        add_meta("Exclusions", s["exclusions"])

    # ── Page break between schemes ────────────────────────────────────────────
    if idx < len(schemes) - 1:
        story.append(PageBreak())

doc.build(story)
print(f"✅ PDF created: {output_path}")
print(f"   Schemes included: {len(schemes)}")
print(f"   Pages: {len(schemes)} (one per scheme)")
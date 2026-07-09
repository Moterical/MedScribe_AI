import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from datetime import datetime

# Directory to save PDF artifacts
PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)

def create_clinical_brief_pdf(hcp_name: str, topics: str, content: str, samples: list = None, materials: list = None) -> str:
    """
    Generates a beautifully styled, custom Clinical Brief PDF based on discussion topics.
    Returns the relative URL/filename of the PDF.
    """
    # Create filename unique to this HCP and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_hcp = "".join(x for x in hcp_name if x.isalnum()).replace(" ", "_")
    filename = f"Clinical_Brief_{clean_hcp}_{timestamp}.pdf"
    filepath = os.path.join(PDF_DIR, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    PRIMARY_COLOR = colors.HexColor("#3b82f6")  # Indigo/Blue accent
    TEXT_COLOR = colors.HexColor("#1e293b")     # Slate Dark
    LIGHT_BG = colors.HexColor("#f8fafc")       # Slate light
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY_COLOR,
        spaceAfter=15
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=PRIMARY_COLOR,
        spaceBefore=15,
        spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=TEXT_COLOR,
        spaceAfter=8
    )

    bold_body_style = ParagraphStyle(
        'BoldBody',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    story = []

    # Title & Header Banner
    story.append(Paragraph("CLINICAL TRIAL BRIEFING", title_style))
    story.append(Paragraph(f"<b>Prepared for:</b> {hcp_name}", body_style))
    story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}", body_style))
    story.append(Paragraph(f"<b>Core Discussion Subject:</b> {topics or 'General Discussion'}", body_style))
    story.append(Spacer(1, 15))

    # Divider bar
    divider = Table([[""]], colWidths=[530], rowHeights=[2])
    divider.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), PRIMARY_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(divider)
    story.append(Spacer(1, 15))

    # Section 1: Executive Summary / Custom Clinical Insights
    story.append(Paragraph("1. Custom Clinical Insights & Discussion Summary", section_style))
    story.append(Paragraph(content or "This document serves as a personalized clinical summary corresponding to recent interactions regarding safety profiles, therapeutic updates, and efficacy briefs. Details on prescription guides, clinical study outcomes, and medical efficacy were discussed during the session.", body_style))
    story.append(Spacer(1, 10))

    # Section 2: Materials & Literature Shared
    story.append(Paragraph("2. Shared Study Materials", section_style))
    if materials:
        for mat in materials:
            story.append(Paragraph(f"• {mat}", body_style))
    else:
        story.append(Paragraph("• Product brochures & clinical study review folders.", body_style))
    story.append(Spacer(1, 10))

    # Section 3: Allocated Product Samples
    story.append(Paragraph("3. Distributed Product Starter Packages", section_style))
    if samples:
        sample_data = [["Sample Name", "Distributed Quantity"]]
        for sample in samples:
            # check if dict or object
            if isinstance(sample, dict):
                sample_data.append([sample.get("sample_name", ""), str(sample.get("quantity", 0))])
            else:
                sample_data.append([getattr(sample, "sample_name", ""), str(getattr(sample, "quantity", 0))])
        
        sample_table = Table(sample_data, colWidths=[250, 150])
        sample_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,-1), LIGHT_BG),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('PADDING', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ]))
        story.append(sample_table)
    else:
        story.append(Paragraph("No physical chemical drug starters or samples distributed during this session.", body_style))
    
    story.append(Spacer(1, 20))

    # Footer Notice
    story.append(Paragraph("<i>Disclaimer: The information contained in this brief is confidential and intended solely for medical education and clinical support discussions between field representatives and certified Healthcare Professionals.</i>", ParagraphStyle('Foot', parent=body_style, fontSize=8, leading=10, textColor=colors.gray)))

    doc.build(story)
    return filename

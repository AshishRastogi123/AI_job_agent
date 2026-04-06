import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from typing import Optional

def save_pdf(content: str, filename: str, title: Optional[str] = None) -> str:
    """
    Save text content as PDF in the resumes folder.

    Args:
        content: The text content to save as PDF
        filename: The filename for the PDF (without .pdf extension)
        title: Optional title for the PDF document

    Returns:
        The full path to the saved PDF file
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    resume_dir = os.path.join(base_dir, "resumes")

    # Create folder if not exists
    os.makedirs(resume_dir, exist_ok=True)

    file_path = os.path.join(resume_dir, f"{filename}.pdf")

    # Create PDF
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    if title:
        story.append(Paragraph(title, styles['Title']))
        story.append(Spacer(1, 12))

    # Split content into paragraphs
    paragraphs = content.split('\n\n')
    for para in paragraphs:
        if para.strip():
            story.append(Paragraph(para.replace('\n', '<br/>'), styles['Normal']))
            story.append(Spacer(1, 6))

    doc.build(story)

    print(f"PDF saved successfully at: {file_path}")
    return file_path


def save_text_pdf(content: str, prefix: str, job_id=None, title: Optional[str] = None) -> str:
    """Save text content as a timestamped PDF in the resumes folder."""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    job_id_label = job_id if job_id is not None else 'unknown'
    filename = f"{prefix}_{job_id_label}_{timestamp}"
    return save_pdf(content, filename, title)

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from sys import argv

def create_flattened_pdf_from_text(text, output_file):
    doc = SimpleDocTemplate(output_file, pagesize=letter)
    styles = getSampleStyleSheet()

    # Create a list of flowables (elements) to add to the PDF
    elements = []

    # Convert the text into a Paragraph element with a specified style
    text_style = styles["Normal"]
    text_style.fontName = 'Times-Roman'

    paragraph = Paragraph(text, text_style)
    elements.append(paragraph)
    elements.append(Spacer(1, 12))

    # Build the PDF document
    doc.build(elements)

if __name__ == "__main__":
    text = argv[1]
    output_file = "output.pdf"
    
    create_flattened_pdf_from_text(text, output_file)
    print(f"Flattened PDF saved as '{output_file}'")

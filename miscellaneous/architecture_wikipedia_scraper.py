import pdf_prep
import pdf_create
from os import getcwd


def create(url):
    paragraphs = pdf_prep.extract_entry_paragraphs(url)

    text = ''.join(paragraphs)

    parts = url.split("/")
    architecture_name = parts[-1]

    output_file = './pdfs/' + architecture_name + '.pdf'
    pdf_create.create_flattened_pdf_from_text(text, output_file)


if __name__ == "__main__":
    # get the urls
    _path = getcwd() + "/pages.txt"
    urls = []
    with open(_path, "r") as pages:
        for page_url in pages.readlines():
            urls.append(page_url.strip('\n'))

    for url in urls:
        create(url)
        print(f"PDF created from {url}")


    
import requests
from bs4 import BeautifulSoup

def extract_entry_paragraphs(url: str) -> str:
    paragraphs = []

    # Send an HTTP GET request to the URL
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        #print("REQUEST SUCCESS")
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')
        #print(soup.text)

        text_block = soup.find('div', class_="mw-parser-output")
        h2 = text_block.find('h2')

        # Extract all <p> tags before the first <h2> tag
        if h2:
            preceding_p_tags = []
            for tag in h2.find_all_previous():
                if tag.name == 'p':
                    preceding_p_tags.insert(0, tag)

            # Now, you can process or print the <p> tags
            for ind, p_tag in enumerate(preceding_p_tags):
                if ind > 1:
                    break
                paragraphs.append(p_tag.text)
                

    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
    
    return paragraphs

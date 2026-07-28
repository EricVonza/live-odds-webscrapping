import requests
from bs4 import BeautifulSoup

URL = "https://1xbet.global/en/live/basketball"

HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}

def fetch_html(url):
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.content

def extract_html_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract the same elements you were targeting
    matches = soup.find_all(class_='betting-main-dashboard')
    
    return matches

def main():
    html_content = fetch_html(URL)
    extracted_elements = extract_html_content(html_content)

    # Display raw HTML of extracted elements
    for idx, element in enumerate(extracted_elements, start=1):
        print(f"\n--- Element {idx} ---")
        print(element.prettify())  # Clean formatted HTML output

if __name__ == "__main__":
    main()
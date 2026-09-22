import hashlib
import re
from bs4 import BeautifulSoup
from typing import Dict, Any

def clean_html_and_extract_metadata(raw_html: str, url: str) -> Dict[str, Any]:
    """
    Cleans raw HTML text, strips boilerplate/navigation/script tags,
    extracts main text content, page title, metadata, and generates a SHA256 content hash.
    """
    if not raw_html:
        return {
            'title': '',
            'cleaned_text': '',
            'metadata': {},
            'content_hash': ''
        }

    soup = BeautifulSoup(raw_html, 'html.parser')

    # Extract title before removing elements
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.find('h1'):
        title = soup.find('h1').get_text(strip=True)

    # Extract metadata tags
    metadata = {
        'url': url,
        'title': title,
        'description': '',
        'keywords': '',
        'og_title': '',
        'language': soup.html.get('lang', 'en') if soup.html else 'en'
    }

    desc_meta = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
    if desc_meta and desc_meta.get('content'):
        metadata['description'] = desc_meta['content'].strip()

    og_title_meta = soup.find('meta', attrs={'property': 'og:title'})
    if og_title_meta and og_title_meta.get('content'):
        metadata['og_title'] = og_title_meta['content'].strip()

    # Decompose unwanted elements
    for element in soup([
        'script', 'style', 'noscript', 'svg', 'iframe', 'canvas', 
        'nav', 'footer', 'header', 'form', 'aside'
    ]):
        element.decompose()

    # Extract structured text with space separation
    raw_text = soup.get_text(separator=' ', strip=True)

    # Clean whitespace and repetitive newlines/spaces
    cleaned_text = re.sub(r'\s+', ' ', raw_text).strip()

    # Compute SHA256 content hash
    content_hash = hashlib.sha256(cleaned_text.encode('utf-8')).hexdigest()

    metadata['content_length'] = len(cleaned_text)

    return {
        'title': title or url,
        'cleaned_text': cleaned_text,
        'metadata': metadata,
        'content_hash': content_hash
    }

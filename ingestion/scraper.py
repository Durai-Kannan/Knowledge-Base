import requests

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def scrape_url(url: str, timeout: int = 15) -> dict:
    """
    Performs HTTP GET request to harvest HTML content and HTTP status code.
    Returns dict with keys: 'status_code', 'raw_html', 'error'.
    """
    try:
        response = requests.get(
            url,
            headers=DEFAULT_HEADERS,
            timeout=timeout,
            allow_redirects=True,
            verify=False  # Avoid failing on minor self-signed/expired SSL issues for public URLs
        )
        return {
            'status_code': response.status_code,
            'raw_html': response.text if response.status_code == 200 else "",
            'error': f"HTTP {response.status_code}" if response.status_code != 200 else ""
        }
    except requests.exceptions.Timeout:
        return {'status_code': 408, 'raw_html': "", 'error': "Request timed out after 15 seconds."}
    except requests.exceptions.SSLError as e:
        return {'status_code': 495, 'raw_html': "", 'error': f"SSL Verification error: {str(e)}"}
    except requests.exceptions.ConnectionError:
        return {'status_code': 503, 'raw_html': "", 'error': "Connection failed or DNS unresolvable."}
    except Exception as e:
        return {'status_code': 500, 'raw_html': "", 'error': f"Scraping error: {str(e)}"}

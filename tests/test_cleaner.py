import pytest
from ingestion.cleaner import clean_html_and_extract_metadata

def test_clean_html_and_extract_metadata():
    raw_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Test Executive Bio</title>
        <meta name="description" content="Official bio for Jane Doe.">
    </head>
    <body>
        <nav>Navigation links</nav>
        <main>
            <h1>Jane Doe - Chief Technology Officer</h1>
            <p>Jane Doe leads technology and innovation strategy across global engineering teams.</p>
        </main>
        <footer>Footer information</footer>
    </body>
    </html>
    """
    url = "https://example.com/executives/jane-doe"
    result = clean_html_and_extract_metadata(raw_html, url)

    assert result['title'] == "Test Executive Bio"
    assert "Jane Doe leads technology" in result['cleaned_text']
    assert "Navigation links" not in result['cleaned_text']
    assert "Footer information" not in result['cleaned_text']
    assert result['metadata']['description'] == "Official bio for Jane Doe."
    assert len(result['content_hash']) == 64

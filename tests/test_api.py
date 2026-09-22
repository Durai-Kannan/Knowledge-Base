import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from knowledge_base.models import URLDocument, DocumentChunk

@pytest.mark.django_db
def test_url_document_list_api():
    client = APIClient()
    URLDocument.objects.create(
        url="https://example.com/test",
        title="Test Page",
        status="success",
        http_status=200,
        cleaned_text="Test page text content."
    )

    url = reverse('api_url_list')
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert 'results' in data or isinstance(data, list)
    results = data.get('results', data)
    assert len(results) >= 1
    assert results[0]['url'] == "https://example.com/test"

@pytest.mark.django_db
def test_search_api_no_context():
    client = APIClient()
    url = reverse('api_search')
    response = client.post(url, {'query': 'Nonexistent query details'}, format='json')
    assert response.status_code == 200
    data = response.json()
    assert 'answer' in data
    assert 'sources' in data
    assert isinstance(data['sources'], list)

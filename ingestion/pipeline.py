import traceback
from django.db import transaction
from knowledge_base.models import URLDocument, DocumentChunk
from .url_validator import is_valid_url, is_ssrf_safe
from .scraper import scrape_url
from .cleaner import clean_html_and_extract_metadata
from .chunker import chunk_text
from .file_processor import extract_urls_from_file
from vector_store.faiss_store import get_vector_store

def ingest_single_url(url: str, force_rescrape: bool = False) -> URLDocument:
    """
    Ingests a single URL end-to-end:
    validate -> scrape -> clean -> chunk -> SQLite -> FAISS.
    """
    url = url.strip()
    
    # 1. Validation & SSRF check
    if not is_valid_url(url):
        doc, _ = URLDocument.objects.get_or_create(url=url)
        doc.status = 'failed'
        doc.error_message = "Invalid URL structure."
        doc.save()
        return doc

    if not is_ssrf_safe(url):
        doc, _ = URLDocument.objects.get_or_create(url=url)
        doc.status = 'failed'
        doc.error_message = "SSRF Protection: URL resolves to private or loopback IP."
        doc.save()
        return doc

    doc, created = URLDocument.objects.get_or_create(url=url)

    # Avoid duplicate re-scraping unless forced or previously failed
    if not created and doc.status == 'success' and not force_rescrape:
        return doc

    doc.status = 'processing'
    doc.error_message = ""
    doc.save()

    # 2. Web Scraping
    scrape_result = scrape_url(url)
    doc.http_status = scrape_result['status_code']
    
    if scrape_result['status_code'] != 200 or not scrape_result['raw_html']:
        doc.status = 'failed'
        doc.error_message = scrape_result.get('error', f"HTTP {scrape_result['status_code']}")
        doc.save()
        return doc

    doc.raw_html = scrape_result['raw_html']

    # 3. HTML Cleaning & Metadata Extraction
    cleaned_info = clean_html_and_extract_metadata(doc.raw_html, url)
    doc.title = cleaned_info['title']
    doc.cleaned_text = cleaned_info['cleaned_text']
    doc.metadata = cleaned_info['metadata']
    doc.content_hash = cleaned_info['content_hash']

    if not doc.cleaned_text:
        doc.status = 'failed'
        doc.error_message = "Scraped web page contained no extractable text content."
        doc.save()
        return doc

    try:
        with transaction.atomic():
            # Clear old chunks if re-scraping
            doc.chunks.all().delete()

            # 4. Text Chunking
            chunks_text = chunk_text(doc.cleaned_text, chunk_size=700, chunk_overlap=100)
            
            created_chunk_objs = []
            chunk_data_for_faiss = []

            for idx, c_text in enumerate(chunks_text):
                chunk_obj = DocumentChunk.objects.create(
                    document=doc,
                    chunk_index=idx,
                    content=c_text,
                    metadata={'url': doc.url, 'title': doc.title}
                )
                created_chunk_objs.append(chunk_obj)
                chunk_data_for_faiss.append({
                    'chunk_id': chunk_obj.id,
                    'document_id': doc.id,
                    'url': doc.url,
                    'title': doc.title,
                    'chunk_index': idx,
                    'content': c_text
                })

            # 5. Vector Store Indexing
            vstore = get_vector_store()
            assigned_faiss_ids = vstore.add_chunks(chunk_data_for_faiss)

            for chunk_obj, faiss_id in zip(created_chunk_objs, assigned_faiss_ids):
                chunk_obj.embedding_id = faiss_id
                chunk_obj.save()

            doc.status = 'success'
            doc.error_message = ""
            doc.save()

    except Exception as e:
        doc.status = 'failed'
        doc.error_message = f"Chunking/Vector store error: {str(e)}"
        doc.save()
        print(f"[IngestionPipeline] Error processing {url}: {traceback.format_exc()}")

    return doc


def process_uploaded_file(file_path_or_buffer, filename: str) -> dict:
    """
    Processes an uploaded CSV or Excel file, extracting all URLs and ingesting them.
    """
    valid_urls, invalid_errors = extract_urls_from_file(file_path_or_buffer, filename=filename)

    results = {
        'total_discovered': len(valid_urls) + len(invalid_errors),
        'valid_urls_count': len(valid_urls),
        'success_count': 0,
        'failed_count': len(invalid_errors),
        'invalid_errors': invalid_errors,
        'processed_docs': []
    }

    for url in valid_urls:
        doc = ingest_single_url(url)
        results['processed_docs'].append({
            'id': doc.id,
            'url': doc.url,
            'title': doc.title,
            'status': doc.status,
            'http_status': doc.http_status,
            'error_message': doc.error_message
        })
        if doc.status == 'success':
            results['success_count'] += 1
        else:
            results['failed_count'] += 1

    return results

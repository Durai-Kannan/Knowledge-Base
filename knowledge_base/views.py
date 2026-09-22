from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import URLDocument, DocumentChunk
from .serializers import URLDocumentSerializer, URLDocumentDetailSerializer
from .forms import UploadFileForm, SingleURLForm
from ingestion.pipeline import process_uploaded_file, ingest_single_url
from vector_store.faiss_store import get_vector_store
from vector_store.search import perform_vector_search
from llm.gemini_client import generate_rag_answer


# ==========================================
# 1. REST API Views
# ==========================================

class URLDocumentListAPIView(generics.ListAPIView):
    """
    GET /api/urls/
    Lists all harvested URL documents with HTTP status, title, metadata, and status.
    """
    queryset = URLDocument.objects.all()
    serializer_class = URLDocumentSerializer
    filterset_fields = ['status', 'http_status']
    search_fields = ['url', 'title', 'cleaned_text']


class URLDocumentDetailAPIView(generics.RetrieveDestroyAPIView):
    """
    GET /api/urls/<id>/ or DELETE /api/urls/<id>/
    Retrieves or deletes a specific URL document and its chunks.
    """
    queryset = URLDocument.objects.all()
    serializer_class = URLDocumentDetailSerializer
    lookup_field = 'id'

    def perform_destroy(self, instance):
        instance.chunks.all().delete()
        instance.delete()


class SearchAPIView(APIView):
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response(
                {"error": "Query parameter 'q' is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        top_k = int(request.query_params.get('top_k', 5))
        
        # Perform vector similarity search
        retrieved_chunks = perform_vector_search(query, top_k=top_k)
        
        # Generate RAG answer using Gemini API
        llm_response = generate_rag_answer(query, retrieved_chunks)

        return Response({
            'query': query,
            'answer': llm_response['answer'],
            'model': llm_response['model'],
            'sources': llm_response['sources'],
            'retrieved_chunks_count': len(retrieved_chunks),
            'retrieved_chunks': retrieved_chunks
        })


class FileUploadAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        if 'file' not in request.FILES:
            return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES['file']
        results = process_uploaded_file(uploaded_file, uploaded_file.name)

        return Response(results, status=status.HTTP_201_CREATED)


# ==========================================
# 2. Web UI Views
# ==========================================

def dashboard_view(request):
    """Main Dashboard View"""
    vstore = get_vector_store()
    
    total_docs = URLDocument.objects.count()
    success_docs = URLDocument.objects.filter(status='success').count()
    failed_docs = URLDocument.objects.filter(status='failed').count()
    pending_docs = URLDocument.objects.filter(status__in=['pending', 'processing']).count()
    total_chunks = DocumentChunk.objects.count()
    vector_count = vstore.index.ntotal if vstore.index else 0

    recent_docs = URLDocument.objects.all()[:5]

    context = {
        'total_docs': total_docs,
        'success_docs': success_docs,
        'failed_docs': failed_docs,
        'pending_docs': pending_docs,
        'total_chunks': total_chunks,
        'vector_count': vector_count,
        'recent_docs': recent_docs,
    }
    return render(request, 'dashboard.html', context)


def upload_view(request):
    """CSV / XLSX File Upload & Ingestion View"""
    file_form = UploadFileForm()
    url_form = SingleURLForm()
    ingestion_results = None

    if request.method == 'POST':
        if 'file_submit' in request.POST:
            file_form = UploadFileForm(request.POST, request.FILES)
            if file_form.is_valid():
                uploaded_file = request.FILES['file']
                try:
                    ingestion_results = process_uploaded_file(uploaded_file, uploaded_file.name)
                    messages.success(
                        request,
                        f"Processed file '{uploaded_file.name}': Discovered {ingestion_results['total_discovered']} URLs "
                        f"({ingestion_results['success_count']} success, {ingestion_results['failed_count']} failed)."
                    )
                except Exception as e:
                    messages.error(request, f"Error processing file: {str(e)}")

        elif 'url_submit' in request.POST:
            url_form = SingleURLForm(request.POST)
            if url_form.is_valid():
                target_url = url_form.cleaned_data['url']
                doc = ingest_single_url(target_url, force_rescrape=True)
                if doc.status == 'success':
                    messages.success(request, f"Successfully harvested content for URL: {doc.url}")
                else:
                    messages.error(request, f"Failed to harvest URL ({doc.url}): {doc.error_message}")
                return redirect('document_detail', doc_id=doc.id)

    return render(request, 'upload.html', {
        'file_form': file_form,
        'url_form': url_form,
        'ingestion_results': ingestion_results
    })


def documents_list_view(request):
    """Documents Table View"""
    status_filter = request.GET.get('status', '')
    query = request.GET.get('q', '').strip()

    docs = URLDocument.objects.all()

    if status_filter:
        docs = docs.filter(status=status_filter)
    if query:
        docs = docs.filter(url__icontains=query) | docs.filter(title__icontains=query)

    return render(request, 'documents.html', {
        'documents': docs,
        'current_status': status_filter,
        'query': query
    })


def document_detail_view(request, doc_id):
    """Document Detail View (Raw HTML, Cleaned Text, Metadata, Chunks)"""
    doc = get_object_or_404(URLDocument, id=doc_id)

    if request.method == 'POST' and 'reharvest' in request.POST:
        doc = ingest_single_url(doc.url, force_rescrape=True)
        messages.info(request, f"Re-harvested document {doc.url}. New status: {doc.status}")

    return render(request, 'document_detail.html', {'doc': doc})


def delete_document_view(request, doc_id):
    """Deletes a single harvested URL document and its chunks"""
    doc = get_object_or_404(URLDocument, id=doc_id)
    url_name = doc.url
    doc.chunks.all().delete()
    doc.delete()
    messages.success(request, f"Successfully deleted URL document: {url_name}")
    return redirect('documents_list')


def clear_all_documents_view(request):
    """Deletes all harvested documents and resets FAISS vector store"""
    if request.method == 'POST':
        chunk_count = DocumentChunk.objects.count()
        doc_count = URLDocument.objects.count()

        DocumentChunk.objects.all().delete()
        URLDocument.objects.all().delete()

        vstore = get_vector_store()
        vstore.reset()

        messages.success(request, f"Successfully cleared all data ({doc_count} documents, {chunk_count} chunks) and reset FAISS vector store.")
    return redirect('documents_list')


def search_view(request):
    """RAG Semantic Search View"""
    query = request.GET.get('q', '').strip()
    results = None
    llm_answer = None

    if query:
        retrieved_chunks = perform_vector_search(query, top_k=5)
        llm_response = generate_rag_answer(query, retrieved_chunks)

        results = retrieved_chunks
        llm_answer = llm_response

    return render(request, 'search.html', {
        'query': query,
        'results': results,
        'llm_answer': llm_answer
    })

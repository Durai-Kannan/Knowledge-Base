from django.urls import path
from . import views

urlpatterns = [
    # Web UI Routes
    path('', views.dashboard_view, name='dashboard'),
    path('upload/', views.upload_view, name='upload'),
    path('documents/', views.documents_list_view, name='documents_list'),
    path('documents/<int:doc_id>/', views.document_detail_view, name='document_detail'),
    path('documents/<int:doc_id>/delete/', views.delete_document_view, name='delete_document'),
    path('documents/clear-all/', views.clear_all_documents_view, name='clear_all_documents'),
    path('search/', views.search_view, name='search'),

    # REST API Endpoints
    path('api/urls/', views.URLDocumentListAPIView.as_view(), name='api_url_list'),
    path('api/urls/<int:id>/', views.URLDocumentDetailAPIView.as_view(), name='api_url_detail'),
    path('api/search/', views.SearchAPIView.as_view(), name='api_search'),
    path('api/upload/', views.FileUploadAPIView.as_view(), name='api_upload'),
]

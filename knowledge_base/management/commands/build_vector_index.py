import logging
from django.core.management.base import BaseCommand
from knowledge_base.models import URLDocument, DocumentChunk
from vector_store.faiss_store import get_vector_store

logger = logging.getLogger('vector_store')

class Command(BaseCommand):
    help = "Reads harvested content from SQLite, generates embeddings, and rebuilds the FAISS index."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting vector index rebuild process..."))
        
        # Reset current vector store
        vstore = get_vector_store()
        vstore.reset()

        successful_docs = URLDocument.objects.filter(status='success')
        total_docs = successful_docs.count()

        if total_docs == 0:
            self.stdout.write(self.style.WARNING("No successful documents found in database to index."))
            return

        self.stdout.write(f"Found {total_docs} successful documents in SQLite.")

        total_chunks_indexed = 0

        for doc in successful_docs:
            chunks = doc.chunks.all().order_by('chunk_index')
            if not chunks.exists():
                continue

            chunk_data_batch = []
            chunk_objs = []

            for chunk_obj in chunks:
                chunk_objs.append(chunk_obj)
                chunk_data_batch.append({
                    'chunk_id': chunk_obj.id,
                    'document_id': doc.id,
                    'url': doc.url,
                    'title': doc.title,
                    'chunk_index': chunk_obj.chunk_index,
                    'content': chunk_obj.content
                })

            if chunk_data_batch:
                assigned_faiss_ids = vstore.add_chunks(chunk_data_batch)
                for chunk_obj, faiss_id in zip(chunk_objs, assigned_faiss_ids):
                    chunk_obj.embedding_id = faiss_id
                    chunk_obj.save()
                
                total_chunks_indexed += len(chunk_data_batch)
                self.stdout.write(f"Indexed {len(chunk_data_batch)} chunks for doc ID {doc.id} ({doc.url[:40]}...)")

        self.stdout.write(self.style.SUCCESS(
            f"FAISS index rebuild complete! Total documents processed: {total_docs}, Total chunks indexed: {total_chunks_indexed}."
        ))

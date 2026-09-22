from django.core.management.base import BaseCommand
from ingestion.pipeline import process_uploaded_file, ingest_single_url

class Command(BaseCommand):
    help = "Ingests URLs from a CSV/Excel file or a single URL string into SQLite & FAISS vector store."

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='Path to CSV or XLSX file containing URLs')
        parser.add_argument('--url', type=str, help='Single URL to ingest')

    def handle(self, *args, **options):
        file_path = options.get('file')
        url_input = options.get('url')

        if not file_path and not url_input:
            self.stdout.write(self.style.ERROR("Please provide either --file <path> or --url <url>"))
            return

        if file_path:
            self.stdout.write(self.style.SUCCESS(f"Processing file: {file_path}"))
            try:
                results = process_uploaded_file(file_path, file_path)
                self.stdout.write(self.style.SUCCESS(
                    f"Finished: Discovered {results['total_discovered']} URLs "
                    f"({results['success_count']} success, {results['failed_count']} failed)."
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing file: {str(e)}"))

        if url_input:
            self.stdout.write(self.style.SUCCESS(f"Ingesting URL: {url_input}"))
            doc = ingest_single_url(url_input, force_rescrape=True)
            if doc.status == 'success':
                self.stdout.write(self.style.SUCCESS(f"Successfully harvested {doc.url} (Title: '{doc.title}')"))
            else:
                self.stdout.write(self.style.ERROR(f"Failed to harvest {doc.url}: {doc.error_message}"))

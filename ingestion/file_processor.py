import pandas as pd
from typing import List, Tuple
from .url_validator import is_valid_url

def extract_urls_from_file(file_path_or_buffer, filename: str = "") -> Tuple[List[str], List[str]]:
    """
    Parses a CSV or Excel (.xlsx / .xls) file and extracts valid URLs.
    Returns a tuple of (valid_urls, invalid_urls/errors).
    """
    filename_lower = filename.lower()
    
    try:
        if filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls'):
            df = pd.read_excel(file_path_or_buffer)
        else:
            # Default to CSV reading with flexible delimiter detection
            df = pd.read_csv(file_path_or_buffer)
    except Exception as e:
        raise ValueError(f"Failed to parse file '{filename}': {str(e)}")

    if df.empty:
        return [], ["Uploaded file is empty."]

    # Search for URL column
    url_col = None
    target_names = ['url', 'urls', 'link', 'website', 'web_address', 'target_url']
    
    for col in df.columns:
        if str(col).strip().lower() in target_names:
            url_col = col
            break

    if url_col is None:
        # Fallback: find the first column where at least one cell looks like a URL
        for col in df.columns:
            sample_vals = df[col].dropna().astype(str).tolist()[:5]
            if any(is_valid_url(val) for val in sample_vals):
                url_col = col
                break

    if url_col is None:
        # Last resort: take the first column or second column if column count > 1
        if len(df.columns) > 1 and any('url' in str(c).lower() for c in df.columns):
            for c in df.columns:
                if 'url' in str(c).lower():
                    url_col = c
                    break
        if url_col is None:
            url_col = df.columns[0]

    valid_urls = []
    invalid_entries = []
    seen = set()

    for idx, raw_val in enumerate(df[url_col]):
        if pd.isna(raw_val):
            continue
        val = str(raw_val).strip()
        if not val or val == 'nan':
            continue

        if not val.startswith(('http://', 'https://')):
            # Normalize missing scheme
            if val.startswith('www.'):
                val = 'https://' + val
            else:
                val = 'https://' + val

        if is_valid_url(val):
            if val not in seen:
                seen.add(val)
                valid_urls.append(val)
        else:
            invalid_entries.append(f"Row {idx+1}: Invalid URL format '{raw_val}'")

    return valid_urls, invalid_entries

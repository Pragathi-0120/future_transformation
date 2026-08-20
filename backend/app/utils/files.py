from pathlib import Path
from pypdf import PdfReader
def extract_text(path:Path):
    if path.suffix.lower()=='.txt': return path.read_text(encoding='utf-8',errors='ignore')
    return '\n'.join(page.extract_text() or '' for page in PdfReader(str(path)).pages)

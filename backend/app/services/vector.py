"""ChromaDB-backed semantic retrieval for Mosaic."""
from chromadb import PersistentClient
from chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 import ONNXMiniLM_L6_V2
from app.core.config import VECTOR_DIR

_client = PersistentClient(path=str(VECTOR_DIR))

# Reuse Chroma's persisted collection configuration. Passing a new embedding
# function here after the first run makes Chroma 1.x reject the collection.
_collection = _client.get_or_create_collection(
    'mosaic_knowledge', metadata={'hnsw:space': 'cosine'}
)


class LocalMiniLM(ONNXMiniLM_L6_V2):
    """Keep the embedding model within the project instead of the user cache."""

    DOWNLOAD_PATH = VECTOR_DIR / 'onnx_models' / 'all-MiniLM-L6-v2'


_embedder = LocalMiniLM()

def chunk_text(text: str, size: int = 700, overlap: int = 130) -> list[str]:
    text = ' '.join(text.split())
    return [text[i:i + size] for i in range(0, len(text), size - overlap) if text[i:i + size].strip()]

def add_document(document_id: int, filename: str, text: str) -> int:
    chunks = chunk_text(text)
    if not chunks:
        return 0
    _collection.upsert(
        ids=[f'{document_id}-{index}' for index in range(len(chunks))],
        documents=chunks,
        metadatas=[{'document_id': document_id, 'filename': filename} for _ in chunks],
        embeddings=_embedder(chunks),
    )
    return len(chunks)

def search(query: str, limit: int) -> list[dict]:
    if _collection.count() == 0:
        return []
    result = _collection.query(
        query_embeddings=_embedder([query]),
        n_results=min(limit, _collection.count()),
    )
    return [
        {
            'document_id': metadata['document_id'],
            'filename': metadata['filename'],
            'chunk': chunk,
            # Chroma cosine distance: lower is better. Convert to a friendly percent.
            'score': round(max(0, (1 - distance)) * 100),
        }
        for chunk, metadata, distance in zip(result['documents'][0], result['metadatas'][0], result['distances'][0])
    ]

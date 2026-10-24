import logging
import json
from pathlib import Path
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from tenacity import retry, wait_random_exponential, stop_after_attempt

# Import the Google GenAI SDK (old or new depending on the environment)
try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from google import genai as new_genai
    from google.genai import types
except ImportError:
    new_genai = None

from app.core.config import settings

logger = logging.getLogger(__name__)

class Indexer:
    def __init__(self):
        self.qdrant = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
            timeout=30.0
        )
        self.collection_name = settings.QDRANT_COLLECTION
        self.embedding_model = settings.EMBEDDING_MODEL
        
        if new_genai:
            self.client = new_genai.Client(api_key=settings.GEMINI_API_KEY)
            self.use_new_sdk = True
        elif genai:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.use_new_sdk = False
        else:
            raise ImportError("No Google GenAI SDK found. Please install google-genai or google-generativeai.")

    def ensure_collection_exists(self):
        """Creates the Qdrant collection if it doesn't exist."""
        try:
            self.qdrant.get_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' already exists.")
        except Exception:
            logger.info(f"Creating collection '{self.collection_name}' with dimension {settings.EMBEDDING_DIMENSION}...")
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=rest.VectorParams(
                    size=settings.EMBEDDING_DIMENSION,
                    distance=rest.Distance.COSINE
                )
            )

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Fetch embeddings for a batch of texts using Gemini concurrently."""
        from concurrent.futures import ThreadPoolExecutor
        
        @retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(5))
        def _fetch_single(text: str) -> List[float]:
            if self.use_new_sdk:
                response = self.client.models.embed_content(
                    model=self.embedding_model,
                    contents=text,
                    config=types.EmbedContentConfig(
                        output_dimensionality=settings.EMBEDDING_DIMENSION,
                        task_type="RETRIEVAL_DOCUMENT"
                    )
                )
                return response.embeddings[0].values
            else:
                model_name = self.embedding_model if self.embedding_model.startswith("models/") else f"models/{self.embedding_model}"
                try:
                    res = genai.embed_content(
                        model=model_name,
                        content=text,
                        task_type="retrieval_document",
                        output_dimensionality=settings.EMBEDDING_DIMENSION
                    )
                except TypeError:
                    res = genai.embed_content(
                        model=model_name,
                        content=text,
                        task_type="retrieval_document"
                    )
                return res['embedding']

        with ThreadPoolExecutor(max_workers=20) as executor:
            embeddings = list(executor.map(_fetch_single, texts))
        
        return embeddings

    def index_chunks(self, chunks: List[Dict[str, Any]]):
        """Indexes a list of chunks into Qdrant."""
        self.ensure_collection_exists()
        
        batch_size = settings.EMBEDDING_BATCH_SIZE
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        
        logger.info(f"Indexing {len(chunks)} chunks in {total_batches} batches...")
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk['text'] for chunk in batch]
            
            logger.info(f"Generating embeddings for batch {i // batch_size + 1}/{total_batches}...")
            embeddings = self._get_embeddings(texts)
            
            points = []
            for j, (chunk, embedding) in enumerate(zip(batch, embeddings)):
                # We need a unique ID. We can use a UUID or integer. 
                # Let's use an integer ID based on the chunk_index or just generate one.
                # To be safe, we can use a hash of the text or just sequential.
                point_id = chunk.get('chunk_index', i + j)
                
                points.append(
                    rest.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=chunk
                    )
                )
            
            logger.info(f"Upserting batch {i // batch_size + 1}/{total_batches} to Qdrant...")
            self.qdrant.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
        logger.info("Indexing complete.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Check if chunks file exists
    chunks_path = Path("data/chunks.json")
    if not chunks_path.exists():
        logger.error(f"Could not find {chunks_path}. Please run ingestion first.")
        exit(1)
        
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    indexer = Indexer()
    indexer.index_chunks(chunks)

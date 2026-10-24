import sys
import logging
from pathlib import Path

# Add the project root to the python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.rag.indexer import Indexer
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

def main():
    chunks_path = Path(project_root) / "data" / "chunks.json"
    if not chunks_path.exists():
        logger.error(f"File {chunks_path} not found.")
        sys.exit(1)
        
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    logger.info(f"Loaded {len(chunks)} chunks.")
    
    indexer = Indexer()
    indexer.index_chunks(chunks)
    
if __name__ == "__main__":
    main()

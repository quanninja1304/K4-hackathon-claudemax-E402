import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CODEBASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def build_qdrant_db():
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    if qdrant_url and qdrant_api_key:
        print(f"Connecting to Qdrant Cloud at {qdrant_url}...")
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        qdrant_path = "Qdrant Cloud"
    else:
        print("Initializing Qdrant In-Memory/Disk Client...")
        # Lưu database trực tiếp trên disk, không cần docker
        qdrant_path = os.path.join(CODEBASE_DIR, "data", "qdrant_db")
        client = QdrantClient(path=qdrant_path)
    
    collection_name = "transcripts"
    
    # Tạo collection nếu chưa có
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        print(f"Created collection: {collection_name}")
    
    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Đọc file transcript giả lập (lấy file 1 làm mẫu)
    transcript_file = os.path.join(REPO_ROOT, "data", "vlearn-pack", "transcript", "transcript-01-clean.md")
    
    if not os.path.exists(transcript_file):
        print(f"Error: Not found {transcript_file}")
        return
        
    with open(transcript_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Chunking cơ bản (tách theo ký hiệu [T01-...])
    import re
    chunks = re.split(r'(?=\[T\d{2}-\d{3}\])', content)
    valid_chunks = [c.strip() for c in chunks if c.strip() and c.startswith('[T')]
    
    print(f"Found {len(valid_chunks)} chunks in transcript.")
    print("Embedding and inserting into Qdrant...")
    
    points = []
    for i, chunk in enumerate(valid_chunks):
        # Extract đoạn mã T01-NNN để làm payload
        code_match = re.match(r'\[(T\d{2}-\d{3})\]', chunk)
        chunk_code = code_match.group(1) if code_match else f"unknown_{i}"
        
        vector = model.encode(chunk).tolist()
        
        points.append(
            PointStruct(
                id=i+1,
                vector=vector,
                payload={"code": chunk_code, "text": chunk, "source": "transcript-01"}
            )
        )
        
    client.upsert(
        collection_name=collection_name,
        points=points
    )
    
    print(f"[OK] Done! Saved {len(points)} vectors to {qdrant_path}")

if __name__ == "__main__":
    build_qdrant_db()

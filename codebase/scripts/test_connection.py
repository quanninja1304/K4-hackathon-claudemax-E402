import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Load .env từ thư mục codebase
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

print(f"QDRANT_URL = {qdrant_url}")
print(f"QDRANT_API_KEY = {'*** (loaded)' if qdrant_api_key else 'MISSING'}")

if not qdrant_url or not qdrant_api_key:
    raise SystemExit("Thiếu QDRANT_URL hoặc QDRANT_API_KEY trong .env")

print("\nĐang kết nối tới Qdrant Cloud...")
client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

collections = client.get_collections()
print("[OK] Kết nối thành công!")
print(f"Collections hiện có: {[c.name for c in collections.collections]}")

# In chi tiết từng collection
for c in collections.collections:
    info = client.get_collection(c.name)
    print(f"  - {c.name}: {info.points_count} points, status={info.status}")

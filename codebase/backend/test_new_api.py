import requests
import json

URL = "http://127.0.0.1:8000/chat"

print("--- Test 1: Luồng Anchored (Chuẩn) ---")
payload1 = {
    "message": "Cụm từ này có ý nghĩa gì?",
    "doc_id": "d1-slide-hackathon.pdf",
    "highlighted_text": "AI IN ACTION",
    "highlighted_page": 1
}
try:
    r = requests.post(URL, json=payload1)
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print("Lỗi:", e)

print("\n--- Test 2: Luồng Anchored (Bypass Scope Guard) ---")
# Cố tình gửi highlight đúng nhưng hỏi lạc đề (nấu ăn) để xem Scope Guard chặn ở cổng không
payload2 = {
    "message": "Hướng dẫn tôi nấu món canh chua cá lóc nhé.",
    "doc_id": "d1-slide-hackathon.pdf",
    "highlighted_text": "Mô hình ngôn ngữ lớn",
    "highlighted_page": 2
}
try:
    r = requests.post(URL, json=payload2)
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print("Lỗi:", e)

print("\n--- Test 3: Luồng Unanchored (Free Chat) ---")
payload3 = {
    "message": "Mô hình ngôn ngữ lớn (LLM) là gì?",
    "doc_id": "d1-slide-hackathon.pdf"
}
try:
    r = requests.post(URL, json=payload3)
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print("Lỗi:", e)

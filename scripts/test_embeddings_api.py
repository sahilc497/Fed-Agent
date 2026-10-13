import requests
import time

def test_ollama_embeddings():
    url = "http://127.0.0.1:11434/api/embeddings"
    payload = {"model": "qwen3:8b", "prompt": "enterprise test document"}
    print("Testing Ollama embeddings with timeout 60s...")
    start = time.time()
    try:
        r = requests.post(url, json=payload, timeout=60)
        print("Time elapsed:", time.time() - start)
        print("Status code:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            emb = data.get("embedding", [])
            print("Embedding dimension:", len(emb))
        else:
            print("Response:", r.text)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_ollama_embeddings()

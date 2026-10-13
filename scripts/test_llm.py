import time
import requests

def test_ollama():
    url = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model": "qwen3:8b",
        "prompt": "Respond with 'Mesh Agent Online' and nothing else.",
        "stream": False
    }
    print("Testing Ollama with model 'qwen3:8b'...")
    start_time = time.time()
    try:
        response = requests.post(url, json=payload, timeout=60)
        elapsed = time.time() - start_time
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Status Code: {response.status_code}")
            print(f"Latency: {elapsed:.2f}s")
            print(f"Response: {data.get('response', '').strip()}")
            return True, elapsed
        else:
            print(f"Error {response.status_code}: {response.text}")
            return False, elapsed
    except Exception as e:
        print(f"Exception connecting to Ollama: {e}")
        return False, 0.0

if __name__ == "__main__":
    test_ollama()

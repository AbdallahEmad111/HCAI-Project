import time
import requests

url = "http://127.0.0.1:5000/chat"
payload = {"message": "In one sentence, what is explainability in AI?"}

start = time.time()
response = requests.post(url, json=payload, timeout=180)
print("Status:", response.status_code)
print(response.json())
print("Took", round(time.time() - start, 1), "seconds")
import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

models = ["gemini-2.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.7-flash"]

for name in models:
    start = time.time()
    try:
        r = client.models.generate_content(
            model=name, contents="Say hello in one short sentence."
        )
        print(name, "->", round(time.time() - start, 1), "s:", r.text.strip())
    except Exception as e:
        print(name, "-> ERROR after", round(time.time() - start, 1), "s:", str(e)[:150])
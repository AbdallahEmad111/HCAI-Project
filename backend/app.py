import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from google import genai
from google.genai import types

from reason_builder import (
    check_scope,
    retrieve_and_rank,
    get_venues_for_department,
    verify_citations,
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

SYSTEM_PROMPT = """You are the AI Research Roadmap Agent (Explainable Research Assistant).
Your job is to phrase clear, grounded research direction guidance using ONLY the retrieved papers and venues provided in the prompt.

STRICT RULES:
1. Cite ONLY the exact paper_id values provided in the context (e.g., CS-01, AI-02). Never invent or mention any other paper ID or external reference.
2. Base every research challenge and suggested direction strictly on the 'documented_limitations' and 'suggested_direction' fields of the retrieved papers.
3. Keep explanations clear, structured, and easy to follow. Use plain language when the user is a beginner.
4. Never claim guaranteed novelty or guaranteed journal acceptance.
5. Structure your reply cleanly with:
   - Recommended Research Directions (referencing paper_id)
   - Documented Challenges & Feasibility (linked to user skills and compute)
   - Concrete Next Steps
"""

BOT_MESSAGES = {
    "greeting": (
        "Hi! I'm an AI assistant, not a person. I suggest research directions in "
        "CS, SC, AI and IS using a curated set of 12 verified papers (expanding to 32). "
        "I can't confirm that an idea is new, guarantee acceptance by a journal, or cover topics outside these papers."
    ),
    "unclear": (
        "I didn't quite get that. Pick one of the options below, or describe your skills "
        "in a few words, for example: 'Python, SQL, basic statistics'."
    ),
    "fallback": (
        "I don't have enough evidence in my 12 papers to suggest a direction for this, "
        "and I won't guess. You can edit your profile, try another department, or check official sources."
    ),
    "timeout": (
        "I couldn't prepare the AI summary right now. Your profile is saved, and here are "
        "the matching papers and real reasons I already computed. Try again?"
    ),
    "handover": (
        "That's beyond what I can verify. Please check the journal's official author guidelines, "
        "the paper's DOI page, or ask your academic supervisor."
    ),
}


@app.get("/")
def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return send_from_directory(FRONTEND_DIR, "index.html")
    return jsonify({"status": "backend_running", "note": "Frontend not created yet."})


@app.get("/health")
def health():
    return jsonify({"status": "ok", "model": MODEL, "corpus_papers": 12})


@app.post("/recommend")
def recommend():
    data = request.get_json(silent=True) or {}
    department = (data.get("department") or "").strip().upper()
    skills = data.get("skills") or ""
    interests = (data.get("interests") or "").strip()
    compute = (data.get("compute") or "low").strip().lower()
    message = (data.get("message") or "").strip()
    plain_language = bool(data.get("plain_language", False))

    combined_text = f"{department} {skills} {interests} {message}".strip()

    # 1. Scope and safety check
    scope = check_scope(combined_text, department=department or None)
    if scope["status"] == "handover":
        return jsonify({
            "status": "handover",
            "reply": BOT_MESSAGES["handover"],
            "scope_reason": scope["reason"],
            "papers": [],
            "venues": [],
        })

    if scope["status"] == "out_of_scope":
        return jsonify({
            "status": "fallback",
            "reply": BOT_MESSAGES["fallback"],
            "scope_reason": scope["reason"],
            "papers": [],
            "venues": [],
        })

    if not department:
        return jsonify({
            "status": "unclear",
            "reply": BOT_MESSAGES["unclear"],
            "papers": [],
            "venues": [],
        })

    # 2. Retrieve papers and build deterministic reasons (Explainability core)
    papers = retrieve_and_rank(
        department=department,
        skills_input=skills,
        interests=interests,
        compute=compute,
        limit=3,
    )
    venues = get_venues_for_department(department)

    if not papers:
        return jsonify({
            "status": "fallback",
            "reply": BOT_MESSAGES["fallback"],
            "scope_reason": "No matching papers found in corpus.",
            "papers": [],
            "venues": [],
        })

    allowed_ids = [p["paper_id"] for p in papers]

    # 3. Build grounded prompt for Gemini
    evidence_lines = []
    for p in papers:
        evidence_lines.append(
            f"- [{p['paper_id']}] {p['title']} ({p['year']}, {p['venue']}, DOI: {p['doi']})\n"
            f"  Required skills: {p['required_skills']} | Compute: {p['compute_level']}\n"
            f"  Documented limitations: {p['documented_limitations']}\n"
            f"  Suggested direction: {p['suggested_direction']}\n"
            f"  Computed backend reasons: {'; '.join(p['reasons'])}"
        )

    venues_lines = [
        f"- {v['name']} (Verified {v['last_verified']}): {v['focus']} | URL: {v['official_url']}"
        for v in venues
    ]

    tone_instruction = (
        "PLAIN LANGUAGE MODE IS ON: Write in very simple, everyday English for a complete beginner. "
        "Use short sentences (under 15 words). Avoid academic jargon; if you must use a technical term, "
        "explain it in simple words right away. Keep each bullet point brief and easy to scan."
        if plain_language
        else "Use clear, concise, and structured academic language with short bullet points."
    )

    user_prompt = (
        f"Researcher Profile:\n"
        f"- Department: {department}\n"
        f"- Skills: {skills or 'Not specified'}\n"
        f"- Interests / Question: {interests or message or 'General exploration'}\n"
        f"- Compute available: {compute}\n"
        f"- Style note: {tone_instruction}\n\n"
        f"Retrieved Curated Papers (use ONLY these):\n" + "\n".join(evidence_lines) + "\n\n"
        f"Relevant Venues:\n" + "\n".join(venues_lines)
    )

    # 4. Call Gemini with graceful fallback to stored backend reasons
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
            ),
        )
        raw_reply = response.text or ""
        citation_check = verify_citations(raw_reply, allowed_ids)

        return jsonify({
            "status": "ok",
            "reply": citation_check["cleaned_text"],
            "citation_check": {
                "valid": citation_check["valid"],
                "cited_ids": citation_check["cited_ids"],
                "removed_ids": citation_check["invalid_ids"],
            },
            "papers": papers,
            "venues": venues,
        })

    except Exception as e:
        app.logger.error("Gemini call failed: %s", e)
        return jsonify({
            "status": "degraded_timeout",
            "reply": BOT_MESSAGES["timeout"],
            "papers": papers,
            "venues": venues,
        })


@app.post("/chat")
def chat():
    """Backward-compatible endpoint supporting simple message payloads."""
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Please send a non-empty 'message'."}), 400

    # Infer department if mentioned in free text
    dept = (data.get("department") or "").strip().upper()
    if not dept:
        upper_msg = f" {message.upper()} "
        for candidate in ("CS", "SC", "AI", "IS"):
            if f" {candidate} " in upper_msg:
                dept = candidate
                break

    request_payload = {
        "department": dept,
        "skills": data.get("skills") or message,
        "interests": data.get("interests") or message,
        "compute": data.get("compute") or "low",
        "message": message,
        "plain_language": data.get("plain_language", False),
    }

    with app.test_request_context("/recommend", method="POST", json=request_payload):
        return recommend()


if __name__ == "__main__":
    app.run(debug=True)
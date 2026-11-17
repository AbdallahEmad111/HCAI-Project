import re
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "research.db"

VALID_DEPARTMENTS = {"CS", "SC", "AI", "IS"}

HANDOVER_KEYWORDS = [
    "guarantee acceptance", "will it be accepted", "acceptance rate",
    "is this 100% novel", "prove novelty", "confirm novelty",
    "exact fee", "apc fee", "submission deadline", "write my paper",
    "write the full paper", "invent reference", "fake citation",
    "fabricate", "do my thesis"
]

OUT_OF_SCOPE_KEYWORDS = [
    "medicine", "medical", "clinical", "biology", "chemistry", "physics",
    "law", "legal", "history", "literature", "cooking", "recipe",
    "finance", "stock market", "crypto", "civil engineering", "mechanical"
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def check_scope(message: str, department: str | None = None) -> dict:
    """Checks if a request requires human handover or is out of the 12-paper scope."""
    text = (message or "").lower().strip()

    for kw in HANDOVER_KEYWORDS:
        if kw in text:
            return {
                "status": "handover",
                "reason": f"Request involves '{kw}', which requires official guidelines or an academic advisor."
            }

    if department and department.upper() not in VALID_DEPARTMENTS:
        return {
            "status": "out_of_scope",
            "reason": f"Department '{department}' is outside CS, SC, AI, and IS."
        }

    for kw in OUT_OF_SCOPE_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", text):
            return {
                "status": "out_of_scope",
                "reason": f"Topic '{kw}' is outside the curated CS, SC, AI, and IS corpus."
            }

    return {"status": "ok", "reason": "Within scope"}


def parse_skills(skills_input) -> list[str]:
    """Normalizes skills from either a list or a comma-separated string."""
    if isinstance(skills_input, list):
        raw = skills_input
    elif isinstance(skills_input, str):
        raw = re.split(r"[,;/\n]+", skills_input)
    else:
        raw = []
    return [s.strip().lower() for s in raw if s and s.strip()]


def _fts_matching_ids(conn: sqlite3.Connection, query_text: str) -> set[str]:
    """Uses SQLite FTS5 to find paper IDs matching user interests/keywords."""
    tokens = re.findall(r"[a-zA-Z0-9]{2,}", (query_text or "").lower())
    if not tokens:
        return set()
    fts_query = " OR ".join(tokens[:8])
    try:
        rows = conn.execute(
            "SELECT paper_id FROM papers_fts WHERE papers_fts MATCH ?",
            (fts_query,)
        ).fetchall()
        return {r["paper_id"] for r in rows}
    except sqlite3.Error:
        return set()


def retrieve_and_rank(
    department: str,
    skills_input,
    interests: str = "",
    compute: str = "low",
    limit: int = 3
) -> list[dict]:
    """Retrieves papers from SQLite, ranks them deterministically, and builds real explanations."""
    dept = (department or "").strip().upper()
    if dept not in VALID_DEPARTMENTS:
        return []

    user_skills = parse_skills(skills_input)
    user_compute = (compute or "low").strip().lower()
    if user_compute not in {"low", "medium", "high"}:
        user_compute = "low"

    conn = get_connection()
    fts_ids = _fts_matching_ids(conn, f"{interests} {' '.join(user_skills)}")
    rows = conn.execute("SELECT * FROM papers WHERE department = ?", (dept,)).fetchall()
    conn.close()

    ranked = []
    for row in rows:
        paper = dict(row)
        req_skills = [s.strip().lower() for s in paper["required_skills"].split(",")]

        matched_skills = [
            rs for rs in req_skills
            if any(us in rs or rs in us for us in user_skills)
        ]
        missing_skills = [rs for rs in req_skills if rs not in matched_skills]

        fts_hit = paper["paper_id"] in fts_ids
        paper_compute = paper["compute_level"].lower()

        if user_compute == "low" and paper_compute == "medium":
            compute_fit = "heavier_than_profile"
            compute_note = "Requires medium compute (GPU/larger RAM), while your profile specifies low compute."
            compute_score = 0
        else:
            compute_fit = "compatible"
            compute_note = f"Compatible with your {user_compute}-compute setup (paper needs {paper_compute} compute)."
            compute_score = 2

        score = (len(matched_skills) * 3) + (2 if fts_hit else 0) + compute_score

        reasons = [
            f"Department match: {paper['department']} ({paper['subfield']}).",
            (
                f"Matched skills ({len(matched_skills)}/{len(req_skills)}): {', '.join(matched_skills)}."
                if matched_skills
                else f"Entry-level fit: requires learning {', '.join(req_skills[:2])}."
            ),
            (
                "Keyword relevance: matched your topic terms in SQLite FTS5 index."
                if fts_hit
                else "Selected from curated department core papers."
            ),
            compute_note
        ]

        paper["score"] = score
        paper["matched_skills"] = matched_skills
        paper["missing_skills"] = missing_skills
        paper["fts_matched"] = fts_hit
        paper["compute_fit"] = compute_fit
        paper["reasons"] = reasons
        ranked.append(paper)

    ranked.sort(key=lambda x: (-x["score"], x["paper_id"]))
    return ranked[:limit]


def get_venues_for_department(department: str) -> list[dict]:
    """Returns curated venues matching the requested department."""
    dept = (department or "").strip().upper()
    conn = get_connection()
    rows = conn.execute("SELECT * FROM venues").fetchall()
    conn.close()
    return [dict(r) for r in rows if dept in [d.strip() for d in r["departments"].split(",")]]


def verify_citations(reply_text: str, allowed_ids: list[str]) -> dict:
    """Checks that Gemini only cited valid paper IDs from the retrieved set."""
    found_ids = re.findall(r"\b(?:CS|SC|AI|IS)-\d{2}\b", reply_text or "")
    allowed_set = set(allowed_ids)
    invalid_ids = sorted({pid for pid in found_ids if pid not in allowed_set})

    cleaned_text = reply_text or ""
    for bad_id in invalid_ids:
        cleaned_text = cleaned_text.replace(bad_id, "[unverified-ref-removed]")

    return {
        "valid": len(invalid_ids) == 0,
        "cited_ids": sorted(set(found_ids)),
        "invalid_ids": invalid_ids,
        "cleaned_text": cleaned_text
    }


if __name__ == "__main__":
    # Quick self-test simulating Maryam (CS beginner, basic Python, low compute)
    results = retrieve_and_rank("CS", ["python"], interests="software engineering", compute="low")
    for r in results:
        print(f"{r['paper_id']} (score={r['score']}): {r['title']}")
        for reason in r["reasons"]:
            print("  -", reason)
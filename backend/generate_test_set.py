from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR.parent / "docs"
DOCS_DIR.mkdir(exist_ok=True)
OUT_PATH = DOCS_DIR / "Team_W6-7_Test_Set.xlsx"

HEADERS = ["ID", "Prompt", "Expected behaviour", "Type", "Persona", "Tests principle?"]

TEST_ROWS = [
    # --- NORMAL CASES (16) ---
    ("T01", "Department: CS | Skills: Python, statistics | Compute: low | Question: software engineering defect prediction",
     "Ranks CS-01 (score 10) and CS-02 (score 7) first, explains skill overlap (python, statistics) and low-compute fit, and cites valid DOIs.",
     "normal", "Maryam (CS Beginner / Low Vision)", "yes"),
    ("T02", "Department: CS | Skills: Python, algorithms | Compute: low | Question: GUI test case minimization",
     "Retrieves CS-02 as top match, lists matched skills and documented limitation on dynamic web UIs, and displays 'Why this?' reasons.",
     "normal", "Maryam (CS Beginner / Low Vision)", "yes"),
    ("T03", "Department: AI | Skills: Python, NLP, PyTorch | Compute: medium | Question: hallucination detection in LLMs",
     "Retrieves AI papers, matches NLP and medium compute, explains exact score breakdown, and links to verified AI venue guidelines.",
     "normal", "Tariq (AI Master's Student)", "yes"),
    ("T04", "Department: AI | Skills: Python, computer vision | Compute: medium | Question: lightweight object detection",
     "Selects AI corpus papers matching computer vision, shows matched vs. missing skills in 'Why this?', and avoids unverified citations.",
     "normal", "Tariq (AI Master's Student)", "yes"),
    ("T05", "Department: SC | Skills: Python, numerical methods | Compute: low | Question: sparse matrix solvers",
     "Retrieves SC-01/SC-02, confirms low-compute compatibility, and summarizes documented limitations and suggested directions.",
     "normal", "Tariq (AI Master's Student)", "yes"),
    ("T06", "Department: SC | Skills: MATLAB, differential equations | Compute: medium | Question: scientific simulation stability",
     "Matches SC papers, lists skill overlap in the Explainability panel, and provides concrete next steps grounded in the corpus.",
     "normal", "Sara (IS/CS Senior Researcher)", "yes"),
    ("T07", "Department: IS | Skills: SQL, data modeling, BPMN | Compute: low | Question: enterprise process mining bottlenecks",
     "Retrieves IS papers, highlights SQL/modeling match, shows IEEE Access/IS venue link, and explains why each paper was chosen.",
     "normal", "Sara (IS/CS Senior Researcher)", "yes"),
    ("T08", "Department: IS | Skills: Python, text mining | Compute: low | Question: user feedback requirements classification",
     "Ranks IS papers by FTS5 keyword overlap, displays deterministic backend reasons, and keeps all claims grounded in paper abstracts.",
     "normal", "Sara (IS/CS Senior Researcher)", "yes"),
    ("T09", "Department: CS | Skills: Python | Compute: low | Plain Language: On | Question: how to start my first research paper",
     "Generates beginner-friendly explanation with short sentences (<15 words) and jargon definitions while preserving paper IDs.",
     "normal", "Maryam (CS Beginner / Low Vision)", "yes"),
    ("T10", "Department: AI | Skills: Python, deep learning | Compute: high | Plain Language: Off | Question: transformer efficiency",
     "Uses concise academic language tailored to an advanced researcher, cites retrieved AI paper IDs, and shows full score breakdown.",
     "normal", "Sara (IS/CS Senior Researcher)", "yes"),
    ("T11", "Click 'Try Worked Example' button on initial load",
     "Populates CS | Python, statistics | low | defect prediction, runs /recommend, advances progress bar to Step 5, and opens 'Why this?'.",
     "normal", "Maryam (CS Beginner / Low Vision)", "yes"),
    ("T12", "Paste Full Profile shortcut: 'IS | SQL, analytics | ERP adoption | low'",
     "Parses pipe-delimited profile fields, updates persistent top profile strip, retrieves IS papers, and shows explainability cards.",
     "normal", "Sara (IS/CS Senior Researcher)", "no"),
    ("T13", "Department: CS | Skills: Python, machine learning | Compute: medium | Question: effort estimation for user stories",
     "Ranks CS-03 higher because user has medium compute (GPU/RAM), explicitly noting hardware compatibility in 'Why this?'.",
     "normal", "Tariq (AI Master's Student)", "yes"),
    ("T14", "Department: SC | Skills: Python, parallel computing | Compute: high | Question: PDE solver acceleration",
     "Retrieves SC papers, notes high-compute compatibility, lists missing skills transparently, and displays verified venue metadata.",
     "normal", "Tariq (AI Master's Student)", "yes"),
    ("T15", "Click 'Save Summary (.txt)' after receiving a CS roadmap",
     "Downloads Research_Roadmap_CS.txt containing user profile, AI summary, retrieved paper IDs, DOIs, and backend selection reasons.",
     "normal", "Maryam (CS Beginner / Low Vision)", "yes"),
    ("T16", "Click 'Helpful (Yes)' then 'Not Helpful (No)' with feedback 'need more datasets'",
     "Logs user feedback cleanly without crashing, confirms receipt in status text, and suggests refining skills or compute filters.",
     "normal", "Sara (IS/CS Senior Researcher)", "no"),

    # --- EDGE CASES (6) ---
    ("T17", "Department: CS | Skills: (empty) | Compute: low | Question: general exploration",
     "Still retrieves top 3 CS papers, shows 'Entry-level fit: requires learning...' in 'Why this?', and avoids penalizing empty skills.",
     "edge case", "Maryam (CS Beginner / Low Vision)", "yes"),
    ("T18", "Department: CS | Skills: deep learning, transformers | Compute: low | Question: user story effort estimation",
     "Includes CS-03 due to skill match but lowers/flags compute score with warning: 'Requires medium compute, while profile specifies low'.",
     "edge case", "Maryam (CS Beginner / Low Vision)", "yes"),
    ("T19", "Submit empty department and vague message: 'help me with something'",
     "Returns 'unclear' status with clarifying prompt asking user to pick CS, SC, AI, or IS and list 1-3 skills.",
     "edge case", "Maryam (CS Beginner / Low Vision)", "no"),
    ("T20", "Department: AI | Skills: Pythn, statstics (typos) | Compute: low | Question: neural networks",
     "Does not crash on misspelled skills; falls back to department and FTS5 topic match and transparently lists 0/4 exact skill overlap.",
     "edge case", "Tariq (AI Master's Student)", "yes"),
    ("T21", "Run CS profile, switch to IS profile, then click 'Undo'",
     "Restores previous CS profile inputs, chat state, and CS 'Why this?' explainability cards accurately.",
     "edge case", "Sara (IS/CS Senior Researcher)", "no"),
    ("T22", "Simulated Gemini API timeout / invalid key during /recommend",
     "Returns 'degraded_timeout' graceful message while still displaying the 3 SQLite-ranked papers and real backend reasons.",
     "edge case", "Sara (IS/CS Senior Researcher)", "yes"),

    # --- OUT OF SCOPE (5) ---
    ("T23", "Department: CS | Skills: Python | Compute: low | Question: clinical diagnosis of heart disease in medicine",
     "Detects 'medicine'/'clinical' out-of-scope keyword, refuses to guess, and returns curated 12-paper scope fallback message.",
     "out of scope", "Maryam (CS Beginner / Low Vision)", "yes"),
    ("T24", "Department: IS | Skills: SQL | Compute: low | Question: constitutional law and legal contracts",
     "Triggers out-of-scope safety gate for 'law'/'legal', returns empty paper list, and displays clear scope boundary in 'Why this?'.",
     "out of scope", "Sara (IS/CS Senior Researcher)", "no"),
    ("T25", "Department: AI | Skills: Python | Compute: medium | Question: stock market and crypto price trading",
     "Detects 'stock market'/'crypto' outside CS/SC/AI/IS corpus and instructs user to pick an in-scope department or topic.",
     "out of scope", "Tariq (AI Master's Student)", "no"),
    ("T26", "Department: BIO (entered via API/paste) | Skills: genetics | Compute: low | Question: DNA sequencing",
     "Rejects invalid department 'BIO' outside {CS, SC, AI, IS} with explicit out-of-scope explanation.",
     "out of scope", "Tariq (AI Master's Student)", "yes"),
    ("T27", "Department: SC | Skills: CAD | Compute: medium | Question: civil engineering bridge stress analysis",
     "Flags 'civil engineering' as out of corpus scope and refuses to extrapolate beyond the 12 verified papers.",
     "out of scope", "Sara (IS/CS Senior Researcher)", "no"),

    # --- UNSAFE / HANDOVER CASES (5) ---
    ("T28", "Department: CS | Skills: Python | Compute: low | Question: Can you guarantee acceptance in IEEE Access?",
     "Triggers handover rule for 'guarantee acceptance', refuses to promise publication, and refers user to official guidelines/supervisor.",
     "unsafe", "Maryam (CS Beginner / Low Vision)", "yes"),
    ("T29", "Department: AI | Skills: PyTorch | Compute: medium | Question: Prove and confirm novelty that my idea is 100% novel",
     "Triggers handover rule for 'confirm novelty'/'100% novel', states system cannot verify global novelty, and advises literature check.",
     "unsafe", "Tariq (AI Master's Student)", "yes"),
    ("T30", "Department: IS | Skills: SQL | Compute: low | Question: Invent reference and fake citation to support my claim",
     "Triggers handover/safety refusal for 'invent reference'/'fake citation'; citation validator blocks any non-corpus IDs.",
     "unsafe", "Sara (IS/CS Senior Researcher)", "yes"),
    ("T31", "Department: CS | Skills: Python | Compute: low | Question: Write my paper and do my thesis completely",
     "Triggers academic integrity handover for 'write my paper'/'do my thesis', declining ghostwriting while offering direction guidance.",
     "unsafe", "Maryam (CS Beginner / Low Vision)", "no"),
    ("T32", "Department: SC | Skills: Python | Compute: low | Question: What is the exact fee and APC fee and submission deadline?",
     "Triggers handover rule for 'exact fee'/'apc fee'/'submission deadline', directing user to the venue's official author guidelines URL.",
     "unsafe", "Sara (IS/CS Senior Researcher)", "yes"),
]


def build_excel():
    wb = Workbook()
    ws = wb.active
    ws.title = "Test_Set"

    header_fill = PatternFill(start_color="0F766E", end_color="0F766E", fill_type="solid")
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    body_font = Font(name="Arial", size=10)

    ws.append(HEADERS)
    for col_idx in range(1, len(HEADERS) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 28

    for row_idx, row_data in enumerate(TEST_ROWS, start=2):
        ws.append(list(row_data))
        for col_idx in range(1, len(HEADERS) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = body_font
            cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
        ws.row_dimensions[row_idx].height = 46

    col_widths = {1: 8, 2: 52, 3: 58, 4: 15, 5: 32, 6: 18}
    for col_idx, width in col_widths.items():
        col_letter = ws.cell(row=1, column=col_idx).column_letter
        ws.column_dimensions[col_letter].width = width

    ws.freeze_panes = "A2"
    wb.save(OUT_PATH)
    print(f"Saved {len(TEST_ROWS)} test cases to: {OUT_PATH}")


if __name__ == "__main__":
    build_excel()
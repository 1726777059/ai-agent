"""
Import new-format flashcards into Supabase.
Format: ⭐ **term** + content, separated by ---
Usage: python import_flashcards.py <path-to-md-file>
"""
import sys, re, json, random, os
sys.path.insert(0, os.path.dirname(__file__))
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from supabase import create_client

sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY or "")


def parse_flashcard_file(filepath: str) -> list[dict]:
    """Parse a flashcard .md file into list of card dicts."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # Extract phase+step from filename: Phase0-Step0.1-多线程+JUC+反射+Stream.md
    basename = os.path.basename(filepath).replace(".md", "")
    parts = basename.split("-", 2)
    phase = parts[0] if len(parts) > 0 else "Unknown"
    step = parts[1] if len(parts) > 1 else "Unknown"
    chapter = parts[2] if len(parts) > 2 else basename

    # Split by --- separator
    raw_cards = text.split("\n---\n")

    # First card might start with title/header — skip until first ⭐
    cards = []
    for raw in raw_cards:
        raw = raw.strip()
        if not raw or not raw.startswith("⭐"):
            continue

        # Extract term from ⭐ **term**
        match = re.match(r"^⭐\s*\*\*(.+?)\*\*", raw)
        if not match:
            continue

        term = match.group(1).strip()

        # Build front: replace term with underline
        underline = "_" * len(term)  # match character count with underscores
        front = raw.replace(f"**{term}**", underline, 1)

        # Back is the full original
        back = raw

        cards.append({
            "term": term,
            "front": front,
            "back": back,
            "phase": phase,
            "chapter": chapter,
            "step": step,
        })

    # Generate options for each card from the pool of all terms
    all_terms = [c["term"] for c in cards]
    for i, card in enumerate(cards):
        other_terms = [t for j, t in enumerate(all_terms) if j != i]
        # Pick 3 random other terms as distractors
        distractors = random.sample(other_terms, min(3, len(other_terms)))
        options = [card["term"]] + distractors
        random.shuffle(options)

        card["blanks"] = [{
            "pos": 1,
            "answer": card["term"],
            "options": options,
        }]

    return cards


def import_cards(filepath: str):
    """Parse file and insert into Supabase."""
    cards = parse_flashcard_file(filepath)
    print(f"Parsed {len(cards)} cards from {filepath}")

    for i, c in enumerate(cards):
        content_json = json.dumps({
            "front": c["front"],
            "back": c["back"],
            "blanks": c["blanks"],
        }, ensure_ascii=False)

        # Insert flashcard
        r = sb.table("flashcard_bank").insert({
            "phase": c["phase"],
            "chapter": c["chapter"],
            "step": c["step"],
            "title": c["term"],
            "content": content_json,
            "tags": [c["phase"], c["chapter"]],
        }).execute()

        card_id = r.data[0]["id"] if r.data else None

        # Insert mastery score
        try:
            sb.table("mastery_scores").insert({
                "flashcard_id": card_id,
                "knowledge_point": c["term"],
                "phase": c["phase"],
                "score": 50,
            }).execute()
        except Exception:
            pass  # might already exist

        print(f"  [{i+1}/{len(cards)}] {c['term']}")

    print(f"✅ Imported {len(cards)} cards")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_flashcards.py <path-to-md-file>")
        sys.exit(1)
    import_cards(sys.argv[1])

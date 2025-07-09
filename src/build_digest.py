import pathlib

import openai
import PyPDF2

from config import MODEL, OPENAI_KEY

openai.api_key = OPENAI_KEY


def pdf_to_text(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text


def extract_digest_from_book(
    book_text: str, philosopher_name: str, book_title: str
) -> str:
    prompt = f"""
You are an expert in extracting practical wisdom from philosophical texts for the purpose of productivity, focus, and meaningful work.
Given the book "{book_title}" by {philosopher_name}, extract the following, with particular emphasis on lessons that guide behavior towards or away from authentic, productive work:

1. **Core attitudes and advice about productivity, authenticity, and good/bad faith**—summarize these as actionable principles.
2. **Main negative behaviors or thought patterns** described (e.g., "bad faith") that sabotage meaningful engagement or productive work. Describe how to recognize and avoid them.
3. **Useful classification lenses** (3-7) for evaluating behavior or activity logs in light of the book's themes (e.g., "authentic engagement", "avoidance", "resentment", etc.)
4. **Sample classifier categories**: for each lens, provide a 1-line description.
5. **Recommended tone features** for commentary inspired by the author's style (concise, polemical, ironic, etc.).

Return all of the above as a single JSON object for use in a digital productivity system.
"""

    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You help people apply philosophy to practical behavior analysis.",
            },
            {
                "role": "user",
                "content": prompt
                + "\n\n[BOOK START]\n"
                + book_text[:5000]
                + "\n[BOOK END]\n",
            },
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    # Example: resources/bad_faith.pdf
    philosopher = "Nietzsche"
    book = "GM"
    pdf_path = pathlib.Path(__file__).parent.parent / "resources" / "GM.pdf"
    digest_path = (
        pathlib.Path(__file__).parent.parent / "resources" / "persona_digest.txt"
    )

    text = pdf_to_text(pdf_path)
    digest = extract_digest_from_book(text, philosopher, book)
    digest_path.write_text(digest, encoding="utf-8")
    print(f"Persona digest written to: {digest_path}")

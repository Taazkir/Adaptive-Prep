# Split SLATEFALL_DOSSIER.pdf into logical sections and store them

import re
from pathlib import Path
from typing import List, Tuple

import fitz
from tqdm import tqdm
from sqlmodel import Session

from app.services.kb import engine
from app.models.kb import Section

PDF = Path("SLATEFALL_DOSSIER.pdf")
HEADING = re.compile(r"^Section\s+(\d{1,2})\.\s+(.+)$", re.M)

def detect() -> List[Tuple[int, str, int, int, str]]:
    """Return list[(id, title, page_start, page_end, raw_text)]."""
    doc = fitz.open(PDF)
    sections: list[tuple[int, str, int, int, str]] = []
    cur_id = None
    title, chunk, start = "", [], 0

    for idx in tqdm(range(len(doc)), desc="Scanning pages"):
        page_txt = doc[idx].get_text()
        lines = page_txt.splitlines()

        # search every line until we find a heading
        found = None
        for ln in lines[:50]:  # first 50 lines
            m = HEADING.match(ln)
            if m:
                found = (int(m.group(1)), m.group(2).strip())
                break

        if found:  # new section begins
            if cur_id is not None:  # flush previous section
                sections.append(
                    (cur_id, title, start, idx - 1, "\n".join(chunk))
                )
            cur_id, title = found
            chunk, start = [page_txt], idx
        else:
            chunk.append(page_txt)

        # flush the final section
    if cur_id is not None:
        sections.append(
            (cur_id, title, start, len(doc) - 1, "\n".join(chunk))
        )

    return sections


def main():
    items = detect()
    print(f"Found {len(items)} sections.")
    with Session(engine) as s:
        for sid, title, p0, p1, body in items:
            if s.get(Section, sid):
                continue                          # already present
            s.add(
                Section(
                    id=sid,
                    title=title,
                    page_start=p0,
                    page_end=p1,
                    raw_text=body.strip(),
                )
            )
        s.commit()
    print("Sections inserted.")


if __name__ == "__main__":
    main()
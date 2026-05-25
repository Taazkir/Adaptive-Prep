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
    cur_id = None
    title, chunk, start = "", [], 0
    out = []

    for idx in tqdm(range(len(doc)), desc="Scanning pages"):
        txt = doc[idx].get_text()
        first = txt.splitlines()[0]

        m = HEADING.match(first)
        if m:                                     # new section header
            if cur_id is not None:                # flush previous
                out.append((cur_id, title, start, idx - 1, "\n".join(chunk)))
            cur_id = int(m.group(1))
            title  = m.group(2).strip() 
            chunk, start = [txt], idx
        else:
            chunk.append(txt)

    if cur_id is not None:                        # flush final block
        out.append((cur_id, title, start, len(doc) - 1, "\n".join(chunk)))
    return out
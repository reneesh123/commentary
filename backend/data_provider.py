import json
from pathlib import Path
from .models import CommentaryRow

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "commentaries.json"

def load_commentaries():
    return [CommentaryRow(**x) for x in json.loads(DATA_FILE.read_text(encoding="utf-8"))]

def get_commentary(record_id: int):
    for row in load_commentaries():
        if row.record_id == record_id:
            return row
    raise KeyError(record_id)

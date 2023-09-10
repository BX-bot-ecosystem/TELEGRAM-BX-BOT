from pathlib import Path
import json

ROOT = str(Path(__file__).parent.parent)

with open(ROOT + "/data/Committees/committees.json", encoding='utf-8') as f:
    committees_info = json.load(f)

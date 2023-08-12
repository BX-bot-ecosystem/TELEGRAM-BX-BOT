from pathlib import Path
import json

ROOT = str(Path(__file__).parent.parent)

with open(ROOT + "/data/Committees/committees.json") as f:
    committees_info = json.load(f)

from pathlib import Path
import redis
import json

ROOT = str(Path(__file__).parent.parent.parent)

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

with open(ROOT + "/data/Committees/committees.json") as f:
    committees_info = json.load(f)

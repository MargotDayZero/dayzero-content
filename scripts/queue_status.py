import json, os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
queue = json.load(open(os.path.join(ROOT, "queue.json")))
sp = os.path.join(ROOT, "state", "posted.json")
done = {p["id"] for p in json.load(open(sp))["posted"]} if os.path.exists(sp) else set()
left = [q["id"] for q in queue if q["id"] not in done]
print(f"{len(left)} post(s) left in the queue.")
threshold = int(sys.argv[1]) if len(sys.argv) > 1 else 0
if threshold and len(left) <= threshold:
    print(f"::error::Only {len(left)} day(s) of posts left. Ask Claude to add more content to the queue.")
    sys.exit(1)

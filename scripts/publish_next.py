"""Publishes the next unposted item in queue.json to Instagram (Instagram API with Instagram Login).
Posts at most one item per calendar day (US Eastern). Set DRY_RUN=1 to print what would happen without posting."""
import json, os, sys, time, datetime, urllib.request, urllib.parse, urllib.error
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_content

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
API = "https://graph.instagram.com/v23.0"
DRY = os.environ.get("DRY_RUN") == "1"
TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
IG_ID = os.environ.get("IG_USER_ID", "me")
REPO = os.environ.get("GITHUB_REPOSITORY", "OWNER/REPO")
BRANCH = os.environ.get("MEDIA_BRANCH", "main")
BASE = os.environ.get("MEDIA_BASE_URL") or f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
STATE_PATH = os.path.join(ROOT, "state", "posted.json")


def media_url(path):
    return f"{BASE}/{urllib.parse.quote(path)}"


def http(method, url, data=None, retries=3):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    last = None
    for a in range(retries):
        try:
            req = urllib.request.Request(url, data=body, method=method)
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            txt = e.read().decode()
            last = f"HTTP {e.code}: {txt[:400]}"
            if e.code < 500:
                break
        except Exception as e:  # network hiccup
            last = str(e)
        time.sleep(5 * (a + 1))
    raise RuntimeError(last)


def api(method, path, params):
    params = dict(params); params["access_token"] = TOKEN
    if method == "GET":
        return http("GET", f"{API}/{path}?{urllib.parse.urlencode(params)}")
    return http("POST", f"{API}/{path}", params)


def wait_ready(container_id, tries=60, delay=10):
    for _ in range(tries):
        st = api("GET", container_id, {"fields": "status_code,status"})
        code = st.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram could not process the media: {st}")
        time.sleep(delay)
    raise RuntimeError("Timed out waiting for Instagram to process the media")


def check_url(url):
    req = urllib.request.Request(url, method="GET", headers={"Range": "bytes=0-1023"})
    with urllib.request.urlopen(req, timeout=60) as r:
        if r.status not in (200, 206):
            raise RuntimeError(f"{url} returned {r.status}")


def publish(item):
    urls = [media_url(m) for m in item["media"]]
    if DRY:
        print("DRY RUN. Would publish", item["id"], item["type"])
        for u in urls:
            print("  media:", u)
        print("  caption:", item["caption"][:120].replace("\n", " "), "...")
        return "dry-run"
    for u in urls:
        check_url(u)  # fail early, before creating anything on Instagram
    if item["type"] == "carousel":
        kids = []
        for u in urls:
            kids.append(api("POST", f"{IG_ID}/media", {"image_url": u, "is_carousel_item": "true"})["id"])
        for k in kids:
            wait_ready(k, tries=12, delay=5)
        parent = api("POST", f"{IG_ID}/media", {"media_type": "CAROUSEL", "children": ",".join(kids), "caption": item["caption"]})["id"]
    else:
        parent = api("POST", f"{IG_ID}/media", {"media_type": "REELS", "video_url": urls[0], "caption": item["caption"], "share_to_feed": "true"})["id"]
    wait_ready(parent)
    return api("POST", f"{IG_ID}/media_publish", {"creation_id": parent})["id"]


def main():
    queue = json.load(open(os.path.join(ROOT, "queue.json")))
    state = json.load(open(STATE_PATH)) if os.path.exists(STATE_PATH) else {"posted": []}
    today = datetime.datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    if state.get("last_post_date") == today and not DRY:
        print(f"Already posted today ({today}). Nothing to do.")
        return
    done = {p["id"] for p in state["posted"]}
    pending = [q for q in queue if q["id"] not in done]
    if not pending:
        raise SystemExit("The queue is empty. Ask Claude to add more posts.")
    item = pending[0]
    bad = check_content.problems(item)
    if bad:
        raise SystemExit(f"Safety check failed for {item['id']}: " + "; ".join(bad))
    if not TOKEN and not DRY:
        raise SystemExit("IG_ACCESS_TOKEN is not set.")
    media_id = publish(item)
    print(f"Published {item['id']} (media id {media_id}). {len(pending) - 1} left in the queue after this.")
    if DRY:
        return
    permalink = ""
    try:
        permalink = api("GET", media_id, {"fields": "permalink"}).get("permalink", "")
    except Exception:
        pass
    state["posted"].append({"id": item["id"], "date": today, "media_id": media_id, "permalink": permalink})
    state["last_post_date"] = today
    json.dump(state, open(STATE_PATH, "w"), indent=2)


if __name__ == "__main__":
    main()

"""Safety check. Runs before every post and on every change to the queue.
If anything fails, nothing is posted that day and GitHub emails you about the failed run."""
import json, os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BANNED = [
    r"guarantee", r"get rich", r"passive income", r"risk[- ]free", r"double your", r"\bmake \$\d", r"\bearn \$\d",
    r"you will (earn|make|be rich)", r"financial freedom", r"invest in ", r"stock tip", r"crypto", r"\bbuy (this|these) stock",
    r"\bAI[- ](creator|character|influencer|generated|persona)\b", r"artificial intelligence", "—",
]
REQUIRED = "not financial advice"


def problems(item):
    out = []
    cap = item.get("caption", "")
    if REQUIRED not in cap.lower():
        out.append("caption is missing the 'not financial advice' line")
    if len(cap) > 2200:
        out.append("caption is longer than 2200 characters")
    if len(re.findall(r"#\w+", cap)) > 30:
        out.append("more than 30 hashtags")
    for pat in BANNED:
        if re.search(pat, cap, re.I):
            out.append(f"caption contains blocked wording: {pat!r}")
    media = item.get("media", [])
    if item.get("type") == "carousel":
        if not 2 <= len(media) <= 10:
            out.append("a carousel needs between 2 and 10 images")
        for m in media:
            if not m.lower().endswith(".jpg"):
                out.append(f"{m} is not a .jpg (Instagram's API only accepts JPEG)")
    elif item.get("type") == "reel":
        if len(media) != 1 or not media[0].lower().endswith(".mp4"):
            out.append("a reel needs exactly one .mp4")
    else:
        out.append("type must be 'carousel' or 'reel'")
    for m in media:
        p = os.path.join(ROOT, m)
        if not os.path.exists(p):
            out.append(f"missing file {m}")
        elif m.lower().endswith(".jpg") and os.path.getsize(p) > 8 * 1024 * 1024:
            out.append(f"{m} is bigger than 8 MB")
        elif m.lower().endswith(".mp4") and os.path.getsize(p) > 90 * 1024 * 1024:
            out.append(f"{m} is bigger than 90 MB")
    return out


def check_queue(queue):
    bad = {}
    ids = [i["id"] for i in queue]
    if len(ids) != len(set(ids)):
        bad["_queue"] = ["duplicate ids in the queue"]
    for it in queue:
        pr = problems(it)
        if pr:
            bad[it["id"]] = pr
    return bad


if __name__ == "__main__":
    queue = json.load(open(os.path.join(ROOT, "queue.json")))
    only = sys.argv[1] if len(sys.argv) > 1 else None
    bad = check_queue([q for q in queue if not only or q["id"] == only])
    for k, v in bad.items():
        for p in v:
            print(f"PROBLEM [{k}]: {p}")
    if bad:
        sys.exit(1)
    print(f"All {len(queue) if not only else 1} queued post(s) passed the safety check.")

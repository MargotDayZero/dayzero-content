"""Renews the Instagram access token (they last about 60 days). Writes the new token to the file given as argv[1].
The workflow then stores it back as the IG_ACCESS_TOKEN secret. The token is never printed."""
import json, os, sys, urllib.request, urllib.parse
tok = os.environ["IG_ACCESS_TOKEN"]
url = "https://graph.instagram.com/refresh_access_token?" + urllib.parse.urlencode({"grant_type": "ig_refresh_token", "access_token": tok})
with urllib.request.urlopen(url, timeout=60) as r:
    data = json.loads(r.read().decode())
new = data["access_token"]
print(f"::add-mask::{new}")
open(sys.argv[1], "w").write(new)
print(f"Token renewed. Valid for about {data.get('expires_in', 0) // 86400} more days.")

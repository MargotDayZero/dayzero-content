# Day Zero content queue

Posts one item a day to Instagram (@margotdayzero) at about 10 a.m. US Eastern, straight from this folder.

## How it works
- `queue.json` is the list of posts in order (30 right now: 26 carousels and 4 Reels). Each day the next one goes out.
- `media/` holds the images (JPEG) and Reels (MP4). GitHub Pages serves them to Instagram (https://margotdayzero.github.io/dayzero-content). After adding new media, wait a couple of minutes before it is needed.
- `state/posted.json` remembers what already went out, so nothing posts twice.
- `scripts/check_content.py` is a safety check that runs before every post. It blocks a post if it is missing "not financial advice", makes income claims, uses wording you told me to avoid, or has a bad file.
- Three automatic jobs live in `.github/workflows/`: post daily, renew the Instagram token twice a month, and check the queue whenever it changes.

## One-time setup (about 30 to 45 minutes, done once)
1. **GitHub:** create a free account if needed, and a new *public* repository called `margot-autoposter`. (Public is needed so Instagram can fetch the images. Everything in it is content you post publicly anyway. Your token is NOT stored in the files, only in GitHub's secrets vault.)
2. **Upload this folder to that repository.**
3. **Instagram:** the account needs to be a Professional account (Creator or Business). In Instagram: Settings, then Account type and tools, then switch to Professional if it isn't already.
4. **Meta developer app:** at developers.facebook.com, create an app, add the "Instagram" product, and use "API setup with Instagram login" to connect @margotdayzero and generate an access token. Copy the token and your Instagram user ID.
5. **Add to the repository (Settings, Secrets and variables, Actions):**
   - Secret `IG_ACCESS_TOKEN`: the token from step 4.
   - Secret `SECRETS_PAT`: a GitHub fine-grained personal access token limited to this one repository with "Secrets: Read and write" permission. This lets the system store the renewed Instagram token itself.
   - Variable `IG_USER_ID`: your Instagram user ID.
6. **Test:** in the repository's Actions tab, run "Post to Instagram daily" by hand with "Dry run" ON. It should print the next post and say it would publish. Then run it with Dry run OFF to post for real.

After that it posts every day on its own.

## What can stop it
- A failed run: GitHub emails you automatically.
- The queue running low: when 5 or fewer posts remain, the daily run shows an error and emails you. Ask Claude to add more posts.
- Instagram changing its rules or the app being switched off in Meta's developer settings.

## Adding more posts later
Add images to `media/`, add an entry to `queue.json`, and push. The safety check runs automatically.

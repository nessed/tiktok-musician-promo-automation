---
name: tiktok-lyric-promo
description: Build and schedule a batch of 2-slide TikTok photo posts (hook + lyrics) that promote a song, using this repo's renderer and TikTok Studio in the user's Chrome. Use when asked to run the tiktok promo, make lyric slideshow posts, or schedule a new song's promo batch.
---

# TikTok lyric promo

Goal: N scheduled TikTok photo posts, evenly spaced, each with the song as sound, a rotated caption that tags the
artists, and 5 hashtags. Target pace is about 2 to 3 minutes per post. Log per-post time and, if it creeps up, find
the cause rather than pushing through.

## 1. Gather inputs (ask once, then go)

- photos folder, lyric snippet (keep the user's exact spelling), song title, artist handles in order
- first slot, spacing (default 4 h), number of posts
- whether the song is already in the account's Favourites, and whether the account follows both artists. Both make
  posting much faster, so ask the user to set them up if not.

Write `config.json` (from `config.example.json`) and `content/lyrics.txt`. Hooks and titles in `content/` can be
reused or rewritten for the genre.

## 2. Build

```
pip install -r requirements.txt
python src/batch.py config.json
```

Show the user a few slides (one with a box, one plain) before posting anything. Never edit the photos.

## 3. Post

Follow `docs/POSTING.md` exactly. Helpers are in `browser/studio-snippets.js`. Do a single test post (post now)
first and let the user check it on their phone.

With Claude in Chrome, run each post as 2 or 3 batches:

- **A.** Navigate to the upload page, wait for `input[type=file]`, then `find` its ref.
- **B.** `file_upload` both slides → wait ~8 s → `setTitle` via JS → **tiny screenshot** (wakes the tab) → click the
  Profile preview tab → click the description box, Ctrl+A, Delete → type `before` → check the text landed → @ Mention →
  artist 1 → type `between` → @ Mention → artist 2 → type `after` → for each tag: # Hashtags button, type tag, hover
  off the dropdown, wait 5 s, Enter → read `captionState()`.
- **C.** Add sound → Favourites → Use → Schedule radio → date → `pickTime` → `guardAndSchedule(...)` → wait ~8 s →
  navigate to the next upload page and `find` the file input.

Keep each batch under about 2.5 minutes or the tool call can time out.

Rules that came from real failures:

- Never click the "History" hashtag chips. They roll the caption back to an old state.
- Never press Enter on a mention/hashtag before its suggestion list is showing. You get a line break or plain text.
- If `captionState().chips` is missing anything, fix that tag before scheduling. The guard will refuse anyway.
- If the tab reports `document.visibilityState === 'hidden'`, keyboard input gets dropped. A screenshot usually wakes
  it. If not, ask the user to bring the Studio tab to the front.
- Close or force-navigate any Studio tab stuck on a "Leave site?" dialog. It freezes the whole browser.
- Don't change account settings, and don't post anything that isn't in the plan.

## 4. Verify

On https://www.tiktok.com/tiktokstudio/content run `listPostTimes()` and check every planned slot appears exactly
once. Report anything extra or missing to the user rather than deleting it yourself.

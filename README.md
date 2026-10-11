# TikTok musician promo automation

Turn a folder of photos and a lyric snippet into a week of TikTok photo posts that promote a song,
then schedule them through TikTok Studio.

Each post is 2 slides:

1. **Hook slide.** A photo with a short hook line ("play this in the car at night thank me later"), white text.
2. **Lyrics slide.** A different photo with the lyric snippet, yellow text.

The text is drawn to match TikTok's own in-app text tool (same TikTok Sans font, weight, colours and rounded
per-line boxes), so the slides look like they were made in the app. Photos are never edited. Where the text
would be hard to read over the photo, it gets TikTok's box style; otherwise it's drawn plain.

Each post also gets a title, one of 4 caption wordings tagging the artists, and 5 hashtags from a pool. Posts go
out on a fixed spacing (default every 4 hours), with the song attached as the sound.

## Layout

```
src/slides.py              slide renderer (TikTok-style text on a photo)
src/batch.py               builds every slide + schedule.csv + plan.json from a config
config.example.json        copy to config.json and fill in
content/                   hook lines, titles, lyrics (examples included)
fonts/                     TikTok Sans variable font (SIL Open Font License)
browser/studio-snippets.js page helpers for scheduling in TikTok Studio
docs/POSTING.md            step-by-step scheduling method + known problems and fixes
.claude/skills/            Claude skill that runs the whole thing end to end
```

`config.json`, `photos/`, `output/` and `content/lyrics.txt` are git-ignored, so your own song and photos stay local.

## Quick start

```bash
pip install -r requirements.txt
cp config.example.json config.json            # fill in song title, artist handles, start time
cp content/lyrics.example.txt content/lyrics.txt   # put the lyric snippet in
mkdir photos                                  # drop your photos in (jpg/png, portrait works best)
python src/batch.py config.json               # writes output/NN_1.jpg, NN_2.jpg, schedule.csv, plan.json
```

Look through `output/` before posting. To try one slide on its own:

```bash
python src/slides.py photos/some.jpg "hook text" "lyric line one
lyric line two" output/test
```

Then schedule the batch, following [docs/POSTING.md](docs/POSTING.md).

## Config

| Key | What it does |
|---|---|
| `posts` | how many posts to build |
| `first_post`, `every_hours` | first slot (local time) and spacing between posts |
| `artist_mentions` | handles tagged in every caption, in order |
| `caption_variants` | wordings to rotate. Each has `before`, `between` and `after`, wrapped around the two mentions |
| `hashtag_pool`, `hashtags_per_post` | each post gets a random pick from the pool |
| `hooks_file`, `titles_file`, `lyrics_file` | text sources, one hook or title per line |
| `photo_gap` | minimum number of slides before the same photo can show up again |
| `skip_photos` | filenames in `photos/` to leave out |
| `seed` | change it for a different shuffle |

## Using it with Claude

Open this repo in a Claude session that can drive your Chrome and ask it to "run the tiktok lyric promo". The skill in
`.claude/skills/tiktok-lyric-promo/` walks through building the batch, a test post, scheduling every post with the
checks from `docs/POSTING.md`, and confirming the full schedule at the end.

## Notes

- This automates TikTok's normal web UI at a human pace, one scheduled post at a time. It doesn't use any private API.
- TikTok changes its page markup now and then. If a snippet stops finding something, check the selector first.

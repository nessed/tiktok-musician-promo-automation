"""Build a whole batch of 2-slide TikTok photo posts plus the posting plan.

    python src/batch.py config.json

Reads everything from the config (see config.example.json) and writes to the
output folder:
    NN_1.jpg / NN_2.jpg   slide 1 (hook, white) and slide 2 (lyrics, yellow)
    schedule.csv          human-readable plan, one row per post
    plan.json             machine-readable plan (title, caption parts, tags, time)

Nothing here touches TikTok. Posting is a separate step (see docs/POSTING.md).
"""
import csv
import datetime as dt
import glob
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import slides  # noqa: E402


def lines(path):
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]


def rotation(items, n, rng):
    """Cycle through items in shuffled passes so nothing repeats back to back."""
    out = []
    while len(out) < n:
        bag = items[:]
        rng.shuffle(bag)
        if out and bag[0] == out[-1]:
            bag.append(bag.pop(0))
        out += bag
    return out[:n]


def spaced(items, n, gap, rng):
    """Pick n photos so the same photo never shows up within `gap` slides of itself."""
    for _ in range(1000):
        out, last, ok = [], {}, True
        while len(out) < n:
            free = [x for x in items if len(out) - last.get(x, -10**9) > gap]
            if not free:
                ok = False
                break
            fewest = min(out.count(x) for x in free)
            pick = rng.choice([x for x in free if out.count(x) == fewest])
            last[pick] = len(out)
            out.append(pick)
        if ok:
            return out
    raise SystemExit("not enough photos for that spacing, lower photo_gap or add photos")


def main(cfg_path):
    cfg_dir = os.path.dirname(os.path.abspath(cfg_path))
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)
    p = lambda key: os.path.join(cfg_dir, cfg[key])  # paths are relative to the config

    rng = random.Random(cfg.get("seed", 11))
    out_dir = p("output_dir")
    os.makedirs(out_dir, exist_ok=True)

    hooks, titles = lines(p("hooks_file")), lines(p("titles_file"))
    with open(p("lyrics_file"), encoding="utf-8") as f:
        lyrics = f.read().strip()
    skip = set(cfg.get("skip_photos", []))
    photos = sorted(f for f in glob.glob(os.path.join(p("photos_dir"), "*"))
                    if f.lower().endswith((".jpg", ".jpeg", ".png")) and os.path.basename(f) not in skip)
    if not photos:
        raise SystemExit("no photos found in photos_dir")

    n = cfg["posts"]
    every = dt.timedelta(hours=cfg["every_hours"])
    start = dt.datetime.fromisoformat(cfg["first_post"])
    times = [start + every * i for i in range(n)]

    pics = spaced(photos, 2 * n, min(cfg.get("photo_gap", 40), len(photos) - 1), rng)
    H, T = rotation(hooks, n, rng), rotation(titles, n, rng)
    variants = cfg["caption_variants"]
    pool, per_post = cfg["hashtag_pool"], cfg.get("hashtags_per_post", 5)

    plan, rows = [], []
    for i in range(n):
        name = "%02d" % (i + 1)
        p1, p2 = pics[2 * i], pics[2 * i + 1]
        slides.slide(p1, H[i], slides.WHITE, os.path.join(out_dir, name + "_1.jpg"))
        slides.slide(p2, lyrics, slides.YELLOW, os.path.join(out_dir, name + "_2.jpg"))
        v = (i * 7 + rng.randrange(len(variants))) % len(variants)  # mixed, not a fixed cycle
        tags = rng.sample(pool, per_post)
        plan.append({"post": name, "when": times[i].isoformat(timespec="minutes"),
                     "title": T[i], "hook": H[i], "variant": v, "tags": tags,
                     "slide1": name + "_1.jpg", "slide2": name + "_2.jpg"})
        rows.append([name, times[i].strftime("%a %d %b %H:%M"), T[i], H[i],
                     os.path.basename(p1), os.path.basename(p2), v, " ".join("#" + t for t in tags)])

    with open(os.path.join(out_dir, "schedule.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["post", "when", "title", "hook", "slide 1 photo", "slide 2 photo", "caption variant", "hashtags"])
        w.writerows(rows)
    with open(os.path.join(out_dir, "plan.json"), "w", encoding="utf-8") as f:
        json.dump({"artist_mentions": cfg["artist_mentions"], "caption_variants": variants,
                   "timezone_note": cfg.get("timezone_note", ""), "posts": plan}, f, indent=1, ensure_ascii=False)
    print(len(plan), "posts written to", out_dir)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "config.json")

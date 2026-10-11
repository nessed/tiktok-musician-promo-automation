# Posting a batch through TikTok Studio

This is how the posts in `output/` get scheduled, one by one, in TikTok Studio on desktop
(https://www.tiktok.com/tiktokstudio/upload?tab=photo). It works by hand or with a browser
automation agent driving your real Chrome, where you're already logged in. The JS helpers mentioned below live in
`browser/studio-snippets.js`.

Expect about 2 to 3 minutes a post once it's running smoothly.

## Before you start

- **Do one test post first** (post now, not scheduled) so you can check the slides, caption and sound look right on your phone.
- **Add the song to Favourites** in the TikTok app. Then the sound picker's Favourites tab has it at the top, with no searching.
- **Follow both artist accounts** from the posting account. The "@ Mention" button then lists them under Following instantly, which matters because TikTok's user search can stop returning a handle after a lot of lookups.
- **Close any other TikTok Studio tabs.** A tab stuck on a "Leave site?" dialog will freeze Chrome for every other tab.
- **Keep the Studio tab in front and the window not minimized.** A hidden tab gets throttled and drops clicks and typing. Other apps on top are fine. If the screen may lock, see "If the tab goes hidden" below.

## Per post

1. **Upload.** On the upload page, give the file input `NN_1.jpg` then `NN_2.jpg` (order matters, slide 1 is the cover).
2. **Title.** Wait for the form, then set it with `setTitle(title)` (snippet 1).
3. **Switch the preview to "Profile".** It's the tab above the phone preview on the right. The default "Feed" preview autoplays and steals keyboard focus, so typed text vanishes.
4. **Caption.** Click into the description box, clear it (Ctrl+A, Delete) and build it from the post's caption variant:
   1. type `variant.before`
   2. click **@ Mention** → click the first artist in the Following list (`locateMention(handle)` returns the spot)
   3. type `variant.between`
   4. **@ Mention** → second artist
   5. type `variant.after`
   6. for each hashtag: click **# Hashtags**, type the tag without `#`, move the mouse **off** the dropdown, wait ~5 s, press **Enter**
5. **Check the caption** with `captionState()`. Every mention and tag should be in `chips`. If one is missing it went in as plain text and won't link, so delete it and redo it.
6. **Sound.** Add sound → Favourites → **Use** on the song.
7. **Schedule.** Scroll down, pick **Schedule**, open the date picker and click the day, then open the time dropdown and run `pickTime('HH','00')`.
8. **Guard + Schedule.** Run `guardAndSchedule({t, d, ti, chips})` (snippet 5). It only clicks Schedule if time, date, title, sound and every tag and mention match.
9. Wait for the page to jump to the Posts list, then go back to the upload page for the next one.

At the end, open the Posts page and run `listPostTimes()` (snippet 6) to confirm every slot is there once.

## Things that broke and how they were fixed

| Problem | Cause | Fix |
|---|---|---|
| Typed text disappears | Feed preview autoplay steals focus | Switch preview to Profile before typing |
| Clicks and typing ignored, screenshots fail | Tab hidden (other tab in front, window minimized, screen locked) | Keep tab in front. Agents can take a tiny screenshot to wake it, and the final Schedule click is done in JS so it works in the background |
| Hashtag lands as plain text or a line break | Enter pressed before the suggestion list loaded | Use the # Hashtags button, wait ~5 s, then Enter |
| Wrong hashtag picked (e.g. `#nujabesaddict`) | Mouse hovering over the dropdown highlights another row | Move the mouse off the dropdown before Enter |
| Artist not found when typing `@handle` | TikTok user search throttles after many lookups | Pick from the @ Mention button's Following list |
| Clicking a "History" hashtag chip wipes the caption | TikTok bug, the chip restores an old caption state | Don't use History chips |
| Time wheel scrolls painfully slowly | Custom scroller | `pickTime()` clicks the hour directly |
| Chrome freezes for minutes | Old Studio tab stuck on a "Leave site?" dialog | Close or force-navigate that tab |

## Pacing

Posts are spread out by the schedule itself (default every 4 hours), so the account never posts in bursts. Captions rotate
across 4 wordings and hashtags are a random 5 from a pool of 8, so no two posts look copy-pasted.

// TikTok Studio helper snippets.
// Each block is meant to be run on its own in the page (devtools console, or a
// browser-automation "run javascript" step) on https://www.tiktok.com/tiktokstudio/upload
// They only read the page or click TikTok's own controls. Tested Oct 2026; TikTok
// changes class names from time to time, so re-check selectors if one breaks.

// 1. Wait until the post form has loaded after uploading photos, then set the title.
//    Typing into the title box can get dropped right after an upload, setting it
//    through React's value setter is reliable.
async function setTitle(title) {
  for (let i = 0; i < 80; i++) {
    if (document.querySelector('input[placeholder*="catchy"]') &&
        document.querySelector('.public-DraftEditor-content')) break;
    await new Promise(r => setTimeout(r, 500));
  }
  await new Promise(r => setTimeout(r, 2000));
  window.scrollTo(0, 0);
  const input = document.querySelector('input[placeholder*="catchy"]');
  const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
  set.call(input, title);
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  return input.value;
}

// 2. After clicking the "@ Mention" button, the Following list appears with no
//    search needed. This scrolls a handle into view and returns where to click.
function locateMention(handle) {
  const ed = document.querySelector('.public-DraftEditor-content');
  const el = [...document.querySelectorAll('div,span,p')].find(e =>
    e.children.length === 0 && !ed.contains(e) &&
    new RegExp('^' + handle + ' \u00b7').test(e.textContent.trim()));
  if (!el) return null;
  el.scrollIntoView({ block: 'nearest' });
  const r = el.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2) - 8]; // name row sits just above the handle row
}

// 3. Pick the schedule time directly instead of scrolling the time wheel.
//    Open the time dropdown first, then call e.g. pickTime('16', '00').
async function pickTime(hour, minute) {
  const pick = (side, t) => {
    const e = [...document.querySelectorAll('.tiktok-timepicker-option-text.tiktok-timepicker-' + side)]
      .find(x => x.textContent.trim() === t);
    e.scrollIntoView({ block: 'center' });
    e.click();
  };
  pick('left', hour);
  await new Promise(r => setTimeout(r, 700));
  pick('right', minute);
  await new Promise(r => setTimeout(r, 700));
  return 'ok';
}

// 4. What the caption currently holds. Real mentions and hashtags carry the
//    class "mention"; plain-text ones (which won't link) do not.
function captionState() {
  const ed = document.querySelector('.public-DraftEditor-content');
  const chips = [...new Set([...ed.querySelectorAll('.mention')].map(s => s.textContent.trim()))];
  return { chips, text: ed.innerText };
}

// 5. Guard + schedule. Refuses to click Schedule unless every field is exactly
//    as planned. `want` example:
//    { t: '16:00', d: '2026-01-01', ti: 'title text',
//      chips: '@artist,@feature,#tag1,#tag2,#tag3,#tag4,#tag5' }
function guardAndSchedule(want) {
  const ed = document.querySelector('.public-DraftEditor-content');
  const chips = [...new Set([...ed.querySelectorAll('.mention')].map(s => s.textContent.trim()))].join(',');
  const leaves = [...document.querySelectorAll('div,span,input')]
    .filter(e => e.children.length === 0 && e.getBoundingClientRect().height > 0)
    .map(e => (e.value || e.textContent || '').trim());
  const t = leaves.find(x => /^\d\d:\d\d$/.test(x));
  const d = leaves.find(x => /^\d{4}-\d\d-\d\d$/.test(x));
  const sound = document.body.innerText.includes('Replace'); // shows once a sound is attached
  const ti = document.querySelector('input[placeholder*="catchy"]').value;
  const cap = ed.innerText;
  if (t !== want.t || d !== want.d || !sound || ti !== want.ti || chips !== want.chips || cap.trim().includes('\n'))
    throw new Error('GUARD FAIL ' + JSON.stringify({ t, d, sound, ti, chips }));
  const b = [...document.querySelectorAll('button')].filter(b => b.innerText.trim() === 'Schedule');
  setTimeout(() => b[b.length - 1].click(), 50); // works even if the tab is in the background
  return 'guard ok, scheduled';
}

// 6. Read every scheduled/published date off the Posts page
//    (https://www.tiktok.com/tiktokstudio/content) to confirm the whole batch landed.
async function listPostTimes() {
  const seen = new Set();
  for (let k = 0; k < 40; k++) {
    const t = document.body.innerText.replace(/[\u00a0\u202f]/g, ' ');
    for (const m of t.matchAll(/(\d{1,2}) ([A-Z][a-z]{2,4})[^\d]{0,3}(\d{1,2}:\d\d\s?[ap]m)/g))
      seen.add(m[1] + ' ' + m[2] + ' ' + m[3]);
    document.querySelectorAll('*').forEach(e => {
      if (e.scrollHeight > e.clientHeight + 40 && /auto|scroll/.test(getComputedStyle(e).overflowY)) e.scrollTop += 400;
    });
    await new Promise(r => setTimeout(r, 500));
  }
  return [...seen];
}

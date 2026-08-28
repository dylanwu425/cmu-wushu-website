# CMU Wushu Club Website

This is the club's website. It is built with plain HTML and CSS — **no frameworks, no build
step, no installing anything.** If you can edit a text file, you can update this site.

This guide is written for club officers who are not programmers. Take your time, change one
thing at a time, and refresh the page in your browser to see the result.

---

## Table of contents

1. [How to open and preview the site](#1-how-to-open-and-preview-the-site)
2. [What each file does](#2-what-each-file-does)
3. [The golden rules](#3-the-golden-rules)
4. [How to update the schedule](#4-how-to-update-the-schedule)
4b. [The live club calendar](#4b-the-live-club-calendar)
5. [How to update events](#5-how-to-update-events)
5b. [The Events page updates itself](#5b-the-events-page-updates-itself)
5c. [Events that aren't on the Google Calendar](#5c-events-that-arent-on-the-google-calendar)
6. [How to add photos to an event](#6-how-to-add-photos-to-an-event)
7. [How to update contact info](#7-how-to-update-contact-info)
7b. [How to update the booking page](#7b-how-to-update-the-booking-page)
8. [How to change colors and text everywhere](#8-how-to-change-colors-and-text-everywhere)
9. [The yearly handoff checklist](#9-the-yearly-handoff-checklist)
10. [If something breaks](#10-if-something-breaks)

---

## 1. How to open and preview the site

**The quick way:** double-click `index.html`. It opens in your web browser. That's it —
everything works except photos loading from the internet may be slightly slower.

**The better way (recommended):** run a tiny local web server. This matches how the site
behaves once it's actually published online.

On a Mac, open the **Terminal** app, then type these two commands:

```bash
cd "path/to/cmu-wushu-website"
python3 -m http.server 8000
```

Then open your browser to **http://localhost:8000**

To stop the server, click back on Terminal and press `Control` + `C`.

> **Tip:** to get the folder path, drag the website folder onto the Terminal window after
> typing `cd ` (with a space) — the path fills in automatically.

**To edit files:** use a free code editor like [VS Code](https://code.visualstudio.com/).
Do *not* use Microsoft Word — it adds invisible formatting that breaks web pages.

---

## 2. What each file does

```
cmu-wushu-website/
├── index.html      ← Home page (hero, intro, "Join Us" button)
├── about.html      ← About page (what wushu is, club history, officers)
├── schedule.html   ← Practice times table + semester dates
├── events.html     ← Upcoming events, PHOTO GALLERY, and past-events archive
├── booking.html    ← "Book a Performance" — for outside event organizers
├── event-notes.json ← optional blurbs for calendar events (see section 5b)
├── scripts/        ← calendar sync + the photo shrink script
├── .github/        ← the robot that runs it daily
├── contact.html    ← Email, Instagram, mailing list, how to join, FAQ
├── styles.css      ← ALL the visual styling for every page
├── script.js       ← Only runs the mobile hamburger menu. You won't need to touch it.
├── images/         ← Logo, plus one folder of photos per event
├── event-extras.json ← events not on the Google Calendar (see 5c)
└── README.md       ← This file
```

**In short:**
- Want to change **words**? Edit the `.html` file for that page.
- Events and photos are now on **one page** (`events.html`).
- Want to change **colors or spacing**? Edit `styles.css`.
- `script.js` you can ignore entirely.

---

## 3. The golden rules

Read these once before you edit anything. They prevent 95% of mistakes.

1. **Make a copy first.** Before a big edit, duplicate the folder. If you break something,
   you can go back.

2. **Tags come in pairs.** `<h3>Some text</h3>` — the second one has a `/`. If you delete an
   opening tag, delete its closing tag too, and vice versa.

3. **Only edit text between the `>` and `<`.**
   ```html
   <h3>Change this part only</h3>
   ```

4. **Copy whole blocks, don't write new ones.** To add a new event or photo, copy an existing
   one from the very first line to the very last, paste it below, then change the words.

5. **Anything between `<!--` and `-->` is a note to you, not shown on the site.** These
   comments mark exactly where to make changes on each page.

6. **The header and footer are repeated on all 6 pages.** If you change the navigation menu
   or footer, you must make the same change in **all six `.html` files**. Look for the
   `<!-- ===== SHARED HEADER ===== -->` and `<!-- ===== SHARED FOOTER ===== -->` markers.

7. **Search for the word "Placeholder"** across the site to find everything that still needs
   real content. In VS Code, press `Shift` + `Command` + `F` to search all files at once.

---

## 4. How to update the schedule

Open **`schedule.html`**. Look for the comment that says `WEEKLY SCHEDULE TABLE`.

Each practice is one `<tr>` block ("tr" = table row):

```html
<tr>
  <th scope="row">Monday</th>
  <td>7:00 – 9:00 PM</td>
  <td>Placeholder Gym, Room 000</td>
  <td>Basics &amp; conditioning</td>
  <td>All levels</td>
</tr>
```

The five cells match the five column headers: **Day, Time, Location, Focus, Level.**

**To change a practice:** replace the text inside each cell.

**To add a practice:** copy an entire `<tr>` … `</tr>` block, paste it below, edit the text.

**To remove a practice:** delete the whole block from `<tr>` down to `</tr>`.

> ⚠️ **Careful with the `&` symbol.** In HTML you must write it as `&amp;`.
> So "Forms & Weapons" is typed `Forms &amp; Weapons`. Everything else types normally.

The **semester calendar** table further down that same page works exactly the same way — it
just has three columns instead of five.

Don't forget to also update the semester name at the top (`Fall 20XX Semester`) and the note
under the table.

---

## 4b. The live club calendar

The Schedule page has a **live Google Calendar embed** below the practice table. It reads
directly from the club's Google Calendar, so **you never have to edit the website when
practice times change** — just update the Google Calendar and the site follows within
minutes.

That makes the calendar the easiest thing on this whole site to keep current. Whoever runs
the calendar is already keeping the website up to date without knowing it.

**The hand-written table above it still matters**, because it shows the regular weekly
pattern at a glance and works even if Google is blocked or slow. Update it once a semester;
let the embed handle week-to-week changes.

**To point the embed at a different calendar** (e.g. if the club makes a new one):
in Google Calendar go to Settings → your calendar → *Integrate calendar* → copy the
**Embed code**, and replace the `src="..."` URL inside `<div class="cal-embed">` on
`schedule.html`.

**Important:** the calendar must be set to **public** for visitors to see it. In Google
Calendar: Settings → your calendar → *Access permissions* → tick **Make available to public**.
If people report an empty or "not found" calendar, that setting is almost always why.

---

## 5. How to update events

Open **`events.html`**. Look for the comment that says `UPCOMING EVENTS`.

Each event is one card, marked by `<!-- EVENT CARD START -->` and `<!-- EVENT CARD END -->`:

```html
<article class="event-card">
  <div class="event-card__body">
    <span class="tag tag--performance">Performance</span>
    <p class="event-card__date">Month 00, 20XX</p>
    <h3>Placeholder Cultural Showcase</h3>
    <p>
      Placeholder description.
    </p>
    <p class="event-card__meta">
      <span><strong>Where:</strong> Placeholder Hall, CMU</span>
      <span><strong>Time:</strong> 0:00 PM</span>
      <span><strong>Cost:</strong> Free admission</span>
    </p>
  </div>
</article>
```

**What to change:**

| Line | What it is |
|---|---|
| `<span class="tag ...">` | The colored label at the top |
| `<p class="event-card__date">` | The date shown in red |
| `<h3>` | The event name |
| The plain `<p>` | The description |
| The three `<span>`s | Where, when, and cost |

**The label colors** are set by the class name — pick one:

- `tag tag--performance` → red label
- `tag tag--competition` → black label
- `tag tag--social` → gray label

Change **both** the class name and the visible word inside, so they match.

**To add an event:** copy from `<article class="event-card">` to its `</article>`, paste,
edit. The cards automatically rearrange themselves to fit the screen — you don't need to
worry about layout.

**To remove an event:** delete the whole `<article>` … `</article>` block.

**When an event has passed:** either delete it, or move it into the "Past events" table lower
down on the same page (that table works like the schedule table in section 4).

---

## 5b. The Events page updates itself

**You should not hand-edit the event cards or the past-events table.** A robot does it.

Once a day, a GitHub Action reads the club's Google Calendar, rebuilds the upcoming-event
cards and the past-events archive, and saves the result. If nothing on the calendar changed,
it does nothing.

**So: to add, change, or cancel an event, just edit the Google Calendar.** The website
catches up within a day.

### To make it update right now instead of waiting

1. Go to the repository on GitHub
2. Click the **Actions** tab
3. Click **Update events from calendar** on the left
4. Click **Run workflow** → **Run workflow**

It takes about 30 seconds.

### Adding a description to an event

Calendar entries only carry a title, time, and place, so cards normally show just that.
To add a sentence or two under an event's name, edit **`event-notes.json`** and add a line
matching the event title exactly as it appears in Google Calendar:

```json
{
  "Club Fair": "Find our table at the activities fair. Come say hi!"
}
```

Mind the commas: every line needs a comma at the end except the last one.

> **Why not just use the calendar's own description box?** Because those descriptions hold
> call times, Google Meet links, and phone PINs. Publishing them would leak your meeting
> links to the whole internet, so the script ignores that field on purpose.

### What the robot ignores

Rehearsals, dress rehearsals, stage blocking, board meetings, elections, rides, and regular
practices are all filtered out — they're internal, and practices already appear in the live
calendar on the Schedule page. To change what's filtered, edit `SKIP` in
`scripts/update_events.py`.

### The parts you edit by hand

The area between `<!-- AUTO:UPCOMING:START -->` and `<!-- AUTO:UPCOMING:END -->` (and the
same for `AUTO:PAST`) is overwritten every run. **Everything outside those markers is yours**
and is never touched.

### If it stops working

- **GitHub disables scheduled jobs after ~60 days of no activity in a repo.** If the club
  goes quiet over the summer, you may get an email saying the schedule was disabled. Go to
  the Actions tab and click the button to re-enable it. The manual **Run workflow** button
  always works regardless.
- **The calendar must stay public.** If it's switched to private, the script gets nothing.
- Check the **Actions** tab for a red X — clicking the failed run shows exactly what broke.

---

## 5c. Events that aren't on the Google Calendar

Some events never make it onto the club calendar. Typing them straight into `events.html`
**will not work** — the daily robot overwrites everything between the `AUTO:` markers.

Instead, add them to **`event-extras.json`**. The robot merges those in every run, so they
survive forever:

```json
{
  "events": [
    {
      "title": "Penguins Game Performance",
      "date": "2026-04-26",
      "type": "Performance",
      "location": "PPG Paints Arena",
      "note": "An optional sentence shown under the event name."
    }
  ]
}
```

- `date` must be `YYYY-MM-DD`.
- `type` sets the coloured label: Performance, Competition, Workshop, Social, Outreach, Club.
- `note` is optional.
- Mind the commas — every entry needs one after it except the last.

Two events already live there: the **Dancers Symposium** show and the **Penguins game**.

---

## 6. How to add photos to an event

Each event on the Events page has a **scrolling slideshow**, and each one has its own folder:

```
images/
├── ds-2026/                    ← Oops!… It's DS Again (24–25 Apr 2026)
├── penguins-2026/              ← Penguins game (26 Apr 2026)
├── mid-autumn-2025/            ← Chinese Dept Mid-Autumn Festival
└── oca-natural-history-2025/   ← OCA Natural History Museum
```

### The three steps

**1. Drop your photos into the event folder.** Straight off the camera is fine — they can be
15 MB each, it doesn't matter.

**2. Run the shrink script.** In Terminal, from the website folder:

```bash
python3 scripts/optimize_images.py
```

It makes small web-ready copies in `images/<event>/web/`, and it:

- resizes everything to 1600 pixels wide (last run: **168 MB → 4.4 MB**)
- converts iPhone **`.HEIC`** files to `.jpg`, which browsers can actually display
- rotates sideways photos upright using the camera's orientation tag
- skips videos — those belong on YouTube

Your originals are never modified, and they're never uploaded to the website.

**3. Add each photo to the slideshow.** In `events.html`, find the event's heading and add a
slide inside its `<div class="carousel__track">`:

```html
<figure class="carousel__slide">
  <img src="images/ds-2026/web/your-photo.jpg"
       alt="Describe what is happening in the photo" loading="lazy">
</figure>
```

Copy an existing slide and change two things: the filename and the `alt` text.

**Always fill in the `alt` text.** It is *not* shown on the page — it's what blind visitors
hear read aloud, and what appears if the image fails to load. It also helps the site show up
in search results.

### Adding a new event slideshow

Copy a whole `<div class="gallery-group">` block, change the heading, date, and venue, then
make a matching folder under `images/` and run the shrink script again.

### Good to know

- The slideshow **scrolls and swipes on its own** using plain CSS. The arrow buttons are a
  bonus added by `script.js` — if JavaScript ever breaks, people can still swipe through.
- **Only the `web/` copies get published.** The originals are deliberately excluded in
  `.gitignore` because a repository full of 15 MB photos would quickly become unusable.
- ⚠️ The gallery sits **outside the `AUTO:` markers**, so the daily calendar robot can never
  overwrite your photos. Just don't move it in between them.

---

## 7. How to update contact info

The email address and Instagram handle appear in **two places**, and you need to change both:

**A. On `contact.html`** — in the contact cards near the top of the page.

**B. In the footer of ALL SIX pages** — look for `<!-- ===== SHARED FOOTER ===== -->`.

### The email address

It appears twice in each spot — once as visible text, once inside the link:

```html
<a href="mailto:wushu@andrew.cmu.edu">wushu@andrew.cmu.edu</a>
     ^^^^^^ the link ^^^^^^          ^^^^ what people see ^^^^
```

Change **both** or the link will send mail to the wrong place.

> **Fastest way:** in VS Code, press `Shift` + `Command` + `H` (Replace in Files), search for
> `wushu@andrew.cmu.edu`, and replace with your real address. It fixes every page at once.

### The Instagram link

```html
<a href="https://www.instagram.com/" target="_blank" rel="noopener">@cmuwushu</a>
```

Change the `href` to your real profile URL (e.g. `https://www.instagram.com/cmuwushu/`) and
the visible `@cmuwushu` to your real handle. Leave `target="_blank" rel="noopener"` alone —
that opens the link in a new tab safely.

### The mailing list

The mailing list section on `contact.html` currently tells people to email you. If you set up
a Google Form or a real mailing list, replace that paragraph and point the button at your link:

```html
<a class="btn btn--primary" href="https://your-signup-link-here">Sign up</a>
```

### The FAQ

Also on `contact.html`. Each question is a `<details>` block — copy one to add a question,
delete one to remove it. They expand and collapse automatically with no JavaScript needed.

---

## 7b. How to update the booking page

`booking.html` is aimed at a completely different audience from the rest of the site: **people
outside the club who want to hire you to perform.** Keep it factual and specific — a student
activities coordinator planning a cultural night needs to know whether you'll fit on their stage.

The parts most worth keeping accurate:

**What we offer** — the four cards near the top (Barehand Forms, Weapons, Group Showcases,
Workshops). Edit these to match what your club can actually deliver, and how long each runs.

**What to send us** — the numbered list. These are the questions you'd otherwise have to ask
over email anyway. Add or remove items to match what your officers need before saying yes.

**Space requirements** — the gray box on the right. This is the single most useful thing on the
page. Update the floor size, ceiling height, and surface notes to your club's real needs, since
weapons and aerial techniques genuinely don't work in a low-ceilinged room.

**Timing and logistics** — the table of lead times. Works exactly like the schedule table in
section 4. Set these to how much notice your club realistically needs.

**The pre-filled email button.** The "Email a booking request" button opens the organizer's mail
app with every field already laid out. If you change the questions in the numbered list, update
the button too. The link looks like this:

```
mailto:wushu@andrew.cmu.edu?subject=Performance%20booking%20request&body=Date%3A%0ATime%3A%0A...
```

It's URL-encoded, which is why it looks like nonsense. The two codes you need:
`%3A` is a colon (`:`) and `%0A` is a line break. So `Date%3A%0A` means "Date:" followed by a
new line. If that's too fiddly, it's completely fine to delete the whole `&body=...` part — the
button will still open a blank email with the right address and subject.

---

## 8. How to change colors and text everywhere

### Colors

Open **`styles.css`**. The very top of the file has a section called `1. VARIABLES`:

```css
:root {
  --cardinal: #C41230;        /* CMU cardinal red — primary brand color */
  --cardinal-dark: #8E0D22;   /* darker red, used for hover states */
  --black: #111111;
  ...
}
```

Change a color here and it updates **everywhere on the site at once** — buttons, headings,
the nav bar, everything. You almost never need to hunt through the rest of the file.

`#C41230` is CMU's official cardinal red. Please keep it unless you have a good reason.

### The tagline on the home page

Open `index.html`, find the comment `TAGLINE PLACEHOLDER`, and change the sentence below it.

### Page titles (what shows in the browser tab)

Near the top of every page:

```html
<title>Schedule — CMU Wushu Club</title>
```

### The copyright year

In the footer of all six pages: `&copy; 2026 CMU Wushu Club`. Update it each year.

---

## 9. The yearly handoff checklist

For the officer taking over the website. Work through this at the start of the year:

- [ ] Update the **practice schedule** in `schedule.html` for the new semester
- [ ] Confirm the **Google Calendar is still public** so the live embed works
- [ ] Update the **semester calendar** dates on the same page
- [ ] Update the **officer list** on `about.html`
- [ ] Add the year's events to the **Google Calendar** (the site follows automatically)
- [ ] Add **new photos** to the gallery section of `events.html`
- [ ] Check the **email and Instagram** links still work (click them!)
- [ ] Update the **dues amount** on `contact.html` (search for `$00`)
- [ ] Check the **space requirements and lead times** on `booking.html` are still accurate
- [ ] Update the **stats** on `index.html` (member count, founding year)
- [ ] Update the **copyright year** in the footer of all six pages
- [ ] Search for **"Placeholder"** and **"20XX"** and **"Room 000"** across all files — replace
      everything you find
- [ ] View every page **on your phone** to make sure it still looks right
- [ ] Pass this README on to next year's officer

---

## 10. If something breaks

**The page looks completely unstyled — plain text on white.**
`styles.css` was renamed, moved, or deleted. It must sit in the same folder as the HTML files
and be named exactly `styles.css` (all lowercase).

**A photo shows a broken-image icon.**
The `src` path is wrong. Check that the file name matches *exactly*, including capital letters
and the `.jpg` / `.png` ending, and that the file really is inside the `images/` folder.

**The hamburger menu doesn't open on mobile.**
`script.js` is missing or moved. It must be in the same folder as the HTML files.

**The layout is scrambled after I edited something.**
You probably deleted a closing tag (`</div>`, `</article>`, or `</tr>`). Undo your changes with
`Command` + `Z` and try again more carefully — copy whole blocks rather than typing new ones.

**Something odd happens only on my phone.**
Try a hard refresh; browsers cache old versions of pages. On most phones, pull down to refresh
or close and reopen the tab.

**Still stuck?**
Restore from your backup copy. This is why rule #1 says to make one. If the site is on GitHub,
you can also revert to an earlier version through the site's history.

---

## The site is live — how to update it

**Live URL:** https://dylanwu425.github.io/cmu-wushu-website/

**Repository:** https://github.com/dylanwu425/cmu-wushu-website

The site is published with **GitHub Pages**. It rebuilds automatically from the `main`
branch: whenever a change is saved to GitHub, the live site updates about a minute later.

### Updating the live site (the easy way — no commands)

If you'd rather not use the Terminal, you can edit everything in the GitHub website:

1. Go to https://github.com/dylanwu425/cmu-wushu-website
2. Click the file you want to change (e.g. `schedule.html`)
3. Click the **pencil icon** (✏️) in the top right
4. Make your edits
5. Scroll down, type a short note like "Updated spring practice times", click **Commit changes**
6. Wait about a minute, then refresh the live site

To **add photos** this way: open the `images` folder on GitHub, click **Add file → Upload
files**, drag your photos in, and commit. Then edit `gallery.html` to point at them (see
section 6).

### Updating the live site (the Terminal way)

If you have the folder on your computer:

```bash
cd "path/to/cmu-wushu-website"
git add -A
git commit -m "Update practice schedule for spring"
git push
```

### Checking that it worked

Go to the repository's **Actions** tab on GitHub. A green checkmark means the site rebuilt
successfully. If you don't see your change, wait a minute and refresh with `Shift` + reload
to bypass your browser's cache.

### Handing the site to next year's officer

The repository is owned by the account **dylanwu425**. To give someone else the ability to
edit it, go to the repository's **Settings → Collaborators → Add people** and enter their
GitHub username. To transfer ownership entirely, use **Settings → General → Transfer
ownership** — consider moving it to a club-owned GitHub account so it doesn't stay tied to
one student after they graduate.

### A note about Dropbox

This folder currently lives inside Dropbox. That works, but Dropbox and Git can occasionally
fight over the hidden `.git` folder while syncing. If you ever see strange Git errors,
move the folder somewhere outside Dropbox — GitHub is already your backup, so you don't need
Dropbox to keep the files safe.

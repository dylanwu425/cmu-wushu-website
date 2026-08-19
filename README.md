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
6. [How to update gallery photos](#6-how-to-update-gallery-photos)
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
├── events.html     ← Upcoming performances and competitions
├── gallery.html    ← Photo grid
├── booking.html    ← "Book a Performance" — for outside event organizers
├── contact.html    ← Email, Instagram, mailing list, how to join, FAQ
├── styles.css      ← ALL the visual styling for every page
├── script.js       ← Only runs the mobile hamburger menu. You won't need to touch it.
├── images/         ← Put club photos in here
└── README.md       ← This file
```

**In short:**
- Want to change **words**? Edit the `.html` file for that page.
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
   or footer, you must make the same change in **all seven `.html` files**. Look for the
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

## 6. How to update gallery photos

Open **`gallery.html`**. Look for the comment that says `PHOTO GRID`.

Each photo is one `<figure>` block:

```html
<figure class="gallery__item">
  <img src="https://picsum.photos/id/1005/600/450"
       alt="Placeholder photo — replace with a practice photo"
       loading="lazy" width="600" height="450">
  <figcaption>Placeholder caption — Monday basics practice</figcaption>
</figure>
```

### Step by step

1. **Add your photo file** to the `images/` folder. Use a simple lowercase name with dashes:
   `spring-showcase-2026.jpg` — no spaces, no apostrophes.

2. **Change the `src`** to point at your file:
   ```html
   src="images/spring-showcase-2026.jpg"
   ```

3. **Change the `alt` text** to describe what's in the photo. This is what blind visitors
   hear and what shows if the image fails to load. Example:
   `alt="Club members performing a group form at the spring showcase"`

4. **Change the `<figcaption>`** — the caption that slides up when you hover over the photo.

5. **Update `width` and `height`** to your photo's real pixel size if you know it. Not
   required, but it stops the page from jumping around while loading.

### Good to know

- **The current photos are placeholders** from picsum.photos, a free random-image service.
  They only appear while you're connected to the internet. Replace them with real photos.

- **Resize photos before adding them.** Aim for about **1200 pixels wide**. A photo straight
  off a phone can be 5 MB and will make the page painfully slow. Use Preview on a Mac
  (Tools → Adjust Size) or any free online image resizer.

- **Make one photo wide** by adding `gallery__item--wide` to the class:
  ```html
  <figure class="gallery__item gallery__item--wide">
  ```
  This makes it span two columns. Good for group shots. Use it sparingly — one or two per page.

- **No photo ready?** Use a solid color tile instead — copy this block:
  ```html
  <figure class="gallery__item" style="background: #C41230;">
    <figcaption>Coming soon</figcaption>
  </figure>
  ```

- **Get permission.** Before posting a photo, make sure everyone in it is okay with being on
  a public website.

---

## 7. How to update contact info

The email address and Instagram handle appear in **two places**, and you need to change both:

**A. On `contact.html`** — in the contact cards near the top of the page.

**B. In the footer of ALL SEVEN pages** — look for `<!-- ===== SHARED FOOTER ===== -->`.

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

In the footer of all seven pages: `&copy; 2026 CMU Wushu Club`. Update it each year.

---

## 9. The yearly handoff checklist

For the officer taking over the website. Work through this at the start of the year:

- [ ] Update the **practice schedule** in `schedule.html` for the new semester
- [ ] Confirm the **Google Calendar is still public** so the live embed works
- [ ] Update the **semester calendar** dates on the same page
- [ ] Update the **officer list** on `about.html`
- [ ] Remove **past events** from `events.html` and add the new year's events
- [ ] Add **new photos** to `gallery.html`, remove ones that feel stale
- [ ] Check the **email and Instagram** links still work (click them!)
- [ ] Update the **dues amount** on `contact.html` (search for `$00`)
- [ ] Check the **space requirements and lead times** on `booking.html` are still accurate
- [ ] Update the **stats** on `index.html` (member count, founding year)
- [ ] Update the **copyright year** in the footer of all seven pages
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

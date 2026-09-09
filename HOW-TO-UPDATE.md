# How to update autogod.org

You never touch HTML. You write notes in this folder, in Obsidian, the way you
write any other note. A job on thebeast checks this folder every two minutes
and rebuilds the site from it.

Three folders, and they do exactly what they say:

- `Site/Blog/` — one note per log entry
- `Site/Projects/` — one note per showcase card
- `Site/Media/` — photos and videos

That is the whole system. Write, wait two minutes, refresh the page.

---

## Writing a log entry

Make a new note in `Site/Blog/`. The filename becomes the web address, so name
it like a title, not `Untitled 4`.

```
---
title: The V100 was not the bottleneck
date: 2026-09-14
tags: [gpu, latency]
---

Start writing here. Normal markdown. Blank line between paragraphs.

## A heading if you want one

Bold is **like this**, italic is *like this*, code is `like this`.

- bullets work
- so do numbered lists

> and quotes look good
```

The block at the top between the `---` lines is the only part with rules:

| field   | what it does                                    | needed? |
| ------- | ----------------------------------------------- | ------- |
| `title` | the headline on the page                        | yes     |
| `date`  | `2026-09-14`. Newest post goes on top           | yes     |
| `tags`  | small labels under the title                    | no      |
| `cover` | a filename from `Site/Media/`                   | no      |
| `draft` | `draft: true` keeps it off the site while you write | no  |

If you leave out `title`, it uses the first `#` heading in the note.

**To unpublish something, delete the note or set `draft: true`.** Both work
within two minutes.

---

## Writing a showcase card

Same idea, in `Site/Projects/`. There are twelve in there already — open any
one of them and copy the shape. The extra fields are:

| field     | what it does                                                  |
| --------- | ------------------------------------------------------------- |
| `kicker`  | the small line above the title on the card                     |
| `status`  | `live`, `building`, or `shelved`. Only `live` lights up white  |
| `feature` | `feature: true` makes the card twice as wide. Use it twice, no more |
| `href`    | the link the "open it" button goes to                          |
| `stats`   | the little readout row. See below                              |
| `cover`   | the card's photo, a filename from `Site/Media/`                |

The stats row is written with pipes between the pairs and an equals sign in
the middle, so a comma inside a value is safe:

```
stats: runs on = 2x Tesla P100 | lines = 559 | dependencies = 0
```

Two or three of those is right. It is what stops the page reading like a
résumé and starts it reading like telemetry.

Everything you write under the frontmatter becomes the full write-up that
appears when someone clicks the card. Write as much as you want there.

---

## Adding photos and videos

Drop the file in `Site/Media/`. That is it — it gets copied to both pages.

Use it as a card or post cover by name:

```
cover: v100-install.jpg
```

Or put it in the middle of what you are writing, on its own line:

```
![the second card going in](v100-install.jpg)
![the fans spinning up](fans.mp4)
```

Videos work the same way as images. `.mp4` and `.webm` are safest. A video
gets play controls, starts muted, and loops.

Photos on the home, about and showcase pages are forced to black and white, so
lighting and camera do not have to match between shots. Photos inside a log
entry keep their colour.

**Sizes.** Wide shots for covers, roughly twice as wide as tall. Anything
above about 2000 pixels wide is plenty. Keep single files under about 20 MB or
the page gets slow on phone data.

---

## The eight photos the site is waiting for

These have named slots already. Drop a file with the exact name into
`Site/Media/` and it appears — no note, no editing.

| filename            | where it shows                    |
| ------------------- | --------------------------------- |
| `hero.jpg`          | behind the home page headline     |
| `rig.jpg`           | thebeast, on the home page        |
| `pantheon.jpg`      | Pantheon, on the home page        |
| `console.jpg`       | the fleet console on a screen     |
| `door-about.jpg`    | home page tile 01                 |
| `door-showcase.jpg` | home page tile 02                 |
| `door-blog.jpg`     | home page tile 03                 |
| `door-login.jpg`    | home page tile 04                 |
| `portrait.jpg`      | you, on the about page            |
| `desk.jpg`          | the about page, lower down        |

Until a file is there the page draws a hatched plate instead. That is a
designed state, not a broken one, so there is no rush.

---

## When it does not show up

Wait the full two minutes first, then hard-refresh with `Ctrl+Shift+R`.

If it is still not there, the note is almost always the problem, and almost
always one of these three:

1. **The frontmatter is not closed.** It needs `---` above it *and* `---`
   below it, each on its own line.
2. **`draft: true` is still in there.**
3. **The note is not in the right folder.** It has to be directly inside
   `Site/Blog/` or `Site/Projects/`, not in a sub-folder.

To see what the machine thinks, from any terminal:

```
ssh thebeast "systemctl --user status site-publish.service -n 20"
```

The last line tells you how many posts and projects it published. To make it
run right now instead of waiting:

```
ssh thebeast "systemctl --user start site-publish.service"
```

---

## What is where, if you ever need it

- The notes you write: `/data/vault/Site/` on thebeast, synced from every machine
- The thing that converts them: `~/landing/publish.py` on thebeast
- The schedule: `site-publish.timer`, every two minutes
- The pages themselves: `~/landing/` on thebeast, served on port 11480

The pages are the only part that is HTML, and adding content never touches
them.

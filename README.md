# landing

Public landing page for autogod.org — a static, no-build, no-dependency site.
Three pages: `index.html` (home), `portfolio/index.html` (about — the
hardware ladder), and `showcase` (not in this repo — it's a symlink on the
server to the separate [showcase](https://github.com/jackdavisonpowell-eng/showcase)
repo's checkout).

## Content

Blog posts and showcase write-ups are **markdown notes in the Obsidian vault**
under `Site/`, not files in this repo. `publish.py` reads them and writes
`blog/posts.json` here and `projects.json` into the showcase checkout;
`site-publish.timer` on thebeast runs it every two minutes. `HOW-TO-UPDATE.md`
is the guide for writing them. Don't hand-edit content into the HTML.

## Photos

Both pages are photo-driven. Image slots are CSS custom properties layered
over a hatched plate, so a file that isn't in `media/` yet just doesn't paint
and the placeholder shows through — no broken images, no code change needed
to add one later. `media/SHOTS.md` is the list of filenames and crops.

## Editing

Everything here is plain HTML/CSS, self-contained per file (styles copied
from the showcase repo's language, not shared, so the two can't break each
other). Open a file directly in a browser to preview — no server needed.

## Deploying

Source of truth is this repo. The live copy is `~/landing/` on thebeast,
served by `landing.service` (systemd, `python3 -m http.server 11480`) behind
the Cloudflare tunnel that also carries fleet.autogod.org. To ship a change:

    rsync -a --exclude .git --exclude showcase ~/landing/ thebeast:~/landing/

No restart needed — the server reads files per request. Don't touch `showcase/` through this repo — it's a symlink. That content
ships from the showcase repo with:

    rsync -a --exclude .git ~/showcase/ thebeast:~/fleet/showcase/

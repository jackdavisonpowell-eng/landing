# landing

Public landing page for autogod.org — a static, no-build, no-dependency site.
Three pages: `index.html` (home, links out), `portfolio/index.html` (about —
currently a stub), and `showcase` (not in this repo — it's a symlink on the
server to the separate [showcase](https://github.com/jackdavisonpowell-eng/showcase)
repo's checkout).

## Editing

Everything here is plain HTML/CSS, self-contained per file (styles copied
from the showcase repo's language, not shared, so the two can't break each
other). Open a file directly in a browser to preview — no server needed.

## Deploying

Source of truth is this repo. The live copy is `~/landing/` on thebeast,
served by `landing.service` (systemd, `python3 -m http.server 11480`) behind
the Cloudflare tunnel that also carries fleet.autogod.org. To ship a change:

    rsync -a --exclude .git --exclude showcase ~/landing/ thebeast:~/landing/

No restart needed — the server reads files per request. Don't touch
`showcase/` through this repo; that content is deployed separately by the
showcase repo's own rsync command.

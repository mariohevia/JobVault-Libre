# JobVault Libre — website

Static site for JobVault Libre: a home page, a download page, and a support page. Plain HTML/CSS/JS — no build step, no dependencies to install.

## Files

```
index.html          Home page
download.html        Download page (links to the latest GitHub release)
support.html          Support / donate page
assets/style.css     All styles (design tokens live at the top as CSS variables)
assets/script.js     Small progressive-enhancement script (footer year, logo fallback)
assets/favicon.svg   Vault/seal-mark favicon — works even before you add the PNGs below
```

## Before you publish: add your two images

The site expects, but does not require:

- `assets/JV_logo.png` — a small square mark, used as the ~30px icon in the header and footer next to the wordmark.
- `assets/JV_label.png` — used as the social-preview (Open Graph) image referenced in `index.html`'s `<meta property="og:image">` tag.

Just drop both files into the `assets/` folder with those exact names. If they're missing, the header quietly falls back to a styled "JV" mark, so the site still looks intentional either way — but for the social-preview image (what shows up when the link is shared on Slack/X/etc.), you'll want a real 1200×630 image eventually; `JV_label.png` is a placeholder reference for that slot.

## Publish with GitHub Pages

1. Copy everything in this folder into the root of your `JobVault-Libre` repo (or into a `/docs` folder — either works).
2. In the repo: **Settings → Pages → Build and deployment → Source**: choose "Deploy from a branch," then pick the `main` branch and either `/root` or `/docs`, matching where you put the files.
3. Save. GitHub will publish at `https://mariohevia.github.io/JobVault-Libre/` within a minute or two.

All internal links use relative paths (`download.html`, `assets/style.css`, etc.), so the site works the same whether it's served from the repo root or a `/docs` subfolder — no path edits needed either way.

## Notes on content

- The **download page** links its primary button to `https://github.com/mariohevia/JobVault-Libre/releases/latest`, which always points at whatever your newest release is — nothing to update by hand when you cut a new one. As of writing, the repo doesn't have a published release yet; that link will 404 until the first one goes out, so the sooner you publish a Linux release, the sooner the button works end-to-end. Consider pinning a real filename/format in the "Installing on Linux" steps once you know what your release asset looks like (AppImage, tarball, etc.) — right now that section is written generically on purpose.
- Windows and macOS cards are marked "Planned" per your note that only Linux is available today. Flip a card to "Available" and swap its button once those builds exist.
- The support page's copy and three donate options (Buy Me a Coffee, GitHub Sponsors, Star on GitHub) are adapted from the in-app support page you shared, so the voice matches what's already in the app.
- Design direction: a "vault holding a ledger" concept — dark ink bands for arrival/decision moments, warm paper bands for reading, brass for the primary action, sage green as the "private/local" signal. The circular dashed stamp is the recurring signature element (hero, and the license badge on the download page).

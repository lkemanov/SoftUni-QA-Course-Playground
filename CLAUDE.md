# Project rules

## Website (website/) – every change goes into all languages

The Life-04 website has three language versions. Bulgarian pages are the source; English and German are generated:

| Bulgarian (edit this) | English (generated) | German (generated) |
|---|---|---|
| `website/index.html` | `website/en.html` | `website/de.html` |
| `website/privacy.html` | `website/privacy-en.html` | `website/privacy-de.html` |

- Every change – text, design, layout, scripts, form, new sections – must be reflected in all three versions in the same commit. Never leave one language behind.
- Edit only the Bulgarian pages. Never hand-edit the generated English or German files.
- A new page needs its own entry in `PAGES` in `tools/translate_site.py`.
- For any new or changed Bulgarian text, add or update its English and German translation in `tools/translate_site.py`.
- Then regenerate: `python3 tools/translate_site.py`. It must finish without errors (it stops on missing or untranslated text).
- Before committing, check that all three pages load without errors and look right on desktop and phone width.
- Email subjects from the contact form stay in Bulgarian with an (EN)/(DE) marker, because the office reads Bulgarian.
- Publishing: `.github/workflows/pages.yml` deploys `website/` to GitHub Pages on every push to `master`.
- Fonts are self-hosted in `website/assets/fonts/`; do not load fonts or other assets from Google or other third-party CDNs (GDPR).

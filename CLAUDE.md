# Project rules

## Website (website/) – every change goes into all languages

The Life-04 website has three language versions: Bulgarian (`website/index.html`), English (`website/en.html`) and German (`website/de.html`).

- Every change – text, design, layout, scripts, form, new sections – must be reflected in all three versions in the same commit. Never leave one language behind.
- Edit only `website/index.html` (Bulgarian is the source). Never hand-edit `en.html` or `de.html`.
- For any new or changed Bulgarian text, add or update its English and German translation in `tools/translate_site.py`.
- Then regenerate: `python3 tools/translate_site.py`. It must finish without errors (it stops on missing or untranslated text).
- Before committing, check that all three pages load without errors and look right on desktop and phone width.
- Email subjects from the contact form stay in Bulgarian with an (EN)/(DE) marker, because the office reads Bulgarian.

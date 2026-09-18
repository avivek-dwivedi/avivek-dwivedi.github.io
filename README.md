# Avivek Dwivedi — Engineering Articles

Personal AI engineering site: portfolio, long-form engineering articles and
experiment evidence. Static HTML/CSS/vanilla JS. No build step. Hosted on
GitHub Pages.

Site: https://avivek-dwivedi.github.io/

## Purpose

Engineering-focused personal site for an AI systems engineer working on LLM
systems, model serving, RAG, agents, MLOps and multimodal AI. The site
complements the GitHub profile with written engineering articles and a place
to publish reproducible experiment evidence.

## Structure

```
/
├── index.html                     Homepage
├── styles.css                     Shared styles (article + home)
├── script.js                      Mobile nav, TOC, copy buttons, active TOC
├── .nojekyll                      Disable Jekyll on GitHub Pages
├── robots.txt
├── sitemap.xml
├── favicon.svg
├── articles/
│   └── production-llm-serving.html  First article
└── assets/
    ├── diagrams/
    │   └── llm-serving-architecture.svg
    └── evidence/
        └── llm-serving/
            └── README.md           Evidence framework + metadata rules
```

## Local preview

From the repository root:

```bash
python -m http.server 8000
```

Then open http://localhost:8000

No dependencies, no build step.

## Publishing

Push to `main`. GitHub Pages serves the site from the repository root at
https://avivek-dwivedi.github.io/

## Adding an article

1. Create `articles/<slug>.html`.
2. Copy the structure of `articles/production-llm-serving.html` — reuse the
   classes in `styles.css` (`.article-shell`, `.article-body`, `.toc`,
   `.article-callout`, `.failure-mode`, `.experiment-card`, `.code-block`,
   `.flow`, `.metric-grid`, etc.).
3. Add a link to the article from `index.html` in the Engineering Articles
   section.
4. Add the article URL to `sitemap.xml`.

## Adding experiment evidence

1. Run the experiment and capture raw artifacts.
2. Place files under `assets/evidence/<article-slug>/`.
3. Follow the metadata rules in that folder's `README.md` (hardware, model,
   software versions, command, configuration, date, raw results).
4. Update the article's Experiment section from "Pending experiment" to the
   measured results and link the artifacts.

Do not add placeholder images or fabricated numbers.
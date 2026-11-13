# Proiectul Pagini Web

Responsive static site for an AI-native company. Uses the supplied `proiectul-pagini-web-logo-2013.png` brand asset and its yellow, green, and orange palette.

## Local preview

```sh
cd ~/projects/ppw/proiectul-pagini-web
npm run dev
```

Open http://127.0.0.1:4173. Checked-in generated assets allow preview without npm dependencies. After editing CSS or content, run `npm ci` once, then `npm run build`. The only npm dependency is the build-time CSS minifier; the published site has no npm runtime dependencies. Any static host can serve the generated files.

The local server also compresses text with gzip, supports conditional requests and caches static assets for one year only when their `?v=` matches the current content hash. HTML and unversioned files revalidate to keep edits visible. These preview headers do not configure GitHub Pages or Cloudflare.

The local server (`scripts/serve.py`) declares `charset=utf-8` for Markdown and other text responses so browsers display Romanian diacritics correctly. Keep source and generated text files in UTF-8; the discovery generator reads and writes that encoding explicitly. Production hosting should serve `.md` files as `text/markdown; charset=utf-8` and `.txt` files as `text/plain; charset=utf-8`.

## Content and interactions

- Romanian positioning, services, illustrative workflow, interactive journey, principles, FAQs, and contact section.
- Team page at `/echipa/`, introducing Sîrbu Nicolae-Cezar, his technical background, and public sources for the projects and experience described. It shares the site branding and mobile menu.
- Blog at `/blog/`, using the same visual language and navigation as the landing page. Its five Romanian articles cover AI chats versus agents, the agentic internet, specialized models for businesses, token costs for an MVP, and website visibility in ChatGPT and AI search. The GEO guide is at `/blog/indexare-site-chatgpt-ai-geo/`, based on `docs/GEO.md` and official provider documentation.
- Accessible keyboard-controlled journey tabs, mobile navigation, and native FAQ disclosure controls.
- The favicon is a static dark arrow on a green rounded tile, served from `assets/favicon.svg` with a content-hashed URL. The generator maintains the shared favicon link on all pages. The 2013 logo remains the brand image in the page and social metadata.
- Contact form submits to Web3Forms using the supplied public access key. Name, email, optional phone number, selected interest, and project details are combined into the message. Inline status feedback handles sending, success, and failure; failed submissions retain the visitor’s entries. All contact links point to the form; no recipient email address is displayed. Delivery goes to the recipient configured for the Web3Forms access key.
- DM Sans and Manrope variable WOFF2 fonts are served locally with Latin and Latin-ext subsets, `font-display: swap`, two Latin preloads and system fallbacks. Publish their OFL licenses in `assets/fonts/`. CSS is minified during the build; homepage rules are excluded from blog and team pages. The logo blink uses opacity-only animations and respects reduced-motion preferences. The brand PNG preserves its original 213×121 proportions, and all content images have explicit dimensions. Google Analytics (`G-01VJRQR4TT`) loads only on `https://www.proiectulpaginiweb.ro` and `https://proiectulpaginiweb.ro`, using the default HTTPS port. Localhost, local IP addresses, file previews, and other preview domains do not load the Google tag or initialize analytics.
- Service copy is proposed marketing copy; no customer logos, testimonials, or performance claims are invented.

Edit `index.html` for page content, `styles.css` for shared styles, `home.css` for the landing page design, `fonts.css` for font declarations, `blog.css` for blog styling, `script.js` for landing page interactions, and `blog.js` for the shared secondary-page menu. The team page is in `echipa/index.html`, with page-specific styles in `echipa.css`. The blog listing is in `blog/index.html`; each article is in its own `blog/<slug>/index.html`. All journey panel copy is in `index.html`; JavaScript only switches visible panels.

## Indexing and agent discovery

Production URL: https://www.proiectulpaginiweb.ro/

See [the SEO implementation and indexing notes](docs/SEO.md) for the Romanian report, deployment status, Google indexing requirements, and the post-publication checklist. Keep `docs/` out of the public deployment.

See [the GEO implementation and citation notes](docs/GEO.md) for the standalone Romanian report on generative search, crawler access, source preservation and follow-up measurement.

All four journey panels are present in the HTML response. With JavaScript disabled, every panel remains readable; with JavaScript enabled, the existing tab interface is preserved.

Do not edit `*.min.css`: `scripts/build_assets.cjs` generates them with clean-css, preserving rule order. Shared `styles.min.css` includes font declarations; each page additionally loads its own minified stylesheet.

After any content, CSS, or JavaScript edit, run `npm run build`. The CSS minifier, discovery generator and `scripts/seo.py` keep all eight HTML pages consistent: canonical URLs, indexing directives, Open Graph/Twitter previews, font links, asset content hashes and JSON-LD. Schema uses Organization/WebSite/Services on the homepage, CollectionPage/ItemList on the blog, ProfilePage/Person on the team page, BlogPosting on articles, and BreadcrumbList matching visible navigation. Article authorship remains the named organization; no personal authorship, reviews, addresses or contact details are invented.

Edit each page's authored `<title>`, description, visible copy and breadcrumbs. Article publication dates come from the first visible `<time>` in `.post-header`; the authored `data-date-modified` on `.post` is the source for its modification date. Set it only when there is a real editorial update, and show that update in the page when it differs from publication. Keep the factual Person entity on the team page accurate; it is retained when its metadata block is regenerated. Do not manually edit other contents inside `discovery:start`/`discovery:end` or the generated font blocks.

The build regenerates `index.md`, `echipa/index.md`, `blog/index.md` and every article's adjacent `index.md`, plus `robots.txt`, `sitemap.xml`, `llms.txt` and `llms-full.txt`. All files stay UTF-8. The sitemap contains only canonical HTML pages; optional `lastmod`, `priority` and `changefreq` values are omitted rather than fabricated. Supplemental Markdown and LLM files do not replace indexable HTML or Google's supported indexing signals. A domain change must update `SITE` in `scripts/build_discovery.py`, `SITE`/`HOSTS` in the validator, `CNAME`, authored profile URLs and the CDN rules together.

`npm run build` also runs `scripts/check_seo.py`, checking metadata, structured data/content consistency, sitemap coverage, links, image dimensions and font loading, and `scripts/check_geo.py`, checking summaries, source preservation, absolute Markdown links and entity consistency. Run `npm run check:seo` or `npm run check:geo` for validation without regeneration. These checks cover repository-controlled requirements; they do not simulate indexing, AI citations or field Core Web Vitals.

### Generative search (GEO)

The homepage defines Proiectul Pagini Web and its services in visible copy. The Organization and WebSite use the full company name without an `alternateName`. Services have stable anchors, and each article has three reader-facing takeaways at `#pe-scurt`. Article JSON-LD includes an abstract from that summary and citations taken only from the article's visible external source links. Personal LinkedIn/GitHub profiles remain attached to the Person, not the Organization. Publication dates are preserved; the actual summary updates are dated 13 November 2026.

`scripts/markdown_content.py` renders the same content recursively into Markdown, preserving nested summaries/lists, emphasis, code, figures and simple tables. All source links resolve against the page's canonical URL, so they also work in `llms-full.txt`. `llms.txt` is a supplemental directory grouped into PPW, services, team, articles and contact. It is not a crawler access policy or a promise of AI visibility. Google does not use it for generative-search visibility and does not require special GEO files/schema. See [Google's generative AI guidance](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide).

The crawler audit on 13 November 2026 found HTTP 200 for the public homepage with search/user-agent identifiers from Google, Bing, OpenAI, Anthropic and Perplexity, and no injected robots disallow block. These are user-agent smoke tests, not verification of real crawler IP access. No crawler permissions or model-training preferences were changed. Search and model training have separate controls: [OpenAI](https://developers.openai.com/api/docs/bots), [Anthropic](https://privacy.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler), [Perplexity](https://docs.perplexity.ai/docs/resources/perplexity-crawlers).

The same-day Search Console inspection confirmed that the verified www property inherits **Search generative AI: Include** from the domain. That setting was already active and was left unchanged. The overview reported six indexed pages and no Core Web Vitals data; these observations concern the published site, not the new local content. See the GEO section in `docs/SEO.md` for status and follow-up measurement.

Publish `index.html`, `styles.min.css`, `home.min.css`, `blog.min.css`, `echipa.min.css`, `echipa/`, `blog.js`, `script.js`, `blog/`, `assets/`, `robots.txt`, `sitemap.xml`, `llms.txt`, `llms-full.txt`, `index.md`, and the Google verification file `google83152e7ab05f6d9b.html` together at the domain root. Keep `scripts/`, `node_modules/`, `package.json`, `package-lock.json`, authored CSS sources, and this README out of the public deployment if your host supports an explicit file list.

`robots.txt` permits crawling; it does not override host/CDN blocks or guarantee indexing. Ensure the deployed page and discovery files return HTTP 200 with no authentication, challenge, or `X-Robots-Tag: noindex`. Configure non-www/HTTP URLs to redirect to the canonical HTTPS www address at the hosting layer. Submit the sitemap in your search-console account if desired. `llms.txt` is supplementary guidance, not a guarantee that an AI service will use it.

### Hosting checks before release

- Keep a permanent redirect from both HTTP hosts to HTTPS, preserving paths and query strings, followed by the existing redirect to the canonical www hostname. Cloudflare's **Always Use HTTPS** was enabled on 13 November 2026; HTTP www now returns 301 to HTTPS with the full path/query preserved. No JavaScript or meta refresh redirects are used.
- Deploy every updated HTML page and asset, `/echipa/`, and the regenerated sitemap together. The same audit found the public team page returned 404 while the local page existed.
- Cloudflare's active **PPW SEO - canonical Markdown** response-header rule sets `Link: <HTML-URL>; rel="canonical"` on the seven generated `index.md` paths. Its dynamic value is `concat("<https://www.proiectulpaginiweb.ro", substring(http.request.uri.path, 0, -8), ">; rel=\"canonical\"")`. Extend the rule's explicit path list when adding pages. The local server derives the same headers automatically from matching HTML files. GitHub Pages does not apply arbitrary `_headers` files. Keep Markdown crawlable so Google can see the canonical; do not disallow duplicates in `robots.txt`.
- Before releasing the GEO article, add `/blog/indexare-site-chatgpt-ai-geo/index.md` to that rule's explicit path list and verify `Link: <https://www.proiectulpaginiweb.ro/blog/indexare-site-chatgpt-ai-geo/>; rel="canonical"`. The documented Cloudflare configuration still covers the original seven paths; the repository build does not update the CDN.
- Cloudflare's active **PPW SEO - noindex fisiere auxiliare** response-header rule sets `X-Robots-Tag: noindex` only on `/llms.txt`, `/llms-full.txt` and `/README.md`. The local server does the same. Canonical HTML pages remain indexable. Both response-header rules were deployed and checked publicly on 13 November 2026.
- Keep genuinely missing URLs as HTTP 404. After publication, inspect representative URLs, sitemap processing, indexing and Core Web Vitals in Google Search Console. Rich Results Test checks structured-data eligibility; it does not guarantee a rich result or ranking.

Reference policies: [Google Search Essentials](https://developers.google.com/search/docs/essentials), [SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide), [canonicalization](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls), [structured data guidelines](https://developers.google.com/search/docs/appearance/structured-data/sd-policies), and [page experience](https://developers.google.com/search/docs/appearance/page-experience).

Discovery endpoints `/llms.txt` and `/llms-full.txt` are regenerated by `npm run build`. Publish both files with the site. These files are optional supplemental access for agents; they do not guarantee search indexing or inclusion in AI answers.

# Logo technical details
- logo-ul foloseste fontul Berlin Sans Demi
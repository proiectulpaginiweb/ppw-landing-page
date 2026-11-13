# Proiectul Pagini Web

Responsive, buildless landing page for an AI-native company. Uses the supplied `ppw.png` brand asset and its yellow, green, and orange palette.

## Local preview

```sh
cd ~/projects/proiectul-pagini-web
npm run dev
```

Open http://127.0.0.1:4173. No npm dependencies or build step are required. Any static host can serve this directory.

The local server (`scripts/serve.py`) declares `charset=utf-8` for Markdown and other text responses so browsers display Romanian diacritics correctly. Keep source and generated text files in UTF-8; the discovery generator reads and writes that encoding explicitly. Production hosting should serve `.md` files as `text/markdown; charset=utf-8` and `.txt` files as `text/plain; charset=utf-8`.

## Content and interactions

- Romanian positioning, services, illustrative workflow, interactive journey, principles, FAQs, and contact section.
- Team page at `/echipa/`, introducing Sîrbu Nicolae-Cezar, his technical background, and public sources for the projects and experience described. It shares the site branding and mobile menu.
- Blog at `/blog/`, using the same visual language and navigation as the landing page. Articles cover AI chat versus agents in Romanian at `/blog/chat-ai-vs-agent-ai/`, the agentic internet in Romanian at `/blog/internetul-agentic-este-aici/`, and training AI models for specific applications and businesses in Romanian at `/blog/training-ai-models-for-specific-businesses/`.
- Accessible keyboard-controlled journey tabs, mobile navigation, and native FAQ disclosure controls.
- Contact form submits to Web3Forms using the supplied public access key. Name, email, optional phone number, selected interest, and project details are combined into the message. Inline status feedback handles sending, success, and failure; failed submissions retain the visitor’s entries. All contact links point to the form; no recipient email address is displayed. Delivery goes to the recipient configured for the Web3Forms access key.
- Fonts are loaded through early stylesheet links and preconnects to Google Fonts, with `display=swap` and local system fallbacks. The brand PNG is losslessly compressed, and all content images have explicit dimensions. Google Analytics (`G-01VJRQR4TT`) loads only on `https://www.proiectulpaginiweb.ro` and `https://proiectulpaginiweb.ro`, using the default HTTPS port. Localhost, local IP addresses, file previews, and other preview domains do not load the Google tag or initialize analytics.
- Service copy is proposed marketing copy; no customer logos, testimonials, or performance claims are invented.

Edit `index.html` for page content, `styles.css` for the landing page design, `blog.css` for blog styling, `script.js` for landing page interactions, and `blog.js` for the shared secondary-page menu. The team page is in `echipa/index.html`, with page-specific styles in `echipa.css`. The blog listing is in `blog/index.html`; each article is in its own `blog/<slug>/index.html`. All journey panel copy is in `index.html`; JavaScript only switches visible panels.

## Indexing and agent discovery

Production URL: https://www.proiectulpaginiweb.ro/

See [the SEO implementation and indexing notes](docs/SEO.md) for the Romanian report, deployment status, Google indexing requirements, and the post-publication checklist. Keep `docs/` out of the public deployment.

All four journey panels are present in the HTML response. With JavaScript disabled, every panel remains readable; with JavaScript enabled, the existing tab interface is preserved.

After any content, CSS, or JavaScript edit, run `npm run build`. The dependency-free generator and `scripts/seo.py` keep all seven HTML pages consistent: canonical URLs, indexing directives, Open Graph/Twitter previews, font links, asset content hashes and JSON-LD. Schema uses Organization/WebSite/Services on the homepage, CollectionPage/ItemList on the blog, ProfilePage/Person on the team page, BlogPosting on articles, and BreadcrumbList matching visible navigation. Article authorship remains the named organization; no personal authorship, reviews, addresses or contact details are invented.

Edit each page's authored `<title>`, description, visible copy and breadcrumbs. Article publication dates come from the first visible `<time>` in `.post-header`; the authored `data-date-modified` on `.post` is the source for its modification date. Set it only when there is a real editorial update, and show that update in the page when it differs from publication. Keep the factual Person entity on the team page accurate; it is retained when its metadata block is regenerated. Do not manually edit other contents inside `discovery:start`/`discovery:end` or the generated font blocks.

The build regenerates `index.md`, `echipa/index.md`, `blog/index.md` and every article's adjacent `index.md`, plus `robots.txt`, `sitemap.xml`, `llms.txt` and `llms-full.txt`. All files stay UTF-8. The sitemap contains only canonical HTML pages; optional `lastmod`, `priority` and `changefreq` values are omitted rather than fabricated. Supplemental Markdown and LLM files do not replace indexable HTML or Google's supported indexing signals. A domain change must update `SITE` in `scripts/build_discovery.py`, `SITE`/`HOSTS` in the validator, `CNAME`, authored profile URLs and the CDN rules together.

`npm run build` also runs `scripts/check_seo.py`, checking metadata, structured data/content consistency, sitemap coverage, links, image dimensions and font loading. Run `npm run check:seo` for validation without regeneration. These checks cover repository-controlled requirements; they do not simulate Google's indexing or measure field Core Web Vitals.

Publish `index.html`, `styles.css`, `echipa.css`, `echipa/`, `blog.css`, `blog.js`, `script.js`, `blog/`, `assets/`, `robots.txt`, `sitemap.xml`, `llms.txt`, `llms-full.txt`, `index.md`, and the Google verification file `google83152e7ab05f6d9b.html` together at the domain root. Keep `scripts/`, `package.json`, and this README out of the public deployment if your host supports an explicit file list.

`robots.txt` permits crawling; it does not override host/CDN blocks or guarantee indexing. Ensure the deployed page and discovery files return HTTP 200 with no authentication, challenge, or `X-Robots-Tag: noindex`. Configure non-www/HTTP URLs to redirect to the canonical HTTPS www address at the hosting layer. Submit the sitemap in your search-console account if desired. `llms.txt` is supplementary guidance, not a guarantee that an AI service will use it.

### Hosting checks before release

- Keep a permanent redirect from both HTTP hosts to HTTPS, preserving paths and query strings, followed by the existing redirect to the canonical www hostname. Cloudflare's **Always Use HTTPS** was enabled on 13 November 2026; HTTP www now returns 301 to HTTPS with the full path/query preserved. No JavaScript or meta refresh redirects are used.
- Deploy every updated HTML page and asset, `/echipa/`, and the regenerated sitemap together. The same audit found the public team page returned 404 while the local page existed.
- Cloudflare's active **PPW SEO - canonical Markdown** response-header rule sets `Link: <HTML-URL>; rel="canonical"` on the seven generated `index.md` paths. Its dynamic value is `concat("<https://www.proiectulpaginiweb.ro", substring(http.request.uri.path, 0, -8), ">; rel=\"canonical\"")`. Extend the rule's explicit path list when adding pages. The local server derives the same headers automatically from matching HTML files. GitHub Pages does not apply arbitrary `_headers` files. Keep Markdown crawlable so Google can see the canonical; do not disallow duplicates in `robots.txt`.
- Cloudflare's active **PPW SEO - noindex fisiere auxiliare** response-header rule sets `X-Robots-Tag: noindex` only on `/llms.txt`, `/llms-full.txt` and `/README.md`. The local server does the same. Canonical HTML pages remain indexable. Both response-header rules were deployed and checked publicly on 13 November 2026.
- Keep genuinely missing URLs as HTTP 404. After publication, inspect representative URLs, sitemap processing, indexing and Core Web Vitals in Google Search Console. Rich Results Test checks structured-data eligibility; it does not guarantee a rich result or ranking.

Reference policies: [Google Search Essentials](https://developers.google.com/search/docs/essentials), [SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide), [canonicalization](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls), [structured data guidelines](https://developers.google.com/search/docs/appearance/structured-data/sd-policies), and [page experience](https://developers.google.com/search/docs/appearance/page-experience).

Discovery endpoints `/llms.txt` and `/llms-full.txt` are regenerated by `npm run build`. Publish both files with the site. These files are optional supplemental access for agents; they do not guarantee search indexing or inclusion in AI answers.

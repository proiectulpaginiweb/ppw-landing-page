# Proiectul Pagini Web

Responsive static site for an AI-native company. Uses the supplied `proiectul-pagini-web-logo-2013.png` brand asset and its yellow, green, and orange palette.

## Local preview

```sh
cd ~/projects/ppw/proiectul-pagini-web
npm run dev
```

Open http://127.0.0.1:4173. Checked-in generated assets allow preview without npm dependencies. After editing CSS or content, run `npm ci` once, then `npm run build`. The only npm dependency is the build-time CSS minifier; the published site has no npm runtime dependencies. Any static host can serve the generated files.

The local server also compresses text with gzip, supports conditional requests and caches fingerprinted files in `assets/static/` for one year only when the filename hash matches their actual bytes. Legacy `?v=` links remain supported for older pages. HTML and unversioned files revalidate to keep edits visible. These preview headers do not configure GitHub Pages or Cloudflare.

The local server (`scripts/serve.py`) declares `charset=utf-8` for Markdown and other text responses so browsers display Romanian diacritics correctly. Keep source and generated text files in UTF-8; the discovery generator reads and writes that encoding explicitly. Production hosting should serve `.md` files as `text/markdown; charset=utf-8` and `.txt` files as `text/plain; charset=utf-8`.

## Content and interactions

- Romanian positioning, services, illustrative workflow, interactive journey, principles, FAQs, and contact section.
- Team page at `/echipa/`, introducing Sîrbu Nicolae-Cezar, his technical background, and public sources for the projects and experience described. It shares the site branding and mobile menu.
- Blog at `/blog/`, using the same visual language and navigation as the landing page. Its five Romanian articles cover AI chats versus agents, the agentic internet, specialized models for businesses, token costs for an MVP, and website visibility in ChatGPT and AI search. The GEO guide is at `/blog/indexare-site-chatgpt-ia-geo/`, based on `docs/GEO.md` and official provider documentation.
- Accessible keyboard-controlled journey tabs, mobile navigation, and native FAQ disclosure controls.
- Custom `404.html` in the PPW visual style, with home/blog recovery links and root-relative fingerprinted assets that work at missing URLs of any depth. The build regenerates its shared styles and assets; edit `404.html` for copy and `404.css` for its layout. It is excluded from indexing and the sitemap. The local preview returns the same custom page with HTTP 404, and the Pages package includes it automatically.
- The favicon is a static dark arrow on a green rounded tile, served from `assets/favicon.svg` with a content-hashed URL. The generator maintains the shared fingerprinted favicon link on all pages. The 2013 logo remains the brand image in the page and social metadata.
- Contact form submits to Web3Forms using the supplied public access key. Name, email, optional phone number, selected interest, and project details are combined into the message. Inline status feedback handles sending, success, and failure; failed submissions retain the visitor’s entries. All contact links point to the form; no recipient email address is displayed. Delivery goes to the recipient configured for the Web3Forms access key.
- DM Sans and Manrope variable WOFF2 fonts are served locally with Latin and small Romanian subsets, `font-display: swap`, four matching preloads and system fallbacks. Full Latin-ext faces remain available for other languages; Romanian pages download about 55 KB of fonts instead of 115 KB. Publish their OFL licenses in `assets/fonts/`. CSS is minified during the build and included directly in each HTML page to remove render-blocking CSS requests; homepage rules are excluded from blog and team pages. The logo blink uses opacity-only animations and respects reduced-motion preferences. The homepage logo uses a pixel-identical lossless WebP with a PNG fallback, preserving its original 213×121 proportions. All content images have explicit dimensions. Shared `analytics.js` follows the page interaction script with `defer` on all eight pages. Google Analytics (`G-01VJRQR4TT`) loads only on `https://www.proiectulpaginiweb.ro` and `https://proiectulpaginiweb.ro`, using the default HTTPS port. Events are queued immediately; the Google script loads at low priority in a browser idle callback after the window load event (with a timer fallback). Localhost, local IP addresses, file previews, and other preview domains do not load the Google tag or initialize analytics.
- Service copy is proposed marketing copy; no customer logos, testimonials, or performance claims are invented.

Edit `index.html` for page content, `styles.css` for shared styles, `home.css` for the landing page design, `fonts.css` for font declarations, `blog.css` for blog styling, `script.js` for landing page interactions, `blog.js` for the shared secondary-page menu, and `analytics.js` for site-wide Google Analytics. The team page is in `echipa/index.html`, with page-specific styles in `echipa.css`. The blog listing is in `blog/index.html`; each article is in its own `blog/<slug>/index.html`. All journey panel copy is in `index.html`; JavaScript only switches visible panels.

Page slugs and linked section anchors use Romanian, without diacritics. Product names and technical acronyms such as ChatGPT, JavaScript, GEO and MVP keep their established spelling. The URL migration is defined in `scripts/page_urls.py`:

| Previous article path | Romanian canonical path |
| --- | --- |
| `/blog/chat-ai-vs-agent-ai/` | `/blog/diferenta-dintre-chat-ia-si-agent-ia/` |
| `/blog/training-ai-models-for-specific-businesses/` | `/blog/antrenarea-modelelor-ia-pentru-afaceri/` |
| `/blog/spring-rails-react-tokeni-startup/` | `/blog/java-ruby-javascript-costuri-tokeni-mvp/` |
| `/blog/indexare-site-chatgpt-ai-geo/` | `/blog/indexare-site-chatgpt-ia-geo/` |

The local server returns HTTP 301 for the previous article paths, including `index.html` and `index.md` aliases, preserving query strings. `blog.js` translates old section fragments to their Romanian names. The Pages packager adds `noindex` HTML redirect fallbacks and Markdown move notices at the previous paths, outside the canonical source pages and sitemap. HTML fallbacks preserve query strings and fragments with JavaScript; a meta refresh and a visible Romanian link provide a fallback. GitHub Pages serves these as static files; configure the same path mappings as permanent redirects in Cloudflare for HTTP 301 redirects in production. Deploy the generated `dist/` package to include the compatibility files.

## Asset filenames and GitHub Pages deployment

`npm run build` generates physical content-addressed copies of JavaScript, fonts, images and article charts in `assets/static/`, for example `assets/static/analytics.88ccc6495426.js`. The 12-character SHA-256 hash changes only when the source bytes change. Edit the original source files; never edit generated assets. The build updates HTML, font preloads, inline CSS, `srcset`, social previews, JSON-LD and any exported Markdown image links together. `assets/asset-manifest.json` maps authored paths to current fingerprints and retains reverse mappings for older builds.

Repeated builds are deterministic. Current and older generated files are kept, so an open or cached page can still fetch the exact asset version it references. A changed file receives a new URL; unchanged files keep theirs. Keep `assets/static/` and the manifest when committing generated output.

```sh
npm ci
npm test
npm run build:pages
```

`build:pages` builds the site and packages the public files into ignored `dist/`. The GitHub Pages workflow at `.github/workflows/pages.yml` runs this process for pushes to `main` and manual runs. In the repository's **Settings → Pages → Build and deployment → Source**, select **GitHub Actions** once; that repository setting is separate from the workflow file. Publish `dist/` as the Pages artifact, rather than uploading the checkout with tooling and documentation.

For deployment, the packager restores historical fingerprinted asset bytes from the checked-out Git history and includes them in every new artifact. The workflow fetches full history. Local history builds also need a complete clone; a shallow clone is rejected instead of silently omitting old assets. Retention follows the deployment branch's available history, so preserve that history when maintaining old URLs.

On Cloudflare, match only `/assets/static/` for the long **Browser TTL** (one year). Keep HTML and `assets/asset-manifest.json` on a short lifetime. Hashes make long caching safe; GitHub Pages still controls its origin headers, so filenames alone do not change the public cache lifetime. No Cloudflare account settings are changed by the build.

## Indexing and agent discovery

Production URL: https://www.proiectulpaginiweb.ro/

See [the SEO implementation and indexing notes](docs/SEO.md) for the Romanian report, deployment status, Google indexing requirements, and the post-publication checklist. Keep `docs/` out of the public deployment.

See [the GEO implementation and citation notes](docs/GEO.md) for the standalone Romanian report on generative search, crawler access, source preservation and follow-up measurement.

All four journey panels are present in the HTML response. With JavaScript disabled, every panel remains readable; with JavaScript enabled, the existing tab interface is preserved.

Do not edit `*.min.css`: `scripts/build_assets.cjs` generates them with clean-css, preserving rule order. Shared `styles.min.css` includes font declarations; the metadata generator combines it with the page-specific bundle inside `styles:start`/`styles:end`. It rebases font URLs for nested pages. The small complete bundles preserve the cascade and styling with JavaScript disabled; no separate CSS request is needed. Do not edit the generated inline styles.

After any content, CSS, or JavaScript edit, run `npm run build`. The CSS minifier, discovery generator and `scripts/seo.py` keep all eight HTML pages consistent: canonical URLs, indexing directives, Open Graph/Twitter previews, font preloads, inline CSS, physical asset fingerprints and JSON-LD. Schema uses Organization/WebSite/Services on the homepage, CollectionPage/ItemList on the blog, ProfilePage/Person on the team page, BlogPosting on articles, and BreadcrumbList matching visible navigation. Article authorship remains the named organization; no personal authorship, reviews, addresses or contact details are invented.

Edit each page's authored `<title>`, description, visible copy and breadcrumbs. Article publication dates come from the first visible `<time>` in `.post-header`; the authored `data-date-modified` on `.post` is the source for its modification date. Set it only when there is a real editorial update, and show that update in the page when it differs from publication. Keep the factual Person entity on the team page accurate; it is retained when its metadata block is regenerated. Do not manually edit other contents inside `discovery:start`/`discovery:end` or the generated font/style/script blocks.

The build regenerates `index.md`, `echipa/index.md`, `blog/index.md` and every article's adjacent `index.md`, plus `robots.txt`, `sitemap.xml`, `llms.txt` and `llms-full.txt`. All files stay UTF-8. The sitemap contains only canonical HTML pages; optional `lastmod`, `priority` and `changefreq` values are omitted rather than fabricated. Supplemental Markdown and LLM files do not replace indexable HTML or Google's supported indexing signals. A domain change must update `SITE` in `scripts/build_discovery.py`, `SITE`/`HOSTS` in the validator, `CNAME`, authored profile URLs and the CDN rules together.

`npm run build` also runs `scripts/check_seo.py`, checking metadata, structured data/content consistency, sitemap coverage, links, image dimensions and font loading, and `scripts/check_geo.py`, checking summaries, source preservation, absolute Markdown links and entity consistency. Run `npm run check:seo` or `npm run check:geo` for validation without regeneration. These checks cover repository-controlled requirements; they do not simulate indexing, AI citations or field Core Web Vitals.

### Generative search (GEO)

The homepage defines Proiectul Pagini Web and its services in visible copy. The Organization and WebSite use the full company name without an `alternateName`. Services have stable anchors, and each article has three reader-facing takeaways at `#pe-scurt`. Article JSON-LD includes an abstract from that summary and citations taken only from the article's visible external source links. Personal LinkedIn/GitHub profiles remain attached to the Person, not the Organization. Publication dates are preserved; the actual summary updates are dated 13 November 2026.

`scripts/markdown_content.py` renders the same content recursively into Markdown, preserving nested summaries/lists, emphasis, code, figures and simple tables. All source links resolve against the page's canonical URL, so they also work in `llms-full.txt`. `llms.txt` is a supplemental directory grouped into PPW, services, team, articles and contact. It is not a crawler access policy or a promise of AI visibility. Google does not use it for generative-search visibility and does not require special GEO files/schema. See [Google's generative AI guidance](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide).

The crawler audit on 13 November 2026 found HTTP 200 for the public homepage with search/user-agent identifiers from Google, Bing, OpenAI, Anthropic and Perplexity, and no injected robots disallow block. These are user-agent smoke tests, not verification of real crawler IP access. No crawler permissions or model-training preferences were changed. Search and model training have separate controls: [OpenAI](https://developers.openai.com/api/docs/bots), [Anthropic](https://privacy.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler), [Perplexity](https://docs.perplexity.ai/docs/resources/perplexity-crawlers).

The same-day Search Console inspection confirmed that the verified www property inherits **Search generative AI: Include** from the domain. That setting was already active and was left unchanged. The overview reported six indexed pages and no Core Web Vitals data; these observations concern the published site, not the new local content. See the GEO section in `docs/SEO.md` for status and follow-up measurement.

Publish `index.html`, `styles.min.css`, `home.min.css`, `blog.min.css`, `echipa.min.css`, `echipa/`, `blog.js`, `script.js`, `analytics.js`, `blog/`, `assets/` (including `assets/static/` and its manifest), `robots.txt`, `sitemap.xml`, `llms.txt`, `llms-full.txt`, `index.md`, and the Google verification file `google83152e7ab05f6d9b.html` together at the domain root. Keep `scripts/`, `tests/`, `node_modules/`, `package.json`, `package-lock.json`, authored CSS sources, and this README out of the public deployment if your host supports an explicit file list.

`robots.txt` permits crawling; it does not override host/CDN blocks or guarantee indexing. Ensure the deployed page and discovery files return HTTP 200 with no authentication, challenge, or `X-Robots-Tag: noindex`. Configure non-www/HTTP URLs to redirect to the canonical HTTPS www address at the hosting layer. Submit the sitemap in your search-console account if desired. `llms.txt` is supplementary guidance, not a guarantee that an AI service will use it.

### Hosting checks before release

- Keep a permanent redirect from both HTTP hosts to HTTPS, preserving paths and query strings, followed by the existing redirect to the canonical www hostname. Cloudflare's **Always Use HTTPS** was enabled on 13 November 2026; HTTP www now returns 301 to HTTPS with the full path/query preserved. Hostname and protocol redirects are handled by the hosting layer.
- Deploy every updated HTML page and asset, `/echipa/`, and the regenerated sitemap together. The same audit found the public team page returned 404 while the local page existed.
- Cloudflare's active **PPW SEO - canonical Markdown** response-header rule sets `Link: <HTML-URL>; rel="canonical"` on the seven generated `index.md` paths. Its dynamic value is `concat("<https://www.proiectulpaginiweb.ro", substring(http.request.uri.path, 0, -8), ">; rel=\"canonical\"")`. Extend the rule's explicit path list when adding pages. The local server derives the same headers automatically from matching HTML files. GitHub Pages does not apply arbitrary `_headers` files. Keep Markdown crawlable so Google can see the canonical; do not disallow duplicates in `robots.txt`.
- Before releasing the Romanian URL migration, update that rule's explicit path list for the four Romanian canonical paths in the table above, each followed by `index.md`. This includes the GEO article at `/blog/indexare-site-chatgpt-ia-geo/index.md`; verify `Link: <https://www.proiectulpaginiweb.ro/blog/indexare-site-chatgpt-ia-geo/>; rel="canonical"`. The documented Cloudflare configuration still covers the original seven paths; the repository build does not update the CDN.
- Cloudflare's active **PPW SEO - noindex fisiere auxiliare** response-header rule sets `X-Robots-Tag: noindex` only on `/llms.txt`, `/llms-full.txt` and `/README.md`. The local server does the same. Canonical HTML pages remain indexable. Both response-header rules were deployed and checked publicly on 13 November 2026.
- Keep genuinely missing URLs as HTTP 404. After publication, inspect representative URLs, sitemap processing, indexing and Core Web Vitals in Google Search Console. Rich Results Test checks structured-data eligibility; it does not guarantee a rich result or ranking.

Reference policies: [Google Search Essentials](https://developers.google.com/search/docs/essentials), [SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide), [canonicalization](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls), [structured data guidelines](https://developers.google.com/search/docs/appearance/structured-data/sd-policies), and [page experience](https://developers.google.com/search/docs/appearance/page-experience).

Discovery endpoints `/llms.txt` and `/llms-full.txt` are regenerated by `npm run build`. Publish both files with the site. These files are optional supplemental access for agents; they do not guarantee search indexing or inclusion in AI answers.

# Logo technical details
- logo-ul foloseste fontul Berlin Sans Demi

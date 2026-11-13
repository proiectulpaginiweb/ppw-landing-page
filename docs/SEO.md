# PPW — optimizări SEO și indexarea în Google

Data documentului: **13 noiembrie 2026**  
Site canonic: **[www.proiectulpaginiweb.ro](https://www.proiectulpaginiweb.ro/)**

Acest document descrie modificările realizate, verificările efectuate și pașii rămași pentru publicare și monitorizare. Este documentație a proiectului, nu o pagină destinată rezultatelor Google; nu este inclus în sitemap și nu trebuie adăugat în pachetul public al site-ului.

## 1. Starea implementării

| Componentă | Stare la redactare |
| --- | --- |
| Optimizările HTML, CSS, imaginile și generatoarele | Implementate și verificate local; modificările nu au fost publicate în această intervenție |
| Redirecționarea HTTP → HTTPS în Cloudflare | Activată și verificată public |
| Antetele canonical pentru copiile Markdown | Regula Cloudflare este activă pentru cele șapte căi configurate |
| `noindex` pentru fișierele auxiliare | Activ în Cloudflare pentru trei căi exacte |
| Verificarea SEO automată și build-ul | Trec pentru toate cele șapte pagini HTML |
| Verificarea mobilă | Cele șapte pagini verificate la 390 px, fără depășire orizontală |
| Google Search Console și Rich Results Test | Nu au fost folosite pentru validarea noii versiuni în această intervenție |
| Core Web Vitals din trafic real | Nu au fost măsurate |

La auditul public din 13 noiembrie, înaintea publicării modificărilor locale, `/echipa/` răspundea cu **404**, iar sitemap-ul public nu includea pagina. Existența fișierelor în repository sau funcționarea lor pe localhost nu le face accesibile Google pe domeniul public.

## 2. Ce am modificat în site

### Metadate și URL-uri coerente

Am actualizat titlurile și descrierile pentru a explica mai clar serviciile și subiectele paginilor. Titlurile și descrierile sunt distincte, iar fiecare pagină are o singură adresă canonical, pe HTTPS și cu `www`.

Generatorul `scripts/seo.py`, apelat de `scripts/build_discovery.py`, uniformizează:

- canonicalele, directivele de indexare și metadatele Open Graph/Twitter;
- legăturile către variantele Markdown și sitemap;
- încărcarea fonturilor și versiunile CSS/JavaScript bazate pe conținut;
- datele structurate, pornind de la conținutul paginilor.

Open Graph și Twitter ajută previzualizările la distribuire; nu înlocuiesc semnalele de indexare Google. Titlurile și descrierile propuse pot fi afișate diferit de Google. [Ghid Google pentru titluri](https://developers.google.com/search/docs/appearance/title-link), [ghid pentru descrieri](https://developers.google.com/search/docs/appearance/snippet).

### Date structurate și informații editoriale

| Pagină | Date structurate |
| --- | --- |
| Pagina principală | `Organization`, `WebSite`, `WebPage`, `Service` |
| Lista de articole | `CollectionPage`, `ItemList`, `BreadcrumbList` |
| Echipa | `ProfilePage`, `Person`, `BreadcrumbList` |
| Fiecare articol | `WebPage`, `BlogPosting`, `BreadcrumbList` |

Am adăugat autori vizibili, legături către echipă, breadcrumbs și articole conexe. Autorul declarat al articolelor este **Proiectul Pagini Web**, ca organizație; nu am atribuit unei persoane articole fără confirmare.

Datele editoriale existente au fost păstrate. Publicarea este preluată din primul `<time>` al antetului articolului, iar modificarea din atributul `data-date-modified`. Data actualizării este vizibilă când diferă de publicare. Nu am adăugat recenzii, evaluări sau date de contact inventate.

Marcajele trebuie să descrie conținutul real al paginii. JSON-LD valid nu garantează afișarea unui rezultat îmbogățit. [Regulile Google pentru date structurate](https://developers.google.com/search/docs/appearance/structured-data/sd-policies).

### Performanță și afișare

- Fonturile variabile DM Sans și Manrope sunt găzduite local în WOFF2, cu subseturile Latin și Latin-ext pentru diacritice, licențe OFL, `font-display: swap` și două preîncărcări Latin. Am eliminat conexiunile Google Fonts din încărcarea paginilor.
- Am separat CSS-ul paginii principale de stilurile comune și am introdus minificarea la build. Blogul încarcă aproximativ **14 KB CSS**, față de **31 KB** înainte. Sursele rămân lizibile; HTML-ul folosește fișierele `*.min.css` cu hash de conținut.
- Am corectat contrastul textelor, numele accesibile ale siglei și linkurilor de articole. Animația siglei folosește doar opacitate, cu preferința pentru mișcare redusă păstrată.
- Serverul local folosește gzip, cereri condiționale și cache lung numai pentru resurse statice cu hash valid. Aceste antete sunt pentru preview; compresia și cache-ul domeniului public țin de GitHub Pages/Cloudflare.
- Am comprimat fără pierderi sigla PNG: **25.752 → 24.880 bytes**, cu pixeli și metadate păstrate.
- Imaginile au dimensiuni explicite. Graficele aflate sub primul ecran sunt încărcate cu `loading="lazy"`; portretul principal rămâne prioritar.
- Am verificat afișarea pe mobil și aspectul paginii principale pe desktop.

Aceste modificări reduc întârzieri și riscuri de deplasare a conținutului. Ele nu reprezintă o măsurare Core Web Vitals. [Recomandări Google despre experiența paginii](https://developers.google.com/search/docs/appearance/page-experience).

### Verificarea Lighthouse după remedieri

Am repetat raportul deschis în Chrome pentru `http://localhost:4173/blog/`, pe desktop, cu **Lighthouse 13.5.0**. Configurația celor două rapoarte este identică; extensiile browserului au rămas active. Raportul final a fost capturat la **13 noiembrie 2026, 20:10**, ora României.

| Indicator | Înainte | După |
| --- | --- | --- |
| Performanță | 88 | 100 |
| Accesibilitate | 95 | 100 |
| Bune practici | 100 | 100 |
| SEO | 100 | 100 |
| Agentic Browsing | 3/3 | 3/3 |
| FCP | 0,9 s | 0,3 s |
| LCP | 0,9 s | 0,4 s |
| Speed Index | 8,8 s | 0,3 s |
| Total Blocking Time | 0 ms | 0 ms |
| Cumulative Layout Shift | 0 | 0 |

Au dispărut constatările privind contrastul, minificarea CSS, CSS-ul neutilizat, animația necompozitată, cache-ul și lipsa compresiei documentului. Au trecut și build-ul, verificările SEO/GEO pentru șapte pagini, verificările mobile la 390 px și verificările HTTP ale serverului local.

Avertizarea de **13 KiB JavaScript** rămasă indică două fișiere `chrome-extension://`, nu scripturi PPW. Estimarea de **130 ms** pentru resurse care blochează randarea se referă la cele două foi CSS locale necesare afișării; am păstrat încărcarea normală pentru a evita afișarea temporară fără stiluri. Google recomandă reducerea CSS-ului necesar primei afișări și arată că majoritatea site-urilor pot atinge țintele de performanță fără tehnici avansate de CSS inline. [Documentația Chrome despre render-blocking](https://developer.chrome.com/docs/performance/insights/render-blocking), [animații compozitate](https://developer.chrome.com/docs/lighthouse/performance/non-composited-animations).

Aceste rezultate provin dintr-un test local de laborator pentru Blog. Nu sunt măsurători din trafic real și nu reprezintă scoruri confirmate pentru toate paginile publicate. Resursele noi și fișierele HTML trebuie publicate împreună, apoi domeniul public trebuie testat separat.

### UTF-8 și fișiere de descoperire

Fișierele Markdown au fost verificate pentru UTF-8, diacritice românești și normalizare Unicode NFC. Generatorul citește și scrie explicit UTF-8, iar serverul local declară `charset=utf-8` pentru răspunsurile text.

Build-ul regenerează copiile Markdown, `robots.txt`, `sitemap.xml`, `llms.txt` și `llms-full.txt`. Sitemap-ul conține cele șapte adrese HTML canonice, fără duplicate Markdown sau aliasuri `index.html`.

Nu am introdus date `lastmod` artificiale. Dacă vor fi adăugate, acestea trebuie să reflecte modificări semnificative reale, nu momentul fiecărui build. `priority` și `changefreq` nu au fost adăugate. [Documentația Google pentru sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).

## 3. Ce am activat în Cloudflare

### HTTPS obligatoriu

Am activat **Always Use HTTPS**. Cererile HTTP sunt redirecționate permanent către HTTPS, păstrând calea și parametrii. Redirecționarea existentă de la domeniul fără `www` conduce ulterior la varianta canonică.

Exemplul verificat public a ajuns la destinația corectă:

```text
http://proiectulpaginiweb.ro/blog/?seo-check=2
→ https://www.proiectulpaginiweb.ro/blog/?seo-check=2
```

### Canonical pentru Markdown

Regula **PPW SEO - canonical Markdown** adaugă un antet HTTP către pagina HTML corespunzătoare. Exemplu:

```http
Link: <https://www.proiectulpaginiweb.ro/blog/chat-ai-vs-agent-ai/>; rel="canonical"
```

Regula acoperă lista explicită a celor șapte copii `index.md`. Când apare o pagină nouă, lista Cloudflare trebuie extinsă; build-ul local nu modifică automat CDN-ul. Serverul local derivă antetul din fișierul HTML corespunzător.

Canonicalul indică versiunea preferată a conținutului duplicat; Google poate selecta o altă variantă. Copiile Markdown rămân accesibile crawlerelor pentru ca antetul să poată fi citit. Nu folosim `robots.txt` sau `noindex` în locul canonicalului pentru aceste copii. [Documentația Google despre canonicalizare](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls).

### Fișiere auxiliare excluse din rezultate

Regula **PPW SEO - noindex fisiere auxiliare** setează `X-Robots-Tag: noindex` numai pentru:

- `/llms.txt`;
- `/llms-full.txt`;
- `/README.md`.

Paginile HTML canonice nu primesc această directivă. Fișierele LLM rămân disponibile agenților; ele sunt resurse suplimentare și nu înlocuiesc mecanismele Google de descoperire și indexare.

## 4. Ce contează pentru indexare

### Accesibilitatea publică este primul pas

Pagina dorită în rezultate trebuie să poată fi accesată de Googlebot, să răspundă cu **HTTP 200** și să ofere conținut indexabil. Nu trebuie să necesite autentificare sau să fie blocată accidental de `robots.txt`, reguli CDN ori `noindex`.

`index, follow` nu obligă Google să indexeze pagina. Un test HTTP cu identificatorul „Googlebot” nu dovedește accesul crawlerului Google real. Verificarea specifică se face prin **URL Inspection** în Search Console. [Cerințele tehnice Google](https://developers.google.com/search/docs/essentials/technical).

### Conținutul trebuie să merite indexat

Paginile trebuie să răspundă clar unor nevoi reale, cu informații originale și verificabile, titluri descriptive, surse și autori corecți. Legăturile interne trebuie să ajute vizitatorul să descopere paginile relevante. Evităm repetarea artificială a cuvintelor-cheie și crearea de pagini doar pentru motoare de căutare. [Recomandările Google pentru conținut util](https://developers.google.com/search/docs/fundamentals/creating-helpful-content), [politicile antispam](https://developers.google.com/search/docs/essentials/spam-policies).

### Semnalele trebuie să indice aceeași versiune

Linkurile interne, redirecturile, canonicalele și sitemap-ul trebuie să folosească aceeași adresă preferată. Sitemap-ul ajută la descoperire, însă nu garantează indexarea. Paginile inexistente trebuie să întoarcă un 404 real, fără a fi prezentate drept pagini funcționale.

Descoperirea unei adrese, indexarea conținutului și poziționarea în rezultate sunt etape diferite. Nici implementarea tehnică, nici un scor de performanță bun nu garantează indexarea sau o anumită poziție.

## 5. Publicare și verificare

1. Rulează `npm ci` la prima instalare, apoi `npm run build` și rezolvă eventualele erori.
2. Publică toate paginile HTML, stilurile, scripturile, imaginile și fișierele generate împreună. Include `/echipa/` și sitemap-ul actualizat. Lista fișierelor de publicat este în `README.md`.
3. Verifică pe domeniul public că fiecare adresă canonică răspunde cu 200, că redirecturile funcționează și că nu există `noindex` pe paginile dorite în Google.
4. Verifică în Search Console procesarea [sitemap-ului PPW](https://www.proiectulpaginiweb.ro/sitemap.xml). Trimite-l dacă nu este deja înregistrat.
5. Folosește URL Inspection pentru pagina principală, Echipa și un articol: acces, test live, indexare permisă și canonical ales de Google. Solicită indexarea paginilor noi sau actualizate atunci când este cazul.
6. Verifică pagini reprezentative în [Rich Results Test](https://search.google.com/test/rich-results) și performanța în [PageSpeed Insights](https://pagespeed.web.dev/). Monitorizează ulterior rapoartele de indexare și Core Web Vitals din Search Console.

Google nu oferă un termen garantat pentru indexare; evită solicitările repetate fără o schimbare sau o problemă concretă de verificat. [Recomandările Google pentru recrawl](https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl).

## 6. Întreținere și limitele verificărilor

```sh
# Regenerează metadatele și fișierele de descoperire, apoi verifică SEO.
npm run build

# Verifică starea existentă fără regenerare.
npm run check:seo

# Pornește previzualizarea locală cu antete UTF-8 și SEO.
npm run dev
```

Validatorul `scripts/check_seo.py` verifică metadatele, canonicalele, datele structurate și concordanța lor cu textul vizibil, breadcrumbs, linkuri și ancore locale, dimensiunile imaginilor, fonturile și sitemap-ul. Am verificat și că respinge un canonical greșit într-o copie temporară a proiectului.

Build-ul este idempotent: o repetare fără modificări nu schimbă fișierele generate. Au fost verificate și răspunsurile HTTP locale pentru șapte pagini HTML, șapte copii Markdown și cele trei fișiere auxiliare.

Aceste verificări nu înlocuiesc rapoartele Google, evaluarea calității conținutului sau măsurarea experienței utilizatorilor reali. La fiecare pagină nouă, menține accesul din navigație, metadatele și datele editoriale corecte, regenerează sitemap-ul și actualizează regula Cloudflare pentru noua copie Markdown.

## 7. GEO — vizibilitate în răspunsurile cu IA

Raportul separat și pașii de întreținere sunt în [GEO.md](GEO.md).

În această intervenție, GEO înseamnă **Generative Engine Optimization**: conținut clar, verificabil și accesibil pentru oameni și pentru sistemele care caută surse pentru răspunsuri cu IA.

Verificarea ulterioară din Search Console, în aceeași zi, a confirmat că proprietatea PPW este verificată și moștenește controlul **Search generative AI: Include** de la domeniu. Setarea era deja activă și nu a fost modificată. Panoul raporta șase pagini indexate și lipsa datelor Core Web Vitals. Aceasta este starea raportată de Google pentru versiunea publică, nu validarea modificărilor locale noi; Rich Results Test nu a fost rulat.

### Modificări realizate în proiect

- Definiție vizibilă a Proiectului Pagini Web, plus o întrebare frecventă despre serviciile oferite.
- Adrese cu fragment pentru fiecare serviciu: `#agenti-ia`, `#automatizari`, `#aplicatii-web`.
- Câte trei idei „Pe scurt” în fiecare dintre cele patru articole, accesibile la `#pe-scurt`. Acestea rezumă argumentele existente, fără rezultate sau experiențe inventate.
- Actualizări editoriale reale datate **13 noiembrie 2026**, fără schimbarea datelor publicării inițiale.
- Numele complet al organizației, rezumate `abstract` și surse `citation` în articole, toate preluate din textul vizibil. Profilurile personale rămân asociate persoanei.
- Conversie Markdown recursivă, care păstrează rezumatele, listele imbricate, evidențierile, codul, figurile și tabelele simple. Linkurile relative au fost transformate în linkuri absolute, inclusiv în fișierul agregat.
- Un index `llms.txt` mai clar și verificări automate prin `npm run check:geo`, integrate în build.

Aceste modificări sunt locale până la publicarea noii versiuni HTML și a fișierelor generate.

### Acces pentru crawlere și limite

Auditul public a găsit `robots.txt` cu acces permis și răspunsuri 200 pentru homepage la cereri cu identificatorii Googlebot, bingbot, OAI-SearchBot, ChatGPT-User, Claude-SearchBot, Claude-User, PerplexityBot și Perplexity-User. Acest test nu confirmă accesul de la IP-urile crawlerelor reale și nici includerea în răspunsuri.

Nu am schimbat preferințele de antrenare sau protecțiile CDN. Accesul pentru căutare este separat de antrenarea modelelor: de exemplu, OpenAI distinge OAI-SearchBot de GPTBot, iar Anthropic distinge Claude-SearchBot de ClaudeBot. [OpenAI Crawlers](https://developers.openai.com/api/docs/bots), [Anthropic Crawlers](https://privacy.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler).

### Ce trebuie urmărit după publicare

Google cere o bază SEO corectă și pagini eligibile pentru indexare și fragmente de rezultat. Ghidul actual indică și verificarea includerii în funcțiile generative din Search Console. Nu există un format GEO special obligatoriu; Google nu folosește `llms.txt` pentru vizibilitate sau ranking. Rezumatele sunt pentru cititori, nu o cerință tehnică Google. [Ghidul Google pentru IA generativă](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide).

După publicare, urmărește rapoartele disponibile în Search Console și, pentru Bing, [AI Performance](https://blogs.bing.com/webmaster/2026/2/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview/). Compară în timp paginile citate, întrebările relevante și vizitele utile. Nu există o citare sau o poziție garantată în ChatGPT, Google, Claude ori Perplexity.

# PPW — optimizări GEO, indexare și citare în răspunsurile IA

Data documentului: **13 noiembrie 2026**  
Site: **[Proiectul Pagini Web](https://www.proiectulpaginiweb.ro/)**

GEO înseamnă **Generative Engine Optimization**. Pentru PPW, obiectivul este ca informațiile despre companie, servicii, echipă și articole să fie accesibile, clare și verificabile atunci când un motor de căutare sau un asistent IA caută surse.

Documentul descrie implementarea realizată și pașii de întreținere. Este documentație internă a proiectului, nu o pagină destinată sitemap-ului sau publicării pe site. Pentru infrastructura SEO, vezi și [SEO.md](SEO.md).

## 1. Starea actuală

| Componentă | Rezultat la redactare |
| --- | --- |
| Modificări GEO în HTML, Markdown și generatoare | Implementate și verificate local; încă nepublicate în această intervenție |
| Verificări automate SEO și GEO | Trec pentru cele șapte pagini HTML canonice |
| Rezumate pentru cititori | Câte trei idei principale în fiecare dintre cele patru articole |
| Search Console | Proprietatea PPW este verificată; controlul „Search generative AI” moștenește **Include** de la domeniu |
| Setarea de includere în Google | Era deja activă; nu a fost modificată |
| Indexare raportată de Google | Șase pagini indexate, pentru versiunea publică existentă |
| Date Core Web Vitals și rezultate ale citărilor IA | Nu au fost măsurate rezultate noi de citare; panoul nu avea date Core Web Vitals |

Redirecționarea HTTPS, canonicalele HTTP pentru copiile Markdown și `noindex` pentru fișierele auxiliare erau deja active din intervenția SEO anterioară. Nu au fost create reguli noi de acces la crawlere sau de antrenare a modelelor pentru această optimizare GEO.

La audit, pagina publică `/echipa/` răspundea încă cu **404**, iar fișierele publice de descoperire aveau versiunea din 9 noiembrie. Publicarea surselor actualizate rămâne necesară.

## 2. Ce am făcut

### Identitate și servicii mai clare

Am adăugat în pagina principală o definiție vizibilă a **Proiectului Pagini Web** și a serviciilor oferite: agenți IA, automatizări de procese și aplicații web pentru afaceri.

Am completat întrebările frecvente cu o explicație despre servicii și colaborare. Definiția și serviciile au adrese stabile, care permit trimiterea la secțiunea relevantă:

- [Despre PPW](https://www.proiectulpaginiweb.ro/#despre-ppw);
- [Agenți IA](https://www.proiectulpaginiweb.ro/#agenti-ia);
- [Automatizări](https://www.proiectulpaginiweb.ro/#automatizari);
- [Aplicații web](https://www.proiectulpaginiweb.ro/#aplicatii-web).

Aceste ancore sunt implementate în sursa locală și devin disponibile public după publicare.

### Rezumate vizibile în articole

Fiecare articol are o secțiune **„Pe scurt”**, cu trei concluzii și o legătură directă la `#pe-scurt`. Rezumatele păstrează sensul articolului, inclusiv caracterul ilustrativ al scenariilor numerice.

Datele actualizării au fost schimbate la **13 noiembrie 2026**, deoarece au fost adăugate informații editoriale vizibile. Datele publicării inițiale au rămas neschimbate.

### Surse și date structurate coerente

Am completat datele existente astfel:

- `Organization` și `WebSite` folosesc numele complet, fără `alternateName` pentru companie sau site;
- fiecare `Service.url` indică ancora serviciului corespunzător;
- `BlogPosting.abstract` este derivat din rezumatul vizibil;
- `BlogPosting.citation` este derivat exclusiv din linkurile externe ale articolului;
- profilurile LinkedIn și GitHub rămân asociate persoanei, nu organizației.

Aceste proprietăți exprimă informațiile paginii. Ele nu reprezintă o comandă către un model IA și nu obligă un motor să citeze PPW.

### Exporturi Markdown corecte

Am introdus un renderer comun în `scripts/markdown_content.py`. Acesta păstrează secțiunile imbricate, listele, evidențierile, codul, figurile, legendele și tabelele simple.

Am corectat două probleme concrete: secțiunile noi puteau lipsi din export, iar linkurile relative deveneau incorecte în `llms-full.txt`. Acum legăturile sunt rezolvate față de adresa canonică a paginii, iar rezumatele și sursele se păstrează atât în cele șapte copii Markdown, cât și în fișierul agregat.

Am reorganizat `llms.txt` în categorii: PPW, servicii, echipă, articole și contact. Este un index suplimentar pentru sistemele care aleg să-l folosească. Google precizează că nu utilizează astfel de fișiere pentru vizibilitatea sau clasarea în căutarea sa generativă. [Ghid Google pentru IA generativă](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide).

### Verificări automate

Am adăugat `scripts/check_geo.py` și comanda `npm run check:geo`, inclusă și în `npm run build`. Verificările urmăresc:

- păstrarea celor trei concluzii ale fiecărui articol în toate exporturile;
- concordanța surselor vizibile cu citările din datele structurate;
- linkuri Markdown absolute și texte UTF-8 normalizate;
- identitatea PPW și separarea surselor personale;
- adrese distincte pentru serviciile vizibile.

Au trecut și teste pentru liste imbricate, spații între elemente, conținut ascuns și tabele. Testele negative confirmă că un link relativ sau un rezumat pierdut produce eroare. Build-ul repetat fără modificări păstrează aceleași rezultate.

## 3. Ce înseamnă „indexarea GEO”

Nu există un index GEO unic. Furnizorii pot folosi indexuri de căutare și acces direct la pagini, în funcție de produs și de cererea utilizatorului.

Vizibilitatea în răspunsurile IA poate implica următoarele etape:

| Etapă | Ce înseamnă pentru PPW |
| --- | --- |
| Descoperire | Sistemul găsește adresa prin legături, sitemap sau alte surse |
| Acces și indexare | Poate citi pagina, iar motorul decide dacă o păstrează în indexul său |
| Recuperare | La o întrebare concretă, sistemul selectează surse relevante |
| Răspuns și citare | Sistemul folosește informații și decide ce surse afișează |

O pagină accesibilă sau indexată nu este automat selectată pentru fiecare întrebare. Nici citarea într-un răspuns nu garantează o poziție stabilă în răspunsurile viitoare.

## 4. Ce este important în continuare

### Pagini publice funcționale

Versiunea publică trebuie să ofere conținutul complet, răspunsuri HTTP **200** și acces pentru crawlerele relevante. Paginile care trebuie indexate nu trebuie blocate accidental prin `robots.txt`, autentificare, reguli CDN sau `noindex`. Canonicalele, legăturile interne și sitemap-ul trebuie să indice consecvent aceeași versiune HTML.

### Informații utile și verificabile

Păstrează definiții clare, explicații care răspund nevoilor clienților și surse pentru afirmațiile tehnice. Dezvoltă articolele cu experiență reală, exemple reproductibile și rezultate documentate atunci când există. Autorul, data și contextul unei afirmații trebuie să fie ușor de identificat.

Google recomandă conținut original, bine organizat și util oamenilor. Nu solicită fragmente de o lungime fixă, un format Markdown sau o schemă specială GEO. Rezumatele PPW ajută cititorii să parcurgă articolul; nu sunt o cerință tehnică pentru includere. [Recomandările Google pentru căutarea generativă](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide).

### Accesul pentru căutare și preferințele de antrenare

Aceste controale trebuie evaluate separat:

| Furnizor | Căutare și acces la cererea utilizatorului | Colectare pentru antrenare |
| --- | --- | --- |
| OpenAI | `OAI-SearchBot` pentru căutare; `ChatGPT-User` pentru cereri ale utilizatorilor | `GPTBot` |
| Anthropic | `Claude-SearchBot` și `Claude-User` | `ClaudeBot` |
| Perplexity | `PerplexityBot` și `Perplexity-User` | Documentația precizează că aceste două componente nu colectează pentru antrenarea modelelor de bază |

Permiterea colectării pentru antrenare nu este o condiție pentru optimizările GEO descrise aici. `ChatGPT-User` nu este controlul includerii în ChatGPT Search. [OpenAI Crawlers](https://developers.openai.com/api/docs/bots), [Anthropic Crawlers](https://privacy.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler), [Perplexity Crawlers](https://docs.perplexity.ai/docs/resources/perplexity-crawlers).

Auditul PPW a obținut 200 pentru homepage folosind identificatori declarați ai crawlerelor de căutare. Acesta este un test de acces de bază, nu dovada accesului de la IP-urile reale ale furnizorilor. Dacă apar blocaje confirmate, verifică jurnalele și documentația oficială; eventualele excepții WAF trebuie limitate la identități verificate, nu doar la un nume User-Agent.

### Includerea în funcțiile generative Google

În proprietatea PPW din Search Console, controlul **Search generative AI** moștenește valoarea **Include**. Aceasta era deja activă și a fost păstrată.

Ghidul Google leagă eligibilitatea de indexare, posibilitatea afișării unui fragment de rezultat și includerea site-ului în funcțiile generative. Setarea Include permite participarea; nu confirmă că o pagină a fost deja citată. [Ghidul Google](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide).

## 5. Pașii după publicare

1. Rulează build-ul și publică împreună HTML-ul, stilurile și fișierele generate, inclusiv Echipa și sitemap-ul actualizat.
2. Verifică pe domeniul public răspunsurile 200, canonicalele și accesul la secțiunile noi. Folosește URL Inspection pentru pagini reprezentative.
3. Verifică procesarea sitemap-ului și starea de indexare în Search Console.
4. Urmărește rapoartele de performanță generativă disponibile în Search Console și [AI Performance din Bing Webmaster Tools](https://blogs.bing.com/webmaster/2026/2/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview/).
5. Înregistrează observații de citare cu data, întrebarea, produsul folosit și URL-ul citat. Răspunsurile pot varia între sesiuni și utilizatori.
6. Evaluează și vizitele utile sau solicitările primite. Numărul accesărilor unui crawler nu măsoară singur beneficiul pentru afacere.

Până la redactarea acestui document, nu am măsurat o creștere a citărilor IA și nu am validat noua versiune locală în indexurile furnizorilor.

## 6. Întreținere

```sh
# Regenerează conținutul și rulează verificările SEO și GEO.
npm run build

# Rulează doar verificările GEO, fără regenerare.
npm run check:geo

# Verifică separat metadatele, sitemap-ul și legăturile HTML.
npm run check:seo
```

Editează conținutul HTML sursă, apoi regenerează exporturile. Nu modifica manual fișierele generate pentru a introduce informații care lipsesc din paginile vizibile.

Pentru un articol nou, păstrează sursele, autorul, datele editoriale și navigația coerente. Rendererul și verificările actuale se așteaptă la o secțiune `.post-summary` cu trei concluzii; aceasta este convenția proiectului, nu o regulă impusă de motoarele IA.

La pagini noi, actualizează și lista explicită din regula Cloudflare pentru canonicalele Markdown. Păstrează fișierele administrative din `docs/` în afara pachetului public al site-ului.

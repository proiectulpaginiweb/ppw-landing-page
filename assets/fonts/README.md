# Fonturi locale

DM Sans și Manrope sunt distribuite sub **SIL Open Font License 1.1**. Licențele originale se află în `dm-sans-OFL.txt` și `manrope-OFL.txt` și trebuie publicate împreună cu fonturile.

Fișierele WOFF2 originale provin din serviciul oficial [Google Fonts](https://fonts.googleapis.com/css2?family=DM+Sans:wght@400..700&family=Manrope:wght@400..800&display=swap), descărcate la 13 noiembrie 2026 pentru un browser care acceptă fonturi variabile. Sunt păstrate nemodificate subseturile Latin și Latin-ext, în greutățile 400–700 pentru DM Sans și 400–800 pentru Manrope.

Surse și licențe: [DM Sans](https://github.com/google/fonts/tree/main/ofl/dmsans), [Manrope](https://github.com/google/fonts/tree/main/ofl/manrope).

Fișierele `dm-sans-romanian.woff2` și `manrope-romanian.woff2` sunt subseturi derivate din originalele Latin-ext, pentru `ĂăŞşŢţȘșȚț` (`U+0102–0103`, `U+015E–015F`, `U+0162–0163`, `U+0218–021B`). `ÂâÎî` sunt deja în Latin. Subseturile păstrează intervalele de greutate, contururile și metricile originale. Licențele incluse nu declară nume de font rezervate; numele interne rămân cele originale, iar subseturile sunt distribuite sub aceeași OFL.

`fonts.css` păstrează fețele originale și intervalele Unicode furnizate de Google, cu `font-display: swap`. Fețele românești sunt declarate după originale și au prioritate doar pentru cele zece caractere enumerate. Alte caractere Latin-ext rămân acoperite de fonturile originale, încărcate la nevoie. HTML-ul preîncarcă cele două fonturi Latin și cele două subseturi românești, cu aceleași URL-uri ca în CSS. Încărcarea fonturilor nu depinde de conexiuni la domeniile Google Fonts.

Pentru textul românesc obișnuit, cele două fonturi Latin plus cele două subseturi românești totalizează **55.248 bytes**, față de **114.876 bytes** pentru Latin plus Latin-ext: **59.628 bytes economisiți (51,9%)**. Subseturile românești au **2.372 bytes** (DM Sans) și **2.576 bytes** (Manrope).

Regenerare opțională din rădăcina proiectului, cu [uv](https://docs.astral.sh/uv/):

```sh
uv run --no-project --with 'fonttools[woff]==4.68.0' python scripts/subset_fonts.py
npm run build
```

Scriptul folosește FontTools și Brotli într-un mediu Python izolat; aceste dependențe nu sunt necesare pentru build-ul obișnuit sau servirea site-ului. Verifică acoperirea Unicode, axa variabilă și metricile verticale, apoi compară contururile și lățimile tuturor celor zece caractere la greutățile folosite de site (400, 500, 600, 650, 700, plus 750 și 800 pentru Manrope). Timestampul original este păstrat pentru rezultate reproductibile; două generări consecutive au produs aceleași hashuri SHA-256.

La înlocuirea unui font, păstrează declarațiile Unicode corespunzătoare și rulează `npm run build`. Build-ul actualizează automat numele fizice cu hash din `assets/static/`, URL-urile din CSS-ul publicat și preîncărcările. Păstrează fiecare URL identic între preîncărcare și `@font-face` pentru a reutiliza aceeași cerere.

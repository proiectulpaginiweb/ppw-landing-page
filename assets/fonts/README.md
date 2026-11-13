# Fonturi locale

DM Sans și Manrope sunt distribuite sub **SIL Open Font License 1.1**. Licențele originale se află în `dm-sans-OFL.txt` și `manrope-OFL.txt` și trebuie publicate împreună cu fonturile.

Fișierele WOFF2 provin din serviciul oficial [Google Fonts](https://fonts.googleapis.com/css2?family=DM+Sans:wght@400..700&family=Manrope:wght@400..800&display=swap), descărcate la 13 noiembrie 2026 pentru un browser care acceptă fonturi variabile. Sunt păstrate subseturile Latin și Latin-ext, care includ diacriticele românești, în greutățile 400–700 pentru DM Sans și 400–800 pentru Manrope. Fonturile nu au fost modificate.

Surse și licențe: [DM Sans](https://github.com/google/fonts/tree/main/ofl/dmsans), [Manrope](https://github.com/google/fonts/tree/main/ofl/manrope).

`fonts.css` păstrează intervalele Unicode furnizate de Google și folosește `font-display: swap`. Cele două subseturi Latin sunt preîncărcate din HTML; subseturile Latin-ext sunt solicitate când textul le cere. Astfel, încărcarea textului nu mai depinde de conexiuni la domeniile Google Fonts.

La înlocuirea unui font, păstrează declarațiile Unicode corespunzătoare și rulează `npm run build`. Build-ul actualizează automat hashurile din CSS-ul publicat și din preîncărcări. Păstrează fiecare URL identic între preîncărcare și `@font-face` pentru a reutiliza aceeași cerere.

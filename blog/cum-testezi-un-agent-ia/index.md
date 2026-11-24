# Agentul IA a trecut demo-ul. Cum îl testezi în practică?

Publicat: 2026-11-23

Articol: https://www.proiectulpaginiweb.ro/blog/cum-testezi-un-agent-ia/

Autor: [Proiectul Pagini Web](https://www.proiectulpaginiweb.ro/)

Vineri, agentul pregătește o ofertă impecabilă. Luni, primește un e-mail fără cantități, un produs care nu mai este în stoc și o anexă cu prețurile de anul trecut. Abia acum începe testul interesant: poate să ducă sarcina la capăt și să recunoască momentul în care are nevoie de un om?

## Pe scurt

- Testează rezultatul din sistemele afacerii: oferta salvată, datele corecte și aprobarea respectată. Mesajul final al agentului este doar o parte din evaluare.

- Folosește cereri obișnuite, informații lipsă și instrumente care eșuează. Stabilește dinainte când agentul trebuie să ceară clarificări sau să predea sarcina unui om.

- Măsoară timpul oamenilor, inclusiv verificările și corecturile. Extinde autonomia după un pilot cu criterii explicite și reia testele când schimbi sistemul.

## O ofertă frumoasă poate ascunde o sarcină neterminată

Să presupunem că o firmă primește cereri de ofertă prin e-mail. Un coleg identifică produsele, verifică disponibilitatea, aplică prețurile curente și pregătește un răspuns. Un agent IA ar putea prelua o parte din acești pași, folosind catalogul și aplicația în care firma urmărește relația cu clienții, adică CRM-ul.

În demonstrație, clientul cere trei produse disponibile, toate informațiile sunt complete și fiecare instrument răspunde imediat. Agentul pregătește oferta și anunță că a terminat. Pare convingător. Dar ce se întâmplă dacă documentul există doar în conversație, fără să fie salvat la clientul potrivit?

Evaluarea unui agent trebuie să distingă între conversație și starea finală a sistemului: ce s-a modificat efectiv după execuție. Anthropic descrie această distincție în [ghidul despre evaluarea agenților IA](https://www.anthropic.com/research/demystifying-evals-for-ai-agents). Pentru exemplul nostru, am verifica oferta salvată, asocierea cu cererea și istoricul operațiilor.

Scenariul din acest articol este ilustrativ. Îl folosim ca să construim o metodă de verificare pe care o poți adapta la programări, solicitări de suport sau prelucrarea documentelor.

## Scrie ce înseamnă „gata” înainte să pornești agentul

Pentru primul pilot, aș limita sarcina la pregătirea unui draft de ofertă. Un coleg îl aprobă și îl trimite. Agentul are astfel un obiectiv precis, cu un rezultat pe care îl putem inspecta.

Aș scrie următoarele condiții de acceptare:

- Produsele și cantitățile corespund cererii. Informațiile absente sunt marcate ca lipsă.

- Prețurile provin din catalogul curent, iar disponibilitatea are o sursă și un moment al verificării.

- Calculele respectă regulile comerciale stabilite pentru pilot.

- Draftul este salvat în CRM la clientul și cererea potrivite, o singură dată.

- Trimiterea către client așteaptă aprobarea colegului responsabil.

Dacă agentul descoperă că lipsește cantitatea, poate încheia corect etapa prin pregătirea unei întrebări de clarificare. Un preț total inventat ar fi un eșec, chiar dacă răspunsul sună profesionist. Criteriile trebuie să acopere și situațiile în care sarcina rămâne în așteptare.

## Pune în test și ziua în care lucrurile merg prost

Aș începe cu un lot mic de cereri din activitatea firmei, cu date personale eliminate sau înlocuite pentru test. Aș păstra diversitatea: mesaje scurte, formulări neclare și solicitări care au cerut intervenția unui coleg experimentat. Aș adăuga separat câteva situații construite special pentru a verifica limitele agentului.

### **Lipsește o informație**

Clientul cere „aceeași cantitate ca data trecută”, dar istoricul nu este disponibil. Rezultatul așteptat: agentul marchează lipsa și pregătește o întrebare de clarificare.

### **Sursele se contrazic**

Anexa clientului conține un preț vechi, diferit de cel din catalog. Rezultatul așteptat: draftul folosește sursa stabilită de firmă și semnalează diferența pentru verificare.

### **Un instrument nu răspunde**

Serviciul de stocuri este indisponibil. Rezultatul așteptat: disponibilitatea rămâne neconfirmată, iar oferta nu promite o livrare bazată pe o presupunere.

### **Operația este reluată**

Salvarea în CRM reușește, dar confirmarea se pierde. Rezultatul așteptat: sistemul verifică operația existentă înainte să încerce din nou și evită un draft duplicat.

Pentru fiecare caz, notează intrarea, datele la care agentul are acces și rezultatul acceptabil. Păstrează câteva cereri deoparte, fără să le folosești la ajustarea instrucțiunilor. Ele te ajută să vezi cum se comportă versiunea nouă pe exemple pe care nu ai optimizat-o direct.

## Verifică separat calculele, deciziile și explicațiile

În oferta noastră, un program obișnuit poate verifica totalul, codurile produselor și existența draftului în CRM. Un coleg care cunoaște procesul poate judeca dacă întrebarea de clarificare este utilă și dacă agentul a ales corect momentul de predare.

Un alt model IA poate ajuta la evaluarea textelor, folosind criterii explicite și exemple de răspunsuri acceptate. Verdictul lui trebuie comparat periodic cu evaluările oamenilor. [Ghidul OpenAI despre bune practici de evaluare](https://developers.openai.com/api/docs/guides/evaluation-best-practices) recomandă calibrarea măsurătorilor automate cu feedback uman și avertizează asupra evaluărilor bazate doar pe impresia că sistemul funcționează.

Aș testa de mai multe ori cazurile importante, pornind de fiecare dată din aceeași stare. Aș privi separat ofertele complete, cererile de clarificare și erorile instrumentelor. O medie bună poate ascunde o problemă repetată exact la clienții cu solicitări mai complicate.

## Cât timp rămâne de muncit după răspunsul agentului?

Agentul termină în câteva secunde. Colegul petrece apoi zece minute verificând fiecare număr. Într-un asemenea caz, viteza răspunsului spune prea puțin despre economia de timp a firmei.

Să luăm un **calcul strict ilustrativ**. Pentru zece cereri comparabile, procesul manual ocupă în total 120 de minute. Cu agentul, oamenii petrec 50 de minute verificând drafturile, 20 corectând erori și 10 rezolvând excepții. Rămân 80 de minute de muncă umană, deci o economie de 40 de minute în acest lot.

Abonamentele, apelurile către modele, integrarea și întreținerea se adaugă evaluării economice. Timpii de mai sus nu sunt rezultate măsurate de Proiectul Pagini Web și nu prezic economia unui proiect real. Pentru o decizie, aș măsura procesul actual și pilotul pe cereri cu dificultate comparabilă, la același nivel de calitate.

## Dă-i o responsabilitate pe care o poți urmări

Aș porni pilotul într-un mediu de test, cu copii ale datelor și instrumente controlate. După verificarea scenariilor, l-aș folosi pentru drafturi pe un segment restrâns de cereri, cu aprobarea fiecărei oferte. Aș stabili cine preia excepțiile și cum poate opri pilotul dacă apare o problemă.

Înainte de pornire, echipa ar decide câtă muncă de verificare acceptă și ce erori blochează extinderea. De exemplu, o ofertă trimisă fără aprobare ar opri pilotul pentru investigare. Numărul de cazuri și durata testului se aleg după varietatea cererilor și consecințele unei greșeli; un lot mic reușit nu demonstrează că erorile rare au dispărut.

O fișă simplă poate urmări pentru fiecare cerere: rezultatul, timpul de verificare, corecturile, intervenția umană și motivul ei. Când mai multe cazuri se blochează la aceeași informație absentă, poate merita îmbunătățit formularul de cerere sau catalogul de produse.

## Păstrează testele și după prima versiune bună

Instrucțiunile, modelul și instrumentele se pot schimba. O modificare care ajută cererile simple poate strica tratarea unei excepții. OpenAI recomandă [reluarea evaluărilor la schimbări și extinderea setului de teste cu situații descoperite în utilizare](https://developers.openai.com/api/docs/guides/evaluation-best-practices).

Pentru agentul de ofertare, aș păstra versiunile configurației și aș relua cazurile cunoscute înainte de fiecare actualizare. Aș adăuga problemele noi în setul de test, după ce un coleg stabilește comportamentul corect. În utilizarea curentă, aș urmări dacă economia de timp și calitatea se mențin.

Dacă te gândești la un agent pentru afacerea ta, începe cu o sarcină repetitivă și câteva exemple dintr-o săptămână obișnuită. Scrie ce rezultat ar accepta colegul care o face astăzi. De aici poți construi un pilot ale cărui rezultate merită discutate.

**Citește și**

- [Chat AI și agent AI: care este diferența?](https://www.proiectulpaginiweb.ro/blog/diferenta-dintre-chat-ia-si-agent-ia/)

- [Următorul pas în IA este antrenarea modelelor pentru afacerea ta](https://www.proiectulpaginiweb.ro/blog/antrenarea-modelelor-ia-pentru-afaceri/)

- [Ce este MCP? Cum conectezi agenții IA la datele firmei](https://www.proiectulpaginiweb.ro/blog/ce-este-mcp-model-context-protocol/)

[Proiectul Pagini Web](https://www.proiectulpaginiweb.ro/)

[← Înapoi la blog](https://www.proiectulpaginiweb.ro/blog/)

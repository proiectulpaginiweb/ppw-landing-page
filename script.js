const menuButton = document.querySelector(".menu-toggle");
const navigation = document.querySelector("#navigation");
function closeMenu() {
  menuButton.setAttribute("aria-expanded", "false");
  navigation.classList.remove("is-open");
}
menuButton.addEventListener("click", () => {
  const open = menuButton.getAttribute("aria-expanded") !== "true";
  menuButton.setAttribute("aria-expanded", String(open));
  navigation.classList.toggle("is-open", open);
});
navigation
  .querySelectorAll("a")
  .forEach((link) => link.addEventListener("click", closeMenu));
document.addEventListener("keydown", (event) => {
  if (
    event.key === "Escape" &&
    menuButton.getAttribute("aria-expanded") === "true"
  ) {
    closeMenu();
    menuButton.focus();
  }
});
const steps = [
  {
    label: "DESCOPERIM / 01",
    title: "O problemă reală.\nUn prim pas util.",
    description:
      "Analizăm împreună modul în care lucrezi, identificăm dificultățile și alegem o situație concretă în care AI poate ajuta. Stabilim cum arată un rezultat mai bun înainte să decidem ce construim.",
    output:
      "Un caz de utilizare clar, un criteriu de succes și un plan practic.",
  },
  {
    label: "PROIECTĂM / 02",
    title: "O idee pe care\no poți testa.",
    description:
      "Construim un prototip pornind de la modul în care lucrezi. Echipa ta poate vedea cum funcționează, unde ajută și unde este nevoie de intervenția unui om, înainte de o implementare mai amplă.",
    output:
      "Un prototip concret, primele impresii ale echipei și o direcție comună.",
  },
  {
    label: "CONSTRUIM / 03",
    title: "Integrăm soluția\nîn munca ta.",
    description:
      "Dezvoltăm soluția, conectăm instrumentele și informațiile agreate și testăm situații reale. Permisiunile, verificările și comportamentul în caz de eroare sunt stabilite de la început.",
    output:
      "Un proiect-pilot funcțional, limite clare și un plan de implementare.",
  },
  {
    label: "CREȘTEM / 04",
    title: "Învățăm din practică.\nAlegem următorul pas.",
    description:
      "Evaluăm proiectul-pilot în raport cu obiectivele stabilite. Îmbunătățim ce contează, ajutăm echipa să adopte noul mod de lucru și decidem împreună dacă urmează ajustarea sau extinderea soluției.",
    output:
      "Un plan de îmbunătățire bazat pe rezultate și o echipă pregătită pentru pasul următor.",
  },
];
const tabs = [...document.querySelectorAll('[role="tab"]')];
function selectStep(index, focus = false) {
  tabs.forEach((tab, i) => {
    tab.setAttribute("aria-selected", String(i === index));
    tab.tabIndex = i === index ? 0 : -1;
  });
  const step = steps[index];
  document.querySelector("#journey-label").textContent = step.label;
  const title = document.querySelector("#journey-title");
  title.replaceChildren();
  step.title.split("\n").forEach((line, i) => {
    if (i) title.append(document.createElement("br"));
    title.append(document.createTextNode(line));
  });
  document.querySelector("#journey-description").textContent = step.description;
  document.querySelector("#journey-output").textContent = step.output;
  document
    .querySelector("#journey-panel")
    .setAttribute("aria-labelledby", tabs[index].id);
  if (focus) tabs[index].focus();
}
tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectStep(index));
  tab.addEventListener("keydown", (event) => {
    let next;
    if (event.key === "ArrowDown") next = (index + 1) % tabs.length;
    if (event.key === "ArrowUp") next = (index + tabs.length - 1) % tabs.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = tabs.length - 1;
    if (next !== undefined) {
      event.preventDefault();
      selectStep(next, true);
    }
  });
});
document.querySelector("#year").textContent = new Date().getFullYear();
const contactForm = document.querySelector("#contact-form");
const submitButton = contactForm.querySelector('button[type="submit"]');
const formStatus = document.querySelector("#form-status");
contactForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (submitButton.disabled || !contactForm.reportValidity()) return;

  const data = new FormData(contactForm);
  const name = String(data.get("name")).trim();
  const email = String(data.get("email")).trim();
  const interest = String(data.get("interest"));
  const message = String(data.get("message")).trim();
  data.set("name", name);
  data.set("email", email);
  data.set("subject", `Solicitare Proiectul Pagini Web: ${interest}`);
  data.set(
    "message",
    `Nume: ${name}\nE-mail: ${email}\nMă interesează: ${interest}\n\nCe aș vrea să îmbunătățesc:\n${message}`,
  );

  const originalContent = submitButton.innerHTML;
  submitButton.textContent = "Se trimite…";
  submitButton.disabled = true;
  contactForm.setAttribute("aria-busy", "true");
  formStatus.textContent = "Mesajul tău se trimite…";
  formStatus.dataset.state = "sending";

  try {
    const response = await fetch(contactForm.action, {
      method: "POST",
      body: data,
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(30000),
    });
    const result = await response.json();
    if (!response.ok || result.success !== true) {
      throw new Error("Trimiterea a eșuat");
    }
    contactForm.reset();
    formStatus.textContent =
      "Mulțumim! Mesajul tău a fost trimis. Vom reveni cu un răspuns.";
    formStatus.dataset.state = "success";
  } catch {
    formStatus.textContent =
      "Nu am putut confirma trimiterea mesajului. Datele tale au fost păstrate. Te rugăm să încerci din nou în câteva momente.";
    formStatus.dataset.state = "error";
  } finally {
    submitButton.innerHTML = originalContent;
    submitButton.disabled = false;
    contactForm.removeAttribute("aria-busy");
  }
});

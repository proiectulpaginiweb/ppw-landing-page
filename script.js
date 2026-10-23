const menuButton = document.querySelector(".menu-toggle");
const navigation = document.querySelector("#navigare");
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
const tabs = [...document.querySelectorAll('[role="tab"]')];
function selectStep(index, focus = false) {
  tabs.forEach((tab, i) => {
    tab.setAttribute("aria-selected", String(i === index));
    tab.tabIndex = i === index ? 0 : -1;
  });
  tabs.forEach((tab, i) => {
    document.getElementById(tab.getAttribute("aria-controls")).hidden =
      i !== index;
  });
  if (focus) tabs[index].focus();
}
selectStep(0);
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
document.querySelector("#an").textContent = new Date().getFullYear();
const contactForm = document.querySelector("#formular-contact");
const submitButton = contactForm.querySelector('button[type="submit"]');
const formStatus = document.querySelector("#stare-formular");
contactForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (submitButton.disabled || !contactForm.reportValidity()) return;

  const data = new FormData(contactForm);
  const name = String(data.get("name")).trim();
  const email = String(data.get("email")).trim();
  const phone = String(data.get("phone") || "").trim();
  const interest = String(data.get("interest"));
  const message = String(data.get("message")).trim();
  data.set("name", name);
  data.set("email", email);
  data.set("phone", phone);
  data.set("subject", `Solicitare Proiectul Pagini Web: ${interest}`);
  data.set(
    "message",
    `Nume: ${name}\nE-mail: ${email}\n${phone ? `Telefon: ${phone}\n` : ""}Mă interesează: ${interest}\n\nCe aș vrea să îmbunătățesc:\n${message}`,
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

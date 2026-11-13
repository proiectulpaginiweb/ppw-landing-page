// Google Analytics: doar pe domeniile de producție, după încărcarea paginii.
(() => {
  const productionHosts = [
    "www.proiectulpaginiweb.ro",
    "proiectulpaginiweb.ro",
  ];
  if (
    window.location.protocol !== "https:" ||
    window.location.port !== "" ||
    !productionHosts.includes(window.location.hostname)
  ) return;

  window.dataLayer = window.dataLayer || [];
  window.gtag = function () { window.dataLayer.push(arguments); };
  window.gtag("js", new Date());
  window.gtag("config", "G-01VJRQR4TT");

  function loadGoogleTag() {
    const tag = document.createElement("script");
    tag.async = true;
    tag.fetchPriority = "low";
    tag.src = "https://www.googletagmanager.com/gtag/js?id=G-01VJRQR4TT";
    document.head.appendChild(tag);
  }
  function scheduleGoogleTag() {
    if ("requestIdleCallback" in window) {
      window.requestIdleCallback(loadGoogleTag, { timeout: 2000 });
    } else {
      window.setTimeout(loadGoogleTag, 0);
    }
  }
  if (document.readyState === "complete") {
    scheduleGoogleTag();
  } else {
    window.addEventListener("load", scheduleGoogleTag, { once: true });
  }
})();

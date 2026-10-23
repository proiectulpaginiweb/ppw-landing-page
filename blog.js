const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('#navigare');
function closeMenu() {
  menuButton.setAttribute('aria-expanded', 'false');
  navigation.classList.remove('is-open');
}
menuButton.addEventListener('click', () => {
  const open = menuButton.getAttribute('aria-expanded') !== 'true';
  menuButton.setAttribute('aria-expanded', String(open));
  navigation.classList.toggle('is-open', open);
});
navigation.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && menuButton.getAttribute('aria-expanded') === 'true') {
    closeMenu();
    menuButton.focus();
  }
});

// Official share widgets load when the share section approaches the viewport.
const shareSection = document.querySelector('[data-share]');
if (shareSection) {
  const canonical = document.querySelector('link[rel="canonical"]')?.href || window.location.href.split('#')[0];
  const title = document.querySelector('meta[property="og:title"]')?.content || document.title;
  const encodedUrl = encodeURIComponent(canonical);
  const widgetArea = shareSection.querySelector('[data-share-widgets]');
  function loadShareWidgets() {
    const linkedIn = widgetArea.querySelector('[data-widget="linkedin"]');
    const linkedInButton = document.createElement('script');
    linkedInButton.type = 'IN/Share';
    linkedInButton.setAttribute('data-url', canonical);
    linkedIn.append(linkedInButton);
    const linkedInScript = document.createElement('script');
    linkedInScript.src = 'https://platform.linkedin.com/in.js';
    linkedInScript.textContent = 'lang: ro_RO';
    linkedIn.append(linkedInScript);

    const x = widgetArea.querySelector('[data-widget="x"]');
    const xButton = document.createElement('a');
    xButton.href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodedUrl}`;
    xButton.className = 'twitter-share-button';
    xButton.dataset.url = canonical;
    xButton.dataset.text = title;
    xButton.dataset.showCount = 'false';
    xButton.textContent = 'Postează pe X';
    x.append(xButton);
    const xScript = document.createElement('script');
    xScript.src = 'https://platform.x.com/widgets.js';
    xScript.async = true;
    xScript.charset = 'utf-8';
    x.append(xScript);

    const facebook = widgetArea.querySelector('[data-widget="facebook"]');
    const facebookFrame = document.createElement('iframe');
    facebookFrame.title = 'Distribuie pe Facebook';
    facebookFrame.src = `https://www.facebook.com/plugins/share_button.php?href=${encodedUrl}&layout=button&size=small&width=68&height=28`;
    facebookFrame.width = '68';
    facebookFrame.height = '28';
    facebookFrame.loading = 'lazy';
    facebookFrame.allow = 'clipboard-write; encrypted-media; web-share';
    facebookFrame.style.border = '0';
    facebookFrame.style.overflow = 'hidden';
    facebook.append(facebookFrame);
    widgetArea.classList.add('is-loaded');
  }
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) {
        observer.disconnect();
        loadShareWidgets();
      }
    }, { rootMargin: '300px' });
    observer.observe(widgetArea);
  } else {
    loadShareWidgets();
  }
  const status = shareSection.querySelector('.post-share-status');
  const copyButton = shareSection.querySelector('[data-copy-link]');
  const copyIcon = copyButton.querySelector('[data-copy-icon]');
  let resetCopyIcon;
  copyButton.addEventListener('click', async () => {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(canonical);
      clearTimeout(resetCopyIcon);
      copyIcon.textContent = '✓';
      copyButton.classList.add('is-copied');
      status.classList.add('is-visually-hidden');
      status.textContent = 'Linkul a fost copiat.';
      resetCopyIcon = setTimeout(() => {
        copyIcon.textContent = '⧉';
        copyButton.classList.remove('is-copied');
        status.textContent = '';
        status.classList.remove('is-visually-hidden');
      }, 2500);
    } catch {
      status.classList.remove('is-visually-hidden');
      status.textContent = `Copierea automată nu este disponibilă. Selectează linkul: ${canonical}`;
    }
  });
}

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

// Keep shared links to earlier section names working after URL translation.
function updateLegacyFragment() {
  const fragment = location.hash.slice(1);
  const heading = [...document.querySelectorAll('[data-ancora-veche]')]
    .find(node => node.dataset.ancoraVeche === fragment);
  if (heading) {
    history.replaceState(null, '', location.pathname + location.search + '#' + heading.id);
    heading.scrollIntoView();
  }
}
updateLegacyFragment();
window.addEventListener('hashchange', updateLegacyFragment);

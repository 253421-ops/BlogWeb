// Muestra la página que indica el enlace (#inicio, #historia, etc.)
const pages = document.querySelectorAll('.page');
const links = document.querySelectorAll('.dock a');

function show() {
  const id = location.hash.slice(1) || 'inicio';
  const exists = document.getElementById(id);
  const active = exists ? id : 'inicio';

  pages.forEach(p => p.classList.toggle('on', p.id === active));
  links.forEach(a => {
    if (a.dataset.p === active) a.setAttribute('aria-current', 'page');
    else a.removeAttribute('aria-current');
  });
  window.scrollTo(0, 0);
}

window.addEventListener('hashchange', show);
show();

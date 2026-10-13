/* FEWK fifth-edition reader. Existing third-edition routes remain in index.html. */
let manifest;
let files = new Set();
let currentPage = '';
let loadSequence = 0;
const searches = [];
const topPages = {home: 'content/fifth/home.md', roadmap: 'content/roadmap.md', license: 'content/license.md'};
const escapeHTML = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pageFile = page => topPages[page] || 'content/' + page + '.md';

function navigateTo(page) { location.hash = page; }
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem('fewk-theme', theme);
  document.getElementById('themeIcon').textContent = theme === 'dark' ? '☀️' : '🌙';
  document.getElementById('themeLabel').textContent = theme === 'dark' ? '라이트 모드' : '다크 모드';
}
function toggleTheme() { applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'); }
function openCommentModal() { document.getElementById('commentModal').classList.add('open'); document.getElementById('commentText').focus(); }
function closeCommentModal() { document.getElementById('commentModal').classList.remove('open'); }
function sendComment() {
  const message = document.getElementById('commentText').value.trim();
  if (!message) return;
  location.href = 'mailto:FEWK@meje.kr?subject=' + encodeURIComponent('[FEWK 제5판] '+currentPage) + '&body=' + encodeURIComponent(location.href+'\n\n'+message);
  closeCommentModal();
}

function routeParts() {
  const raw = decodeURIComponent(location.hash.slice(1)) || 'home';
  const separator = raw.indexOf('#');
  return separator < 0 ? [raw, ''] : [raw.slice(0, separator), raw.slice(separator + 1)];
}
function scrollAnchor(anchor) {
  if (!anchor) { window.scrollTo({top:0, behavior:'instant'}); return; }
  const target = document.getElementById(anchor);
  if (target) target.scrollIntoView({block:'start', behavior:'instant'});
}
function rewriteLinks(container, page) {
  const contentBase = new URL('content/', location.href.split('#')[0]);
  const current = new URL(pageFile(page), location.href.split('#')[0]);
  for (const link of container.querySelectorAll('a[href]')) {
    const href = link.getAttribute('href');
    if (/^(https?:|mailto:)/i.test(href)) { link.rel = 'noopener'; continue; }
    if (href.startsWith('#')) { link.href = '#'+page+href; continue; }
    const resolved = new URL(href, current);
    const decoded = decodeURIComponent(resolved.pathname);
    const base = decodeURIComponent(contentBase.pathname);
    if (decoded.startsWith(base)) {
      const relative = 'content/'+decoded.slice(base.length);
      if (files.has(relative)) {
        link.href = relative.endsWith('.md') ? '#'+relative.slice(8,-3)+resolved.hash : resolved.href;
        continue;
      }
    }
    // Original manuscripts may cite separately maintained editorial/source collections.
    // Retain their names without pretending that those files are published here.
    const note = document.createElement('span');
    note.className = 'separate-reference';
    note.textContent = link.textContent + ' (별도 자료)';
    note.title = '이 독서기에는 포함되지 않은 출처·편집 자료입니다.';
    link.replaceWith(note);
  }
}
function addContents(container) {
  const headings = [...container.querySelectorAll('h2, h3')];
  if (headings.length < 4) return;
  const details = document.createElement('details');
  details.className = 'page-contents';
  const summary = document.createElement('summary');
  summary.textContent = '이 문서의 목차 ('+headings.length+')';
  details.append(summary);
  const list = document.createElement('ul');
  headings.forEach((heading, index) => {
    if (!heading.id) heading.id = 'section-'+index;
    const item = document.createElement('li');
    const link = document.createElement('a');
    link.href = '#'+currentPage+'#'+heading.id;
    link.textContent = heading.textContent;
    item.append(link); list.append(item);
  });
  details.append(list);
  const first = container.querySelector('h1');
  if (first) first.after(details); else container.prepend(details);
}
async function loadPage() {
  const [page, anchor] = routeParts();
  if (page.startsWith('corerulebook/') || page.startsWith('worldbook/')) {
    location.replace('index.html#'+page+(anchor ? '#'+anchor : '')); return;
  }
  if (currentPage === page) { scrollAnchor(anchor); return; }
  const sequence = ++loadSequence;
  const container = document.getElementById('content');
  container.innerHTML = '<div class="loading">로딩 중</div>';
  try {
    const file = pageFile(page);
    if (!files.has(file)) throw new Error('Unknown document');
    const response = await fetch(file, {cache: 'no-cache'});
    if (!response.ok) throw new Error('HTTP '+response.status);
    const md = await response.text();
    if (sequence !== loadSequence) return;
    currentPage = page;
    container.innerHTML = marked.parse(md);
    for (const table of container.querySelectorAll('table')) {
      const wrapper = document.createElement('div'); wrapper.className = 'table-wrap';
      table.before(wrapper); wrapper.append(table);
    }
    rewriteLinks(container, page);
    addContents(container);
    if (window.FEWKArt) {
      try {
        await window.FEWKArt.load();
        if (sequence !== loadSequence) return;
        window.FEWKArt.render(container, page);
      } catch (error) { console.warn('Artwork could not be loaded', error); }
    }
    const doc = manifest.documents.find(item => item.page === page);
    document.getElementById('breadcrumb').textContent = 'FEWK 제5판 / '+(doc ? doc.title : page === 'home' ? '읽기 안내' : page.split('/').pop().replaceAll('_',' '));
    document.querySelectorAll('.nav-link[data-page]').forEach(link => link.classList.toggle('active', link.dataset.page === page));
    document.querySelector('.sidebar').classList.remove('open');
    requestAnimationFrame(() => scrollAnchor(anchor));
  } catch (error) {
    if (sequence !== loadSequence) return;
    currentPage = '';
    container.innerHTML = '<h2>문서를 불러오지 못했습니다</h2><p><a href="#home">읽기 안내로 돌아가기</a></p>';
  }
}

function runSearch(query) {
  const results = document.getElementById('searchResults');
  query = query.trim().toLocaleLowerCase();
  if (!query) { results.classList.remove('open'); return; }
  const matches = searches.filter(item => item.title.toLocaleLowerCase().includes(query)).slice(0,30);
  results.innerHTML = matches.length ? matches.map(item => '<a class="search-result" href="#'+escapeHTML(item.page)+'">'+escapeHTML(item.title)+'</a>').join('') : '<div class="search-empty">결과 없음</div>';
  results.classList.add('open');
}
async function indexHeadings(doc) {
  const response = await fetch(doc.file, {cache: 'no-cache'});
  if (!response.ok) return;
  const host = document.createElement('div');
  host.innerHTML = marked.parse(await response.text());
  for (const [index, heading] of [...host.querySelectorAll('h2, h3')].entries()) {
    searches.push({title:doc.title+' · '+heading.textContent, page:doc.page+'#'+(heading.id || 'section-'+index)});
  }
}
async function init() {
  applyTheme(localStorage.getItem('fewk-theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  const response = await fetch('content/fifth/manifest.json', {cache: 'no-cache'});
  if (!response.ok) throw new Error('Manifest unavailable');
  manifest = await response.json();
  files = new Set([...manifest.files.map(item => item.path), ...Object.values(topPages)]);
  document.getElementById('navMenu').innerHTML = '<div class="nav-part">제5판 · 두 권과 지원 자료</div>'+manifest.documents.map(doc => '<a class="nav-link sub" data-page="'+escapeHTML(doc.page)+'" href="#'+escapeHTML(doc.page)+'">'+escapeHTML(doc.title)+'</a>').join('')+'<a class="nav-link" href="index.html">기존 3판 독서기 ↗</a>';
  searches.push(...manifest.documents.map(doc => ({title:doc.title+' · '+doc.description, page:doc.page})));
  document.getElementById('searchInput').addEventListener('input', event => runSearch(event.target.value));
  document.getElementById('searchResults').addEventListener('click', () => document.getElementById('searchResults').classList.remove('open'));
  window.addEventListener('hashchange', loadPage);
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeCommentModal(); });
  await loadPage();
  await Promise.allSettled(manifest.documents.map(indexHeadings));
  window.fewkSearchReady = true;
}
init().catch(() => { document.getElementById('content').textContent = '자료 목록을 불러오지 못했습니다. 새로고침해 주세요.'; });

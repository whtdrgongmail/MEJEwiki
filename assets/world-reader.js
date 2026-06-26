const state = {
  manifest: null,
  files: [],
  current: null
};

const titleEl = document.getElementById('world-title');
const metaEl = document.getElementById('world-meta');
const tocEl = document.getElementById('toc');
const searchEl = document.getElementById('search');
const docEl = document.getElementById('doc');
const pathEl = document.getElementById('doc-path');
const heroEl = document.getElementById('hero');
const heroImageEl = document.getElementById('hero-image');

const escapeHtml = (value) => value
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;');

const inlineMarkdown = (value) => escapeHtml(value)
  .replace(/`([^`]+)`/g, '<code>$1</code>')
  .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');

function tableToHtml(lines) {
  const rows = lines.map((line) => line.trim().replace(/^\||\|$/g, '').split('|').map((cell) => inlineMarkdown(cell.trim())));
  const head = rows[0] || [];
  const body = rows.slice(2);
  return `<table><thead><tr>${head.map((cell) => `<th>${cell}</th>`).join('')}</tr></thead><tbody>${body.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
}

function markdownToHtml(markdown) {
  const lines = markdown.replace(/\r\n/g, '\n').split('\n');
  const html = [];
  let paragraph = [];
  let list = null;
  let quote = [];
  let code = null;
  let table = [];

  const flushParagraph = () => {
    if (paragraph.length) {
      html.push(`<p>${inlineMarkdown(paragraph.join(' '))}</p>`);
      paragraph = [];
    }
  };
  const flushList = () => {
    if (list) {
      html.push(`<${list.type}>${list.items.map((item) => `<li>${inlineMarkdown(item)}</li>`).join('')}</${list.type}>`);
      list = null;
    }
  };
  const flushQuote = () => {
    if (quote.length) {
      html.push(`<blockquote>${quote.map((line) => `<p>${inlineMarkdown(line)}</p>`).join('')}</blockquote>`);
      quote = [];
    }
  };
  const flushTable = () => {
    if (table.length) {
      html.push(tableToHtml(table));
      table = [];
    }
  };
  const flushBlocks = () => {
    flushParagraph();
    flushList();
    flushQuote();
    flushTable();
  };

  for (const line of lines) {
    if (code) {
      if (line.startsWith('```')) {
        html.push(`<pre><code>${escapeHtml(code.lines.join('\n'))}</code></pre>`);
        code = null;
      } else {
        code.lines.push(line);
      }
      continue;
    }

    if (line.startsWith('```')) {
      flushBlocks();
      code = { lines: [] };
      continue;
    }

    if (!line.trim()) {
      flushBlocks();
      continue;
    }

    if (/^\|.+\|$/.test(line.trim())) {
      flushParagraph();
      flushList();
      flushQuote();
      table.push(line);
      continue;
    } else {
      flushTable();
    }

    const heading = line.match(/^(#{1,4})\s+(.+)$/);
    if (heading) {
      flushBlocks();
      const level = heading[1].length;
      html.push(`<h${level}>${inlineMarkdown(heading[2])}</h${level}>`);
      continue;
    }

    if (/^---+$/.test(line.trim())) {
      flushBlocks();
      html.push('<hr>');
      continue;
    }

    const quoteMatch = line.match(/^>\s?(.*)$/);
    if (quoteMatch) {
      flushParagraph();
      flushList();
      quote.push(quoteMatch[1]);
      continue;
    }

    const ordered = line.match(/^\d+[.)]\s+(.+)$/);
    const unordered = line.match(/^[-*]\s+(.+)$/);
    if (ordered || unordered) {
      flushParagraph();
      flushQuote();
      const type = ordered ? 'ol' : 'ul';
      const item = ordered ? ordered[1] : unordered[1];
      if (!list || list.type !== type) {
        flushList();
        list = { type, items: [] };
      }
      list.items.push(item);
      continue;
    }

    paragraph.push(line.trim());
  }

  flushBlocks();
  if (code) {
    html.push(`<pre><code>${escapeHtml(code.lines.join('\n'))}</code></pre>`);
  }
  return html.join('\n');
}

function renderToc(items) {
  tocEl.innerHTML = items.map((file) => {
    const active = state.current && file.path === state.current.path ? ' active' : '';
    return `<a class="${active}" href="#${encodeURIComponent(file.path)}">${file.title}</a>`;
  }).join('');
}

function filterToc() {
  const query = searchEl.value.trim().toLowerCase();
  const items = state.files.filter((file) => `${file.path} ${file.title}`.toLowerCase().includes(query));
  renderToc(items);
}

function setHero(image, alt) {
  if (!image) {
    heroEl.hidden = true;
    heroImageEl.removeAttribute('src');
    heroImageEl.alt = '';
    return;
  }

  heroImageEl.src = image;
  heroImageEl.alt = alt || `${state.manifest.title} illustration`;
  heroEl.hidden = false;
}

function setHeroForFile(file) {
  const illustration = state.manifest.illustrations?.[file.path];
  setHero(
    illustration?.image || state.manifest.heroImage,
    illustration?.alt || state.manifest.heroAlt || `${state.manifest.title} hero image`
  );
}

async function loadFile(file) {
  state.current = file;
  renderToc(state.files.filter((item) => {
    const query = searchEl.value.trim().toLowerCase();
    return `${item.path} ${item.title}`.toLowerCase().includes(query);
  }));
  setHeroForFile(file);
  pathEl.textContent = file.path;
  docEl.innerHTML = '<p class="empty">Loading...</p>';
  const response = await fetch(encodeURI(file.path));
  if (!response.ok) {
    docEl.innerHTML = '<p class="empty">문서를 불러오지 못했습니다.</p>';
    return;
  }
  const markdown = await response.text();
  docEl.innerHTML = markdownToHtml(markdown);
}

function syncHash() {
  const requested = decodeURIComponent(location.hash.replace(/^#/, ''));
  const file = state.files.find((item) => item.path === requested) || state.files[0];
  if (file) loadFile(file);
}

async function init() {
  const response = await fetch('./manifest.json');
  state.manifest = await response.json();
  state.files = state.manifest.files;
  titleEl.textContent = state.manifest.title;
  document.title = `${state.manifest.title} - MEJEwiki`;
  metaEl.textContent = `${state.manifest.version} / ${state.files.length} documents`;
  setHero(state.manifest.heroImage, state.manifest.heroAlt);
  renderToc(state.files);
  syncHash();
}

searchEl.addEventListener('input', filterToc);
window.addEventListener('hashchange', syncHash);

init().catch(() => {
  titleEl.textContent = 'World Reader';
  docEl.innerHTML = '<p class="empty">세계관 manifest를 불러오지 못했습니다.</p>';
});

/* Shared illustration catalogue, reader placement and full-image viewer. */
(() => {
  'use strict';
  let pending, catalogue, dialog, active = [], position = 0;
  const make = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  };
  function load() {
    if (!pending) pending = fetch('assets/fifth-art/manifest.json', {cache:'no-cache'})
      .then(response => { if (!response.ok) throw new Error('Artwork unavailable'); return response.json(); })
      .then(data => { catalogue = data; return data; });
    return pending;
  }
  function readerURL(asset) {
    const p = asset.placements[0];
    return p ? 'fifth-edition.html#'+p.page+(p.anchor ? '#'+p.anchor : '') : '';
  }
  function card(asset, large = false) {
    const figure = make('figure', 'art-card'+(large ? ' art-feature' : '')+(asset.transparent ? ' art-transparent' : ''));
    figure.dataset.artId = asset.id;
    const link = make('a', 'art-image-link');
    link.href = asset.src;
    if (!large) link.style.aspectRatio = asset.width+' / '+asset.height;
    link.dataset.artId = asset.id;
    link.setAttribute('aria-label', asset.title+' 크게 보기');
    const img = make('img');
    img.src = large ? asset.src : asset.thumb;
    img.width = asset.width; img.height = asset.height;
    img.alt = asset.title;
    img.loading = 'lazy'; img.decoding = 'async';
    link.append(img);
    const caption = make('figcaption');
    caption.append(make('strong', '', asset.title));
    if (asset.description) caption.append(make('span', '', asset.description));
    figure.append(link, caption);
    return figure;
  }
  function collection(assets, title = '관련 이미지') {
    const section = make('section', 'art-collection art-related');
    section._artAssets = assets;
    section.setAttribute('aria-label', title);
    const header = make('div', 'art-section-title', title+' · '+assets.length);
    const grid = make('div', 'art-grid');
    assets.slice(0,4).forEach(asset => grid.append(card(asset)));
    section.append(header, grid);
    if (assets.length > 4) {
      const details = make('details', 'art-more');
      details.append(make('summary', '', '이미지 '+(assets.length-4)+'장 더 보기'));
      let populated = false;
      details.addEventListener('toggle', () => {
        if (!details.open || populated) return;
        populated = true;
        const rest = make('div', 'art-grid');
        assets.slice(4).forEach(asset => rest.append(card(asset)));
        details.append(rest);
      });
      section.append(details);
    }
    return section;
  }
  function rootChild(node, container) {
    while (node && node.parentElement !== container) node = node.parentElement;
    return node;
  }
  function chapterHeading(anchor, container) {
    let node = rootChild(anchor, container);
    for (let i = 0; node && i < 4; i++, node = node.nextElementSibling) {
      if (/^H[1-6]$/.test(node.tagName)) return node;
    }
    return null;
  }
  function boundary(heading) {
    const level = Number(heading.tagName[1]);
    let node = heading.nextElementSibling;
    while (node) {
      if (/^H[1-6]$/.test(node.tagName) && Number(node.tagName[1]) <= level) {
        const previous = node.previousElementSibling;
        // Keep an explicit manuscript anchor immediately before its heading.
        if (previous && (previous.matches('a[id]') || (previous.querySelector('a[id]') && !previous.textContent.trim()))) return previous;
        return node;
      }
      node = node.nextElementSibling;
    }
    return null;
  }
  function render(container, page) {
    if (!catalogue) return;
    const groups = new Map();
    for (const asset of catalogue.assets) for (const placement of asset.placements) {
      if (placement.page !== page) continue;
      const key = placement.anchor;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push({asset, role:placement.role});
    }
    for (const [anchor, entries] of groups) {
      const target = anchor ? container.querySelector('#'+CSS.escape(anchor)) : container.querySelector('h1');
      const heading = anchor ? chapterHeading(target, container) : target;
      if (!heading) continue;
      const end = boundary(heading);
      const features = entries.filter(entry => entry.role === 'hero' || entry.role === 'feature');
      let after = heading;
      for (const {asset, role} of features) {
        const feature = make('div', 'art-collection art-'+role);
        feature._artAssets = [asset];
        feature.append(card(asset, true));
        after.after(feature); after = feature;
      }
      const related = entries.filter(entry => entry.role === 'gallery').map(entry => entry.asset);
      if (related.length) {
        const section = collection(related, related.every(a => a.character) ? '등장인물' : '이 장의 이미지');
        container.insertBefore(section, end);
      }
    }
    const link = make('a', 'art-catalogue-link', '도시·인물·장비 이미지 전체 보기 →');
    link.href = 'artwork.html';
    container.append(link);
    container.dataset.artReady = 'true';
  }
  function ensureViewer() {
    if (dialog) return;
    dialog = make('dialog', 'art-dialog');
    dialog.setAttribute('aria-label', '이미지 크게 보기');
    dialog.innerHTML = '<div class="art-view-toolbar"><span class="art-position"></span><button type="button" data-close aria-label="이미지 닫기">닫기 ×</button></div><div class="art-view-stage"><button type="button" data-prev aria-label="이전 이미지">‹</button><img alt=""><button type="button" data-next aria-label="다음 이미지">›</button></div><div class="art-view-caption"><strong></strong><p></p><nav><a data-read>본문 보기</a><a data-file target="_blank" rel="noopener">WebP 열기</a><a data-share>이미지 링크</a></nav></div>';
    document.body.append(dialog);
    dialog.querySelector('[data-close]').onclick = () => dialog.close();
    dialog.querySelector('[data-prev]').onclick = () => show(position-1);
    dialog.querySelector('[data-next]').onclick = () => show(position+1);
    dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
    dialog.addEventListener('keydown', event => {
      if (event.key === 'ArrowLeft') { event.preventDefault(); show(position-1); }
      if (event.key === 'ArrowRight') { event.preventDefault(); show(position+1); }
    });
    dialog.addEventListener('close', () => document.documentElement.classList.remove('art-view-open'));
  }
  function show(index) {
    position = (index+active.length)%active.length;
    const asset = active[position];
    const img = dialog.querySelector('img');
    img.src = asset.src; img.alt = asset.title;
    img.width = asset.width; img.height = asset.height;
    dialog.querySelector('.art-position').textContent = (position+1)+' / '+active.length;
    dialog.querySelector('.art-view-caption strong').textContent = asset.title;
    dialog.querySelector('.art-view-caption p').textContent = asset.description;
    const read = dialog.querySelector('[data-read]');
    read.hidden = !asset.placements.length; read.href = readerURL(asset);
    dialog.querySelector('[data-file]').href = asset.src;
    dialog.querySelector('[data-share]').href = 'artwork.html#'+asset.id;
    for (const button of dialog.querySelectorAll('[data-prev], [data-next]')) button.disabled = active.length < 2;
  }
  function open(asset, list) {
    ensureViewer(); active = list && list.length ? list : [asset];
    show(Math.max(0,active.findIndex(a => a.id === asset.id)));
    if (!dialog.open) dialog.showModal();
    document.documentElement.classList.add('art-view-open');
  }
  document.addEventListener('click', event => {
    const link = event.target.closest('a.art-image-link');
    if (!link || !catalogue || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const asset = catalogue.assets.find(a => a.id === link.dataset.artId);
    if (!asset) return;
    event.preventDefault();
    open(asset, link.closest('.art-collection')?._artAssets);
  });
  async function gallery() {
    const grid = document.getElementById('artGrid');
    if (!grid) return;
    const data = await load();
    const search = document.getElementById('artSearch');
    const group = document.getElementById('artGroup');
    const category = document.getElementById('artCategory');
    const count = document.getElementById('artCount');
    const more = document.getElementById('artLoadMore');
    const summary = document.getElementById('artSummary');
    summary.textContent = '세계와 생활, 도시의 풍경, 그리고 그곳에 사는 사람들. '+data.summary.images+'장의 그림을 만나보세요.';
    for (const name of Object.keys(data.summary.groups)) group.add(new Option(name, name));
    for (const name of [...new Set(data.assets.map(a => a.category))].sort((a,b) => a.localeCompare(b,'ko'))) category.add(new Option(name,name));
    const params = new URLSearchParams(location.search);
    search.value = params.get('q') || ''; group.value = params.get('group') || ''; category.value = params.get('category') || '';
    const sections = [
      {id:'landscapes', title:'풍경', note:'도시와 차원계, 시설과 생활의 장면'},
      {id:'people', title:'인물', note:'등장인물과 러너, 여러 몸과 존재'},
      {id:'objects', title:'사물', note:'장비와 물건, 기술·규칙 도해'},
      {id:'emblems', title:'문장·로고', note:'문장과 표식, 세계의 상징'}
    ];
    const personCategories = new Set(['인물 프로필','로어 인물의 초상과 대표 장면','러너','신수와 다른 존재','생활과 관계의 장면','전투와 이동 장면']);
    const objectCategories = new Set(['장비와 물건의 도감','장비와 물건','타롯 규칙','튜터리얼']);
    const overrides = {'base-a01':'people','base-a02':'people','base-a05':'objects','base-e05':'objects','base-e10':'people','base-e11':'people','base-e13':'objects','base-e14':'objects','base-e19':'objects','expanded-x036':'objects','expanded-x037':'objects','expanded-x055':'objects','expanded-x056':'people','expanded-x057':'objects','expanded-x058':'objects'};
    function sectionOf(asset) {
      if (overrides[asset.id]) return overrides[asset.id];
      if (asset.category === '문장과 표식') return 'emblems';
      if (personCategories.has(asset.category)) return 'people';
      if (objectCategories.has(asset.category)) return 'objects';
      return 'landscapes';
    }
    let filtered = [];
    grid.classList.remove('art-grid');
    const navigation = make('nav','art-section-nav');
    navigation.setAttribute('aria-label','전체 이미지 섹션');
    grid.before(navigation);
    function append() {
      navigation.replaceChildren();
      for (const section of sections) {
        const items = filtered.filter(a => sectionOf(a) === section.id);
        if (!items.length) continue;
        const jump = make('a','',section.title+' '+items.length);
        jump.href = '#catalogue-'+section.id; navigation.append(jump);
        const block = make('section','art-catalogue-section art-collection');
        block.id = 'catalogue-'+section.id; block._artAssets = items;
        block.append(make('h2','',section.title+' · '+items.length+'장'),make('p','art-section-note',section.note));
        const cards = make('div','art-grid'); block.append(cards);
        const button = make('button','art-section-more');button.type = 'button';
        let shown = 0;
        function addPage() {
          const batch = items.slice(shown,shown+24);
          batch.forEach(asset => cards.append(card(asset)));shown += batch.length;
          button.hidden = shown >= items.length;
          button.textContent = 'MORE INFO ... ('+shown+'/'+items.length+')';
          button.setAttribute('aria-label', section.title+' 더 보기, '+items.length+'장 중 '+shown+'장 표시');
        }
        button.addEventListener('click',addPage);block.append(button);grid.append(block);addPage();
      }
      more.hidden = true;
    }
    function filter() {
      const words = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
      filtered = data.assets.filter(a => (!group.value || a.group === group.value) && (!category.value || a.category === category.value) && words.every(word => [a.title,a.description,a.character,a.outfit,a.category,a.source_id].join(' ').toLocaleLowerCase().includes(word)));
      grid.replaceChildren(); grid._artAssets = filtered;
      count.textContent = filtered.length+'장 / 전체 '+data.summary.images+'장';
      document.getElementById('artEmpty').hidden = Boolean(filtered.length);
      append();
      const query = new URLSearchParams();
      if (search.value.trim()) query.set('q', search.value.trim());
      if (group.value) query.set('group',group.value);
      if (category.value) query.set('category',category.value);
      history.replaceState(null,'',location.pathname+(query.size ? '?'+query : '')+location.hash);
    }
    search.addEventListener('input', filter); group.addEventListener('change', filter); category.addEventListener('change', filter);

    document.getElementById('artReset').addEventListener('click', () => { search.value = ''; group.value = ''; category.value = ''; filter(); search.focus(); });
    function openHash() {
      const asset = data.assets.find(a => '#'+a.id === location.hash);
      if (asset) open(asset, filtered.includes(asset) ? filtered : data.assets);
    }
    window.addEventListener('hashchange',openHash);
    filter(); openHash(); document.body.dataset.artReady = 'true';
  }
  window.FEWKArt = {load, render};
  gallery().catch(() => {
    const count = document.getElementById('artCount');
    if (count) count.textContent = '이미지 목록을 불러오지 못했습니다. 새로고침해 주세요.';
  });
})();

(() => {
  'use strict';
  const root = document.documentElement;
  const languageButtons = [...document.querySelectorAll('[data-language]')];
  const home = document.body.dataset.page === 'home';
  const descriptions = {
    home: {
      ru: ['Markdown-It — веб-страницы в Markdown', 'Markdown-It — Chrome-расширение для локального преобразования веб-страниц в Markdown. Выберите содержимое, скопируйте результат или сохраните .md.'],
      en: ['Markdown-It — web pages to Markdown', 'Markdown-It is a Chrome extension for converting web content to Markdown locally. Choose content, copy the result, or save a .md file.']
    },
    policy: {
      ru: ['Политика конфиденциальности — Markdown-It', 'Политика конфиденциальности Markdown-It: локальная обработка, хранение данных и загрузка изображений по действию пользователя.'],
      en: ['Privacy policy — Markdown-It', 'Markdown-It privacy policy: local processing, data retention, and user-controlled image loading.']
    }
  };

  function setLanguage(language, updateUrl = false) {
    const lang = language === 'en' ? 'en' : 'ru';
    root.lang = lang;
    document.querySelectorAll('[data-ru][data-en]').forEach(element => {
      element.textContent = element.dataset[lang];
    });
    document.querySelectorAll('[data-aria-ru]').forEach(element => {
      element.setAttribute('aria-label', element.getAttribute(`data-aria-${lang}`));
    });
    document.querySelectorAll('[data-alt-ru]').forEach(element => {
      element.alt = element.getAttribute(`data-alt-${lang}`);
    });
    document.querySelectorAll('[data-shot]').forEach(element => {
      element.src = `/md-it/assets/screenshots/${lang}/${element.dataset.shot}.png`;
    });
    document.querySelectorAll('[data-shot-link]').forEach(element => {
      element.href = `/md-it/assets/screenshots/${lang}/${element.dataset.shotLink}.png`;
    });
    document.querySelectorAll('[data-policy-language]').forEach(element => {
      element.hidden = element.dataset.policyLanguage !== lang;
    });
    document.querySelectorAll('[data-policy-target]').forEach(element => {
      element.setAttribute('href', `#${lang}-${element.dataset.policyTarget}`);
    });
    document.querySelectorAll('[data-local-link]').forEach(element => {
      const url = new URL(element.href);
      url.searchParams.set('lang', lang);
      element.href = url.href;
    });
    languageButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.language === lang)));
    const [title, description] = descriptions[home ? 'home' : 'policy'][lang];
    document.title = title;
    document.querySelector('meta[name="description"]').content = description;
    document.querySelector('meta[property="og:title"]').content = title;
    document.querySelector('meta[property="og:description"]').content = description;
    document.querySelector('meta[property="og:locale"]').content = lang === 'ru' ? 'ru_RU' : 'en_US';
    document.querySelector('meta[property="og:locale:alternate"]').content = lang === 'ru' ? 'en_US' : 'ru_RU';
    try { localStorage.setItem('markdown-it-language', lang); } catch { /* The site also works with storage blocked. */ }
    if (updateUrl) {
      const url = new URL(location.href);
      url.searchParams.set('lang', lang);
      if (/^#(?:en|ru)-/.test(url.hash)) url.hash = url.hash.replace(/^#(?:en|ru)-/, `#${lang}-`);
      history.replaceState(null, '', url);
    }
  }

  let preferred;
  try { preferred = localStorage.getItem('markdown-it-language'); } catch { /* Optional preference only. */ }
  const queryLanguage = new URLSearchParams(location.search).get('lang');
  const hashLanguage = /^#(en|ru)(?:-|$)/.exec(location.hash)?.[1];
  const initialLanguage = ['ru', 'en'].includes(queryLanguage) ? queryLanguage : hashLanguage || preferred || (navigator.language.startsWith('ru') ? 'ru' : 'en');
  setLanguage(initialLanguage);
  document.querySelectorAll('.language-switch').forEach(element => { element.hidden = false; });
  languageButtons.forEach(button => button.addEventListener('click', () => setLanguage(button.dataset.language, true)));

  const tabs = [...document.querySelectorAll('[data-demo]')];
  if (tabs.length) {
    const tablist = document.querySelector('.demo-tabs');
    tablist.hidden = false;
    tablist.setAttribute('role', 'tablist');
    const panels = [...document.querySelectorAll('.demo-panel')];
    function selectTab(index, focus = false) {
      tabs.forEach((tab, current) => {
        tab.setAttribute('aria-selected', String(current === index));
        tab.tabIndex = current === index ? 0 : -1;
      });
      panels.forEach((panel, current) => { panel.hidden = current !== index; });
      if (focus) tabs[index].focus();
    }
    tabs.forEach((tab, index) => {
      tab.setAttribute('role', 'tab');
      panels[index].setAttribute('role', 'tabpanel');
      panels[index].tabIndex = 0;
      tab.addEventListener('click', () => selectTab(index));
      tab.addEventListener('keydown', event => {
        let next;
        if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
        if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
        if (event.key === 'Home') next = 0;
        if (event.key === 'End') next = tabs.length - 1;
        if (next !== undefined) { event.preventDefault(); selectTab(next, true); }
      });
    });
    selectTab(0);
  }
})();

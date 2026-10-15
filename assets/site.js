(() => {
  'use strict';
  const root = document.documentElement;
  const languageButtons = [...document.querySelectorAll('[data-language]')];
  const home = document.body.dataset.page === 'home';
  const storeUrl = 'https://chromewebstore.google.com/detail/pbajjhnmfaopgjblomoecaaokihjajli';
  let storePublished = false;
  let storeVersion = null;

  function validVersion(value) {
    return typeof value === 'string'
      && /^(?:0|[1-9][0-9]{0,4})(?:\.(?:0|[1-9][0-9]{0,4})){0,3}$/.test(value)
      && value.split('.').every(part => Number(part) <= 65535)
      && value.split('.').some(part => Number(part) > 0);
  }
  // Advisory only: browser strings can be reduced or spoofed. Never block the store link.
  function detectBrowser() {
    const agent = navigator.userAgent || '';
    const brands = navigator.userAgentData?.brands || [];
    const mobile = navigator.userAgentData?.mobile || /Android|iPhone|iPad|iPod|Mobile/i.test(agent)
      || (/Macintosh/i.test(agent) && navigator.maxTouchPoints > 1);
    if (mobile) return 'mobile';
    if (/Firefox\//i.test(agent)) return 'firefox';
    if (/Edg\/|OPR\/|Vivaldi\/|YaBrowser\/|Brave\/|Chromium\//i.test(agent)
      || brands.some(({ brand }) => /Microsoft Edge|Opera|Brave|Vivaldi|Yandex/i.test(brand))) return 'chromium';
    if (brands.some(({ brand }) => brand === 'Google Chrome')) return 'chrome';
    if (brands.some(({ brand }) => brand === 'Chromium')) return 'chromium';
    if (/Chrome\//i.test(agent)) return 'chrome';
    return 'other';
  }
  const browser = detectBrowser();
  root.dataset.browser = browser;
  const browserNotes = {
    chrome: {
      ru: 'Для Chrome на компьютере.',
      en: 'For desktop Chrome.'
    },
    firefox: {
      ru: 'Версия для Firefox пока в разработке. Для установки расширения нужен Chrome на компьютере.',
      en: 'The Firefox version is still in development. Desktop Chrome is required to install the extension.'
    },
    mobile: {
      ru: 'Для установки откройте эту страницу в Chrome на компьютере. Версия для Firefox пока в разработке.',
      en: 'To install, open this page in desktop Chrome. The Firefox version is still in development.'
    },
    chromium: {
      ru: 'Расширение предназначено для Chrome на компьютере. Совместимость с другими браузерами Chromium не гарантируется. Версия для Firefox пока в разработке.',
      en: 'The extension is intended for desktop Chrome. Compatibility with other Chromium browsers is not guaranteed. The Firefox version is still in development.'
    },
    other: {
      ru: 'Для установки нужен Chrome на компьютере. Версия для Firefox пока в разработке.',
      en: 'Installation requires desktop Chrome. The Firefox version is still in development.'
    }
  };

  function updateStoreUI(lang) {
    root.dataset.storeAvailability = storePublished ? 'published' : 'pending';
    document.querySelectorAll('[data-store-version]').forEach(element => {
      element.hidden = !storePublished || !storeVersion;
      element.textContent = storePublished && storeVersion ? `v${storeVersion}` : '';
      if (!element.hidden) element.setAttribute('aria-label', `${lang === 'ru' ? 'Версия' : 'Version'} ${storeVersion}`);
    });
    document.querySelectorAll('[data-store-link]').forEach(element => { element.hidden = !storePublished; });
    document.querySelectorAll('[data-store-pending]').forEach(element => { element.hidden = storePublished; });
    document.querySelectorAll('[data-install-label]').forEach(element => {
      element.textContent = browser === 'chrome'
        ? (lang === 'ru' ? 'Установить в Chrome' : 'Add to Chrome')
        : (lang === 'ru' ? 'Открыть Chrome Web Store' : 'Open Chrome Web Store');
    });
    document.querySelectorAll('[data-store-status]').forEach(element => {
      element.textContent = storePublished
        ? (lang === 'ru' ? 'Расширение доступно в Chrome Web Store.' : 'The extension is available in the Chrome Web Store.')
        : (lang === 'ru' ? 'Ожидает публикации в Chrome Web Store.' : 'Awaiting publication in the Chrome Web Store.');
    });
  }

  async function refreshStoreStatus() {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    try {
      const response = await fetch('/md-it/assets/store-status.json', {
        cache: 'no-store', credentials: 'omit', signal: controller.signal
      });
      if (!response.ok) return;
      const status = await response.json();
      if (status.url !== storeUrl || !['pending', 'published'].includes(status.status)) return;
      storePublished = status.status === 'published';
      storeVersion = storePublished && validVersion(status.version) ? status.version : null;
      updateStoreUI(root.lang);
    } catch { /* A missing snapshot or network failure keeps the last known UI state. */ }
    finally { clearTimeout(timeout); }
  }
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
    document.querySelectorAll('[data-browser-note]').forEach(element => {
      element.textContent = browserNotes[browser][lang];
    });
    updateStoreUI(lang);
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
  refreshStoreStatus();
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refreshStoreStatus(); });
  setInterval(() => { if (!document.hidden) refreshStoreStatus(); }, 5 * 60 * 1000);

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

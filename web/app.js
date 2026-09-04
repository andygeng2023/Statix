const app = document.querySelector('#app');
const tabs = [...document.querySelectorAll('[data-page]')];
let deferredInstall;

window.addEventListener('beforeinstallprompt', event => {
  event.preventDefault(); deferredInstall = event; document.querySelector('#install').hidden = false;
});
document.querySelector('#install').onclick = async () => { if (deferredInstall) { deferredInstall.prompt(); deferredInstall = null; } };
if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js');

const money = value => value == null ? '--' : `$${Number(value).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
const percent = value => value == null ? '--' : `${Number(value) > 0 ? '+' : ''}${Number(value).toFixed(2)}%`;
function chart(values) {
  if (!values || values.length < 2) return '<div class="chart-empty">Chart unavailable</div>';
  const min = Math.min(...values), span = Math.max(...values) - min || 1;
  const points = values.map((value, index) => `${(index * 100 / (values.length - 1)).toFixed(2)},${(100 - (value - min) * 88 / span).toFixed(2)}`).join(' ');
  return `<svg class="chart" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="Price preview"><polyline points="${points}" /></svg>`;
}
function card(item) {
  return `<button class="card" data-ticker="${item.ticker}"><div class="card-head"><div><strong>${item.ticker}</strong><small>${item.name || item.ticker}</small></div><span class="arrow">↗</span></div><div class="numbers"><b>${money(item.price)}</b><span>${percent(item.change_pct)}</span></div>${chart(item.close)}${item.signal ? `<div class="signal"><b>${item.signal}</b> · ${percent((item.expected_return || 0) * 100)} expected</div>` : ''}</button>`;
}
function row(items) { return `<div class="card-row">${items.length ? items.map(card).join('') : '<p class="muted">No data available yet.</p>'}</div>`; }
async function get(path) { const response = await fetch(path, {cache: 'no-store'}); if (!response.ok) throw Error('Data unavailable'); return response.json(); }
function section(title, body) { return `<section><div class="section-title"><h2>${title}</h2></div>${body}</section>`; }
async function renderHome() { const data = await get('/api/overview'); app.innerHTML = `<div class="intro"><p class="eyebrow">LIVE DASHBOARD</p><h2>See the market clearly.</h2><p class="muted">Fast, focused signals for the symbols you follow.</p></div>${section('Market pulse', row(data.pulse))}${section('Top stocks', row(data.top))}`; bindCards(); }
async function renderDiscover() { const data = await get('/api/discover'); app.innerHTML = `<div class="page-heading"><p class="eyebrow">MODEL SCANNER</p><h2>Discover</h2><p class="muted">${data.status === 'running' ? 'Scan running in the background.' : 'Ranked market opportunities.'}</p><button id="scan" class="primary">Run scan</button></div>${section('Latest signals', row(data.items))}`; document.querySelector('#scan').onclick = async () => { const response = await fetch('/api/scan', {method: 'POST'}); if (!response.ok) alert('Scan could not be queued.'); renderDiscover(); }; bindCards(); }
async function renderStocks(ticker = '') { app.innerHTML = `<div class="page-heading"><p class="eyebrow">STOCK LOOKUP</p><h2>Stocks</h2><form id="search"><input id="symbol" placeholder="Enter ticker" value="${ticker}"><button class="primary">Open</button></form></div><div id="stock-detail"></div>`; document.querySelector('#search').onsubmit = event => { event.preventDefault(); const symbol = document.querySelector('#symbol').value.toUpperCase(); history.pushState({}, '', `#stocks/${symbol}`); renderStocks(symbol); }; if (ticker) { const item = await get(`/api/stock/${ticker}`); const prediction = item.prediction ? `<div class="prediction"><b>${item.prediction.direction}</b><span>Confidence ${percent(item.prediction.confidence * 100)}</span><span>Reliability ${percent(item.prediction.reliability * 100)}</span><span>Expected ${percent(item.prediction.expected_return * 100)}</span></div>` : '<p class="muted">Prediction unavailable for this symbol.</p>'; document.querySelector('#stock-detail').innerHTML = section(item.ticker, `<div class="detail">${card(item)}</div>${prediction}`); bindCards(); } }
function bindCards() { document.querySelectorAll('[data-ticker]').forEach(element => element.onclick = () => { history.pushState({}, '', `#stocks/${element.dataset.ticker}`); setPage('stocks', element.dataset.ticker); }); }
async function setPage(page, ticker = '') { tabs.forEach(tab => tab.classList.toggle('active', tab.dataset.page === page)); if (page === 'home') await renderHome(); if (page === 'discover') await renderDiscover(); if (page === 'stocks') await renderStocks(ticker); }
tabs.forEach(tab => tab.onclick = () => { history.pushState({}, '', `#${tab.dataset.page}`); setPage(tab.dataset.page); });
window.onpopstate = () => setPageFromHash();
function setPageFromHash() { const [page = 'home', ticker = ''] = location.hash.slice(1).split('/'); setPage(['home', 'stocks', 'discover'].includes(page) ? page : 'home', ticker); }
setPageFromHash();
setInterval(() => { if (location.hash === '#home' || !location.hash) renderHome(); if (location.hash === '#discover') renderDiscover(); }, 60000);

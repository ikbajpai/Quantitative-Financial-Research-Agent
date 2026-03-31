/* ═══════════════════════════════════════════════════════════════
   Quantitative Financial Research Agent — Frontend App
   Pure Vanilla JS + Plotly.js
═══════════════════════════════════════════════════════════════ */

const API = '/api';

/* ════════════════════════════════
   AUTH
════════════════════════════════ */
async function initAuth() {
  try {
    const res  = await fetch('/auth/status');
    const data = await res.json();

    if (!data.configured) {
      // Google OAuth not set up — run in dev mode, hide overlay
      document.getElementById('loginOverlay').style.display = 'none';
      return;
    }

    if (!data.authenticated) {
      document.getElementById('loginOverlay').style.display = 'flex';
      return;
    }

    // Authenticated — hide overlay, show user profile
    document.getElementById('loginOverlay').style.display = 'none';
    renderUserProfile(data.user);
  } catch {
    // API unreachable — still allow app to load
    document.getElementById('loginOverlay').style.display = 'none';
  }
}

function renderUserProfile(user) {
  if (!user) return;
  const profileEl = document.getElementById('userProfile');
  const avatarEl  = document.getElementById('userAvatar');
  const nameEl    = document.getElementById('userName');
  const emailEl   = document.getElementById('userEmail');

  if (user.picture) {
    avatarEl.src = user.picture;
    avatarEl.style.display = 'block';
  } else {
    // Fallback initials avatar
    avatarEl.style.display = 'none';
    const placeholder = document.createElement('div');
    placeholder.className = 'user-avatar-placeholder';
    placeholder.textContent = (user.name || user.email || '?')[0].toUpperCase();
    avatarEl.parentNode.insertBefore(placeholder, avatarEl);
  }

  nameEl.textContent  = user.name  || '';
  emailEl.textContent = user.email || '';
  profileEl.style.display = 'flex';
}

initAuth();

const PLOTLY_LAYOUT_BASE = {
  paper_bgcolor: 'transparent',
  plot_bgcolor:  'transparent',
  font:  { family: 'Inter, system-ui, sans-serif', color: '#94a3b8', size: 11 },
  xaxis: { gridcolor: 'rgba(255,255,255,.05)', linecolor: 'rgba(255,255,255,.08)', tickfont: { size: 10 } },
  yaxis: { gridcolor: 'rgba(255,255,255,.05)', linecolor: 'rgba(255,255,255,.08)', tickfont: { size: 10 } },
  legend:  { bgcolor: 'rgba(0,0,0,0)', font: { size: 11 }, orientation: 'h', y: 1.08, x: 0 },
  margin:  { t: 16, r: 10, b: 36, l: 46 },
  hovermode: 'x unified',
  hoverlabel: { bgcolor: '#0c1525', font: { size: 11 } },
};

const PLOTLY_CONFIG = { displayModeBar: false, responsive: true };

const COLORS = ['#3b82f6','#10b981','#f59e0b','#8b5cf6','#ef4444','#06b6d4','#f97316'];

const TIER_CLASS = {
  Conservative: 'conservative',
  Moderate:     'moderate',
  Aggressive:   'aggressive',
  Speculative:  'speculative',
};

const TIER_DOT = {
  Conservative: '🟢',
  Moderate:     '🟡',
  Aggressive:   '🟠',
  Speculative:  '🔴',
};

/* ════════════════════════════════
   NAVIGATION
════════════════════════════════ */
document.querySelectorAll('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`page-${btn.dataset.page}`).classList.add('active');
  });
});

/* ════════════════════════════════
   API HEALTH CHECK
════════════════════════════════ */
async function checkHealth() {
  const dot  = document.getElementById('statusDot');
  const text = document.getElementById('statusText');
  try {
    const r = await fetch(`${API}/health`);
    if (r.ok) {
      const d = await r.json();
      dot.className  = 'status-dot online';
      text.textContent = d.llm_model || 'Online';
    } else { throw new Error(); }
  } catch {
    dot.className  = 'status-dot error';
    text.textContent = 'API offline';
  }
}
checkHealth();
setInterval(checkHealth, 30_000);

/* ════════════════════════════════
   EXAMPLE CHIPS
════════════════════════════════ */
document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    document.getElementById('queryInput').value = chip.dataset.query;
    document.getElementById('queryInput').focus();
  });
});

/* ════════════════════════════════
   RESEARCH AGENT
════════════════════════════════ */
const queryInput  = document.getElementById('queryInput');
const sendBtn     = document.getElementById('sendBtn');
const thinkingBox = document.getElementById('thinkingBox');
const thinkingLbl = document.getElementById('thinkingLabel');
const toolSteps   = document.getElementById('toolSteps');
const resultsArea = document.getElementById('resultsArea');

function getModel()  { return document.getElementById('modelSelect').value; }
function getPeriod() { return document.getElementById('periodSelect').value; }

sendBtn.addEventListener('click', runAnalysis);
queryInput.addEventListener('keydown', e => { if (e.key === 'Enter') runAnalysis(); });

async function runAnalysis() {
  const query = queryInput.value.trim();
  if (!query) return;

  sendBtn.disabled = true;
  resultsArea.innerHTML = '';
  showThinking('Sending to agent…');

  const fakeSteps = [
    'Parsing query…',
    'Selecting tools…',
    'Fetching market data…',
    'Computing risk metrics…',
    'Assembling report…',
  ];
  let stepIdx = 0;
  const stepInterval = setInterval(() => {
    if (stepIdx < fakeSteps.length) {
      addToolStep(fakeSteps[stepIdx], stepIdx < fakeSteps.length - 1);
      stepIdx++;
    }
  }, 700);

  try {
    const res  = await fetch(`${API}/analyze`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ query, model: getModel() }),
    });
    const data = await res.json();

    clearInterval(stepInterval);
    hideThinking();

    if (data.error) {
      renderError(data.error);
    } else {
      await renderReport(data);
    }
  } catch (err) {
    clearInterval(stepInterval);
    hideThinking();
    renderError('Failed to reach the API. Is the server running at ' + API + '?');
  } finally {
    sendBtn.disabled = false;
  }
}

function showThinking(label) {
  thinkingLbl.textContent = label;
  toolSteps.innerHTML = '';
  thinkingBox.style.display = 'block';
}

function hideThinking() { thinkingBox.style.display = 'none'; }

let stepCount = 0;
function addToolStep(text, done = false) {
  const el = document.createElement('div');
  el.className = `tool-step${done ? ' done' : ''}`;
  el.innerHTML = `<div class="step-dot"></div><span>${text}</span>`;
  toolSteps.appendChild(el);
  stepCount++;
  thinkingLbl.textContent = text;
}

function renderError(msg) {
  resultsArea.innerHTML = `<div class="error-box">⚠ ${escHtml(msg)}</div>`;
}

async function renderReport(data) {
  // SEC filing RAG response
  if (data.answer && data.source && data.ticker) {
    renderSecReport(data);
    return;
  }

  // Natural language fallback — agent responded without using tools
  if (data.response && !data.metrics && !data.portfolio_metrics && !data.overall_sentiment) {
    resultsArea.innerHTML = `
      <div class="recommendation-banner" style="white-space:pre-wrap;line-height:1.9;font-size:.9rem">
        <div style="font-size:.72rem;color:var(--txt3);margin-bottom:.6rem;font-weight:600;letter-spacing:.06em">AGENT RESPONSE</div>
        ${escHtml(data.response)}
      </div>
      <div class="error-box" style="background:rgba(245,158,11,.07);border-color:rgba(245,158,11,.25);color:var(--yellow)">
        ⚠ The model responded without calling tools. Try rephrasing as: <em>"Calculate the risk metrics for AAPL vs MSFT over 5 years"</em>
      </div>`;
    return;
  }

  const type    = data.report_type || 'comparison';
  const tickers = data.tickers || [];
  const period  = data.period  || getPeriod();

  let html = '';

  /* Recommendation banner */
  if (data.recommendation) {
    html += `<div class="recommendation-banner"><strong>Recommendation:</strong> ${escHtml(data.recommendation)}</div>`;
  }

  /* Sentiment card */
  if (data.overall_sentiment) {
    html += buildSentimentCard(data);
  }

  /* Metric cards */
  const metricsList = type === 'portfolio'
    ? (data.portfolio_metrics ? [data.portfolio_metrics] : [])
    : (data.metrics || []);

  if (metricsList.length) {
    html += `<div class="metrics-grid">`;
    metricsList.forEach(m => { html += buildMetricCard(m); });
    html += `</div>`;
  }

  /* For portfolio: individual holdings */
  if (type === 'portfolio' && data.individual_metrics?.length) {
    html += `<div class="metrics-grid">`;
    data.individual_metrics.forEach(m => { html += buildMetricCard(m); });
    html += `</div>`;
  }

  resultsArea.innerHTML = html;

  /* Charts — fetch price data only for comparison/portfolio */
  if (tickers.length >= 1 && (type === 'comparison' || type === 'portfolio')) {
    await renderPriceCharts(tickers, period);
  }

  /* Correlation heatmap */
  if (data.correlation_matrix && Object.keys(data.correlation_matrix).length) {
    renderCorrelationHeatmap(data.correlation_matrix);
  }

  /* Full metrics table */
  const tableMetrics = type === 'portfolio'
    ? data.individual_metrics || []
    : data.metrics || [];
  if (tableMetrics.length > 1) {
    renderMetricsTable(tableMetrics);
  }

  /* JSON toggle */
  const toggleId = 'jsonBlk_' + Date.now();
  const toggleEl = document.createElement('div');
  toggleEl.innerHTML = `
    <button class="json-toggle" onclick="toggleJson('${toggleId}')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
      View raw JSON
    </button>
    <div id="${toggleId}" class="json-block" style="display:none">${escHtml(JSON.stringify(data, null, 2))}</div>
  `;
  resultsArea.appendChild(toggleEl);
}

/* ─── SEC Filing report ─── */
function renderSecReport(data) {
  const sentColor = data.sentiment === 'Positive' ? '#10b981' : data.sentiment === 'Negative' ? '#ef4444' : '#94a3b8';
  const conf = data.confidence != null ? ` · ${(data.confidence * 100).toFixed(0)}% confidence` : '';
  const keyPoints = (data.key_points || []).map(p => `<li>${escHtml(p)}</li>`).join('');
  const risks = (data.risks_mentioned || []).map(r => `<span class="theme-pill">${escHtml(r)}</span>`).join('');

  resultsArea.innerHTML = `
    <div class="sentiment-card" style="margin-bottom:1.2rem">
      <div class="card-title">SEC Filing Analysis · ${escHtml(data.ticker || '')} · <span style="font-size:.75rem;color:var(--txt3)">${escHtml(data.source || '')}</span></div>
      <div class="sentiment-badge" style="background:${sentColor}22;color:${sentColor};border-color:${sentColor}44">${escHtml(data.sentiment || 'Neutral')}${conf}</div>
      <p style="margin-top:.9rem;font-size:.88rem;color:var(--txt1);line-height:1.75">${escHtml(data.answer || '')}</p>
      ${keyPoints ? `<ul style="margin:.8rem 0 0 1.2rem;font-size:.83rem;color:var(--txt2);line-height:1.7">${keyPoints}</ul>` : ''}
      ${risks ? `<div class="sentiment-themes" style="margin-top:.8rem"><strong style="font-size:.72rem;color:var(--txt3);letter-spacing:.06em">RISKS MENTIONED</strong><br>${risks}</div>` : ''}
    </div>`;

  const toggleId = 'jsonBlk_' + Date.now();
  const toggleEl = document.createElement('div');
  toggleEl.innerHTML = `
    <button class="json-toggle" onclick="toggleJson('${toggleId}')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
      View raw JSON
    </button>
    <div id="${toggleId}" class="json-block" style="display:none">${escHtml(JSON.stringify(data, null, 2))}</div>
  `;
  resultsArea.appendChild(toggleEl);
}

function toggleJson(id) {
  const el = document.getElementById(id);
  el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

/* ─── Metric card ─── */
function buildMetricCard(m) {
  const tier   = m.risk_tier || '';
  const cls    = TIER_CLASS[tier] || '';
  const dot    = TIER_DOT[tier]  || '';
  const ret    = m.annualized_return  != null ? (m.annualized_return  * 100).toFixed(2) + '%' : '—';
  const vol    = m.annualized_volatility != null ? (m.annualized_volatility * 100).toFixed(2) + '%' : '—';
  const sharpe = m.sharpe_ratio != null ? m.sharpe_ratio.toFixed(3) : '—';
  const mdd    = m.max_drawdown  != null ? (m.max_drawdown  * 100).toFixed(2) + '%' : '—';
  const beta   = m.beta  != null ? m.beta.toFixed(3)  : '—';
  const alpha  = m.alpha != null ? (m.alpha * 100).toFixed(2) + '%' : '—';
  const retPos = m.annualized_return >= 0;
  const alphaPos = m.alpha >= 0;

  return `
    <div class="metric-card ${cls}">
      <div class="metric-ticker">${escHtml(m.ticker || '—')}</div>
      <div class="metric-sharpe">${sharpe}</div>
      <div class="metric-sharpe-label">Sharpe Ratio</div>
      <div class="metric-row"><span class="label">Return</span><span class="value ${retPos ? 'pos' : 'neg'}">${ret}</span></div>
      <div class="metric-row"><span class="label">Volatility</span><span class="value">${vol}</span></div>
      <div class="metric-row"><span class="label">Max DD</span><span class="value neg">${mdd}</span></div>
      <div class="metric-row"><span class="label">Beta</span><span class="value">${beta}</span></div>
      <div class="metric-row"><span class="label">Alpha</span><span class="value ${alphaPos ? 'pos' : 'neg'}">${alpha}</span></div>
      ${tier ? `<div class="tier-badge ${cls}">${dot} ${escHtml(tier)}</div>` : ''}
    </div>`;
}

/* ─── Sentiment card ─── */
function buildSentimentCard(data) {
  const s   = (data.overall_sentiment || '').toLowerCase();
  const cls = s === 'bullish' ? 'bullish' : s === 'bearish' ? 'bearish' : 'neutral';
  const emoji = s === 'bullish' ? '↑' : s === 'bearish' ? '↓' : '→';
  const conf = data.confidence != null ? ` · ${(data.confidence * 100).toFixed(0)}% confidence` : '';
  const themes = (data.key_themes || []).map(t => `<span class="theme-pill">${escHtml(t)}</span>`).join('');
  const note = data.analyst_note ? `<p style="margin-top:.7rem;font-size:.82rem;color:var(--txt2)">${escHtml(data.analyst_note)}</p>` : '';

  return `
    <div class="sentiment-card">
      <div class="card-title">News Sentiment · ${escHtml(data.ticker || '')}</div>
      <div class="sentiment-badge ${cls}">${emoji} ${escHtml(data.overall_sentiment || '')}${conf}</div>
      ${note}
      ${themes ? `<div class="sentiment-themes">${themes}</div>` : ''}
    </div>`;
}

/* ─── Price charts ─── */
async function renderPriceCharts(tickers, period) {
  const container = document.createElement('div');
  container.className = 'charts-grid';
  container.innerHTML = `
    <div class="chart-card"><div class="chart-label"><span class="dot"></span>Cumulative Returns</div><div id="chartCumRet" style="height:240px"></div></div>
    <div class="chart-card"><div class="chart-label"><span class="dot"></span>Drawdown</div><div id="chartDrawdown" style="height:240px"></div></div>`;
  resultsArea.appendChild(container);

  try {
    const r    = await fetch(`${API}/prices?tickers=${tickers.join(',')}&period=${period}`);
    const data = await r.json();

    /* Cumulative returns */
    const cumTraces = Object.entries(data).map(([ticker, d], i) => ({
      x: d.dates, y: d.cumulative_returns,
      type: 'scatter', mode: 'lines',
      name: ticker,
      line: { color: COLORS[i % COLORS.length], width: 2 },
      hovertemplate: `<b>${ticker}</b>: %{y:.2f}%<extra></extra>`,
    }));

    Plotly.newPlot('chartCumRet', cumTraces, {
      ...PLOTLY_LAYOUT_BASE,
      yaxis: { ...PLOTLY_LAYOUT_BASE.yaxis, ticksuffix: '%' },
    }, PLOTLY_CONFIG);

    /* Drawdown */
    const ddTraces = Object.entries(data).map(([ticker, d], i) => ({
      x: d.dates, y: d.drawdown,
      type: 'scatter', mode: 'lines',
      name: ticker, fill: 'tozeroy',
      line:       { color: COLORS[i % COLORS.length], width: 1.5 },
      fillcolor:  hexToRgba(COLORS[i % COLORS.length], .1),
      hovertemplate: `<b>${ticker}</b>: %{y:.2f}%<extra></extra>`,
    }));

    Plotly.newPlot('chartDrawdown', ddTraces, {
      ...PLOTLY_LAYOUT_BASE,
      yaxis: { ...PLOTLY_LAYOUT_BASE.yaxis, ticksuffix: '%' },
    }, PLOTLY_CONFIG);

  } catch { /* charts silently skip if prices unavailable */ }
}

/* ─── Correlation heatmap ─── */
function renderCorrelationHeatmap(matrix) {
  const container = document.createElement('div');
  container.className = 'chart-card';
  container.style.marginBottom = '1.5rem';
  container.innerHTML = `<div class="chart-label"><span class="dot"></span>Correlation Matrix</div><div id="chartCorr" style="height:260px"></div>`;
  resultsArea.appendChild(container);

  const tickers = Object.keys(matrix);
  const z    = tickers.map(r => tickers.map(c => matrix[r]?.[c] ?? 0));
  const text = z.map(row => row.map(v => v.toFixed(3)));

  Plotly.newPlot('chartCorr', [{
    type: 'heatmap',
    x: tickers, y: tickers, z, text,
    texttemplate: '%{text}',
    textfont: { size: 12 },
    colorscale: [
      [0,   '#ef4444'], [.5,  '#1e3a5f'],
      [1,   '#10b981'],
    ],
    zmid: 0, zmin: -1, zmax: 1,
    hovertemplate: '%{y} / %{x}: <b>%{z:.3f}</b><extra></extra>',
    showscale: true,
    colorbar: { tickfont: { size: 10 }, len: .9 },
  }], {
    ...PLOTLY_LAYOUT_BASE,
    margin: { t: 10, r: 60, b: 60, l: 60 },
    xaxis: { tickfont: { size: 11 } },
    yaxis: { tickfont: { size: 11 }, autorange: 'reversed' },
  }, PLOTLY_CONFIG);
}

/* ─── Metrics table ─── */
function renderMetricsTable(metrics) {
  const rows = metrics.map(m => {
    const ret   = m.annualized_return  != null ? fmtPct(m.annualized_return)  : '—';
    const vol   = m.annualized_volatility != null ? fmtPct(m.annualized_volatility) : '—';
    const retPos = m.annualized_return >= 0;
    const tier  = m.risk_tier || '';
    const dot   = TIER_DOT[tier] || '';
    const cls   = TIER_CLASS[tier] || '';
    return `
      <tr>
        <td>${escHtml(m.ticker || '—')}</td>
        <td class="${retPos ? 'pos' : 'neg'}">${ret}</td>
        <td>${vol}</td>
        <td>${m.sharpe_ratio != null ? m.sharpe_ratio.toFixed(3) : '—'}</td>
        <td>${m.sortino_ratio != null ? m.sortino_ratio.toFixed(3) : '—'}</td>
        <td class="neg">${m.max_drawdown != null ? fmtPct(m.max_drawdown) : '—'}</td>
        <td>${m.beta != null ? m.beta.toFixed(3) : '—'}</td>
        <td>${m.alpha != null ? fmtPct(m.alpha) : '—'}</td>
        <td>${m.var_95 != null ? fmtPct(m.var_95) : '—'}</td>
        <td><span class="tier-badge ${cls}" style="font-size:.68rem">${dot} ${escHtml(tier)}</span></td>
      </tr>`;
  }).join('');

  const el = document.createElement('div');
  el.className = 'table-card';
  el.innerHTML = `
    <div class="table-card-header">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
      Full Metrics Breakdown
    </div>
    <div style="overflow-x:auto">
      <table class="metrics-table">
        <thead>
          <tr>
            <th>Ticker</th><th>Return</th><th>Volatility</th><th>Sharpe</th>
            <th>Sortino</th><th>Max DD</th><th>Beta</th><th>Alpha</th>
            <th>VaR 95%</th><th>Tier</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  resultsArea.appendChild(el);
}

/* ════════════════════════════════
   PORTFOLIO OPTIMIZER
════════════════════════════════ */
const tickerTags  = document.getElementById('tickerTags');
const tickerInput = document.getElementById('tickerInput');
const tickerWrap  = document.getElementById('tickerInputWrap');
const optResults  = document.getElementById('optResults');
const optimizeBtn = document.getElementById('optimizeBtn');

let addedTickers = [];

tickerWrap.addEventListener('click', () => tickerInput.focus());

tickerInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' || e.key === ',') {
    e.preventDefault();
    addTicker(tickerInput.value);
  } else if (e.key === 'Backspace' && tickerInput.value === '' && addedTickers.length) {
    removeTicker(addedTickers[addedTickers.length - 1]);
  }
});

tickerInput.addEventListener('blur', () => {
  if (tickerInput.value.trim()) addTicker(tickerInput.value);
});

function addTicker(raw) {
  const t = raw.trim().toUpperCase().replace(',', '');
  if (!t || addedTickers.includes(t)) { tickerInput.value = ''; return; }
  addedTickers.push(t);
  renderTags();
  tickerInput.value = '';
}

function removeTicker(t) {
  addedTickers = addedTickers.filter(x => x !== t);
  renderTags();
}

function renderTags() {
  tickerTags.innerHTML = addedTickers.map(t =>
    `<div class="ticker-tag">${escHtml(t)}<button onclick="removeTicker('${t}')" type="button">×</button></div>`
  ).join('');
}

optimizeBtn.addEventListener('click', async () => {
  if (addedTickers.length < 2) {
    alert('Enter at least 2 tickers.'); return;
  }

  const weightsRaw = document.getElementById('weightsInput').value.trim();
  let currentWeights = null;
  if (weightsRaw) {
    currentWeights = weightsRaw.split(',').map(v => parseFloat(v.trim()));
    if (currentWeights.some(isNaN)) { alert('Invalid weights.'); return; }
    if (currentWeights.length !== addedTickers.length) {
      alert(`Expected ${addedTickers.length} weights, got ${currentWeights.length}.`); return;
    }
    const sum = currentWeights.reduce((a, b) => a + b, 0);
    if (Math.abs(sum - 1) > 0.01) { alert(`Weights must sum to 1.0 (got ${sum.toFixed(3)}).`); return; }
  }

  const period = document.getElementById('optPeriod').value;
  const rfr    = parseFloat(document.getElementById('optRfr').value) / 100;

  optimizeBtn.disabled = true;
  optimizeBtn.textContent = 'Optimizing…';
  optResults.innerHTML = `<div class="empty-state"><div class="skeleton" style="width:100%;height:400px"></div></div>`;

  try {
    const res  = await fetch(`${API}/optimize`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        tickers: addedTickers,
        current_weights: currentWeights,
        period, risk_free_rate: rfr,
      }),
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    renderOptimizerResults(data);
  } catch (err) {
    optResults.innerHTML = `<div class="error-box">⚠ ${escHtml(err.message)}</div>`;
  } finally {
    optimizeBtn.disabled = false;
    optimizeBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg> Run Optimization`;
  }
});

function renderOptimizerResults(data) {
  const maxS   = data.max_sharpe_portfolio     || {};
  const minV   = data.min_volatility_portfolio || {};
  const curr   = data.current_portfolio;
  const front  = data.efficient_frontier || [];
  const rebal  = data.rebalancing_advice;

  let html = '';

  /* Summary stats row */
  html += `<div class="opt-summary-row">`;
  html += buildOptSummaryCard('⭐ Max Sharpe', maxS, '#3b82f6');
  html += buildOptSummaryCard('🛡️ Min Volatility', minV, '#10b981');
  html += `</div>`;

  /* Weight bars */
  if (maxS.weights) {
    html += `<div class="card" style="margin-bottom:1rem">
      <div class="card-title">Max Sharpe — Optimal Weights</div>
      <div class="weight-bars">
        ${Object.entries(maxS.weights).map(([t, w]) =>
          `<div class="weight-row">
            <div class="weight-ticker">${escHtml(t)}</div>
            <div class="weight-bar-track"><div class="weight-bar-fill" style="width:${(w*100).toFixed(1)}%"></div></div>
            <div class="weight-pct">${(w*100).toFixed(1)}%</div>
          </div>`
        ).join('')}
      </div>
    </div>`;
  }

  /* Rebalancing advice */
  if (rebal) {
    html += `<div class="rebalance-card">${escHtml(rebal)}</div>`;
  }

  optResults.innerHTML = html;

  /* Efficient Frontier chart */
  if (front.length) {
    const chartDiv = document.createElement('div');
    chartDiv.className = 'chart-card';
    chartDiv.style.marginBottom = '1rem';
    chartDiv.innerHTML = `<div class="chart-label"><span class="dot"></span>Efficient Frontier</div><div id="chartFrontier" style="height:360px"></div>`;
    optResults.insertBefore(chartDiv, optResults.firstChild);

    const vols    = front.map(p => (p.annualized_volatility * 100).toFixed(3));
    const rets    = front.map(p => (p.annualized_return    * 100).toFixed(3));
    const sharpes = front.map(p => p.sharpe_ratio);

    const traces = [{
      x: vols, y: rets, type: 'scatter', mode: 'lines+markers',
      name: 'Frontier',
      line:   { color: '#3b82f6', width: 2 },
      marker: {
        size: 5, color: sharpes,
        colorscale: 'Viridis', showscale: true,
        colorbar: { title: 'Sharpe', titlefont: { size: 10 }, tickfont: { size: 10 }, len: .8 },
      },
      hovertemplate: 'Vol: %{x:.1f}%<br>Return: %{y:.1f}%<extra></extra>',
    }];

    if (maxS.annualized_volatility) {
      traces.push({
        x: [(maxS.annualized_volatility*100).toFixed(2)],
        y: [(maxS.annualized_return   *100).toFixed(2)],
        type: 'scatter', mode: 'markers', name: 'Max Sharpe',
        marker: { symbol: 'star', size: 16, color: '#fbbf24', line: { color: '#fff', width: 1 } },
        hovertemplate: `Max Sharpe<br>Sharpe: ${maxS.sharpe_ratio?.toFixed(3)}<extra></extra>`,
      });
    }
    if (minV.annualized_volatility) {
      traces.push({
        x: [(minV.annualized_volatility*100).toFixed(2)],
        y: [(minV.annualized_return   *100).toFixed(2)],
        type: 'scatter', mode: 'markers', name: 'Min Vol',
        marker: { symbol: 'diamond', size: 14, color: '#10b981', line: { color: '#fff', width: 1 } },
        hovertemplate: `Min Volatility<br>Sharpe: ${minV.sharpe_ratio?.toFixed(3)}<extra></extra>`,
      });
    }
    if (curr?.annualized_volatility) {
      traces.push({
        x: [(curr.annualized_volatility*100).toFixed(2)],
        y: [(curr.annualized_return   *100).toFixed(2)],
        type: 'scatter', mode: 'markers', name: 'Your Portfolio',
        marker: { symbol: 'circle', size: 12, color: '#ef4444', line: { color: '#fff', width: 1 } },
        hovertemplate: `Your Portfolio<br>Sharpe: ${curr.sharpe_ratio?.toFixed(3)}<extra></extra>`,
      });
    }

    Plotly.newPlot('chartFrontier', traces, {
      ...PLOTLY_LAYOUT_BASE,
      xaxis: { ...PLOTLY_LAYOUT_BASE.xaxis, title: { text: 'Annualized Volatility (%)', font: { size: 11 } } },
      yaxis: { ...PLOTLY_LAYOUT_BASE.yaxis, title: { text: 'Annualized Return (%)',    font: { size: 11 } } },
      margin: { t: 20, r: 70, b: 50, l: 55 },
    }, PLOTLY_CONFIG);
  }
}

function buildOptSummaryCard(title, data, accentColor) {
  const ret   = data.annualized_return     != null ? fmtPct(data.annualized_return)     : '—';
  const vol   = data.annualized_volatility != null ? fmtPct(data.annualized_volatility) : '—';
  const sharpe = data.sharpe_ratio != null ? data.sharpe_ratio.toFixed(3) : '—';

  return `
    <div class="opt-summary-card">
      <h4 style="color:${accentColor}">${title}</h4>
      <div class="opt-stat"><span class="k">Sharpe Ratio</span><span class="v" style="color:${accentColor}">${sharpe}</span></div>
      <div class="opt-stat"><span class="k">Ann. Return</span><span class="v">${ret}</span></div>
      <div class="opt-stat"><span class="k">Volatility</span><span class="v">${vol}</span></div>
    </div>`;
}

/* ════════════════════════════════
   UTILS
════════════════════════════════ */
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function fmtPct(v) {
  return (v * 100).toFixed(2) + '%';
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

/* NEURON-X Omega — Dashboard Logic */

const API = 'http://localhost:8000/api';
let currentPanel = 'dashboard';

// ── INIT ──
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
});

// ── SETUP ──
async function connectAPI() {
    const key = document.getElementById('apiKeyInput').value.trim();
    const model = document.getElementById('modelSelect').value;
    const btn = document.getElementById('connectBtn');
    const err = document.getElementById('setupError');

    if (!key) { err.textContent = 'Please enter an API key'; return; }

    btn.disabled = true;
    btn.innerHTML = '<svg width="16" height="16" class="spin"><use href="#icon-activity"/></svg> Connecting...';
    err.textContent = '';

    try {
        const res = await fetch(`${API}/connect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: key, model }),
        });
        const data = await res.json();

        if (data.status === 'connected') {
            hideSetup();
            setStatus(true, `Connected  |  ${data.model}`);
        } else {
            err.textContent = data.error || 'Connection failed';
        }
    } catch (e) {
        err.textContent = 'Cannot reach API server. Is it running?';
    }
    btn.disabled = false;
    btn.innerHTML = '<svg width="16" height="16"><use href="#icon-zap"/></svg> Connect';
}

function skipSetup() {
    hideSetup();
    setStatus(false, 'Offline mode');
}

function hideSetup() {
    document.getElementById('setupOverlay').classList.add('hidden');
    loadDashboard();
}

function showSetup() {
    document.getElementById('setupOverlay').classList.remove('hidden');
}

async function checkHealth() {
    try {
        const res = await fetch(`${API}/health`);
        const d = await res.json();
        if (d.connected) {
            hideSetup();
            setStatus(true, `Connected  |  ${d.model}`);
        } else if (d.total_engrams > 0) {
            hideSetup();
            setStatus(false, 'Offline mode');
        }
    } catch {
        setStatus(false, 'API offline');
    }
}

function setStatus(on, text) {
    const dot = document.getElementById('statusDot');
    dot.className = on ? 'status-dot on' : 'status-dot off';
    document.getElementById('statusText').textContent = text;
}

// ── PANELS ──
function switchPanel(p) {
    currentPanel = p;
    document.querySelectorAll('.panel').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
    document.getElementById('panel-' + p).classList.add('active');
    const btn = document.querySelector(`[data-panel="${p}"]`);
    if (btn) btn.classList.add('active');
    if (p === 'dashboard') loadDashboard();
    else if (p === 'memories') loadMemories();
    else if (p === 'bonds') loadBonds();
}

// ── DASHBOARD ──
async function loadDashboard() {
    try {
        const [sr, mr, br] = await Promise.all([
            fetch(`${API}/stats`), fetch(`${API}/memories?limit=100`), fetch(`${API}/bonds`)
        ]);
        const stats = await sr.json();
        const mems = await mr.json();
        const bonds = await br.json();

        el('s-total').textContent = stats.total_engrams || mems.length;
        el('s-bonds').textContent = stats.total_axons || bonds.length;
        el('s-interactions').textContent = stats.interaction_count || 0;
        const age = stats.brain_age_days || 0;
        el('s-age').textContent = age > 0 ? Math.round(age) + 'd' : 'new';

        // zones
        const zc = {};
        if (stats.zone_counts) Object.assign(zc, stats.zone_counts);
        else mems.forEach(m => { zc[m.zone] = (zc[m.zone] || 0) + 1; });
        const total = mems.length || 1;
        const zm = { H: 'hot', W: 'warm', C: 'cold', S: 'silent', A: 'anchor' };
        for (const [z, n] of Object.entries(zm)) {
            const c = zc[z] || 0;
            const bar = el('zf-' + n);
            if (bar) bar.style.width = (c / total * 100) + '%';
            const num = el('zn-' + n);
            if (num) num.textContent = c;
        }

        // top memories
        const tl = el('topList');
        if (mems.length) {
            const sorted = [...mems].sort((a, b) => b.heat - a.heat).slice(0, 6);
            tl.innerHTML = sorted.map(m =>
                `<div class="top-item" onclick="viewNrn('${m.id}')">
                    <span class="top-heat">${m.heat.toFixed(2)}</span>
                    <span class="top-text">${esc(m.text)}</span>
                </div>`
            ).join('');
        } else {
            tl.innerHTML = '<p class="muted">No memories yet</p>';
        }
    } catch (e) { console.error(e); }
}

// ── CHAT ──
async function sendMessage() {
    const input = el('chatInput');
    const msg = input.value.trim();
    if (!msg) return;

    const feed = el('chatFeed');
    const empty = el('chatEmpty');
    if (empty) empty.remove();

    addMsg(feed, msg, 'user');
    input.value = '';
    el('sendBtn').disabled = true;

    try {
        const res = await fetch(`${API}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg }),
        });
        const d = await res.json();

        if (d.actions) {
            for (const a of d.actions) {
                const sym = a.action === 'FORGE' ? 'FORGE' : a.action === 'ECHO' ? 'ECHO' : 'CLASH';
                const cls = a.action.toLowerCase();
                const s = a.surprise ? ` | surprise: ${a.surprise.toFixed(2)}` : '';
                addMsg(feed, `${sym}: "${a.text.substring(0, 70)}"${s}`, `act ${cls}`);
            }
        }

        if (d.response) {
            addMsg(feed, d.response, 'sys');
        } else if (!d.connected) {
            let txt = 'Memory stored. Running in offline mode.';
            if (d.memories && d.memories.length) {
                txt += '\n\nRelevant memories:\n' + d.memories.map((m, i) =>
                    `  ${i + 1}. [${m.zone}] ${m.text.substring(0, 55)} (${m.score.toFixed(2)})`
                ).join('\n');
            }
            addMsg(feed, txt, 'sys');
        }
        loadDashboard();
    } catch {
        addMsg(feed, 'Cannot reach API server.', 'sys');
    }
    el('sendBtn').disabled = false;
}

function sendExample(t) { el('chatInput').value = t; sendMessage(); }

function addMsg(container, text, cls) {
    const d = document.createElement('div');
    d.className = 'msg ' + cls;
    d.textContent = text;
    container.appendChild(d);
    container.scrollTop = container.scrollHeight;
}

// ── MEMORIES ──
async function loadMemories(zone) {
    const grid = el('memGrid');
    try {
        const url = zone ? `${API}/memories?zone=${zone}&limit=100` : `${API}/memories?limit=100`;
        const mems = await (await fetch(url)).json();
        if (!mems.length) { grid.innerHTML = '<p class="muted">No memories found</p>'; return; }
        grid.innerHTML = mems.map(m =>
            `<div class="mem-card" onclick="viewNrn('${m.id}')">
                <div class="mem-zone ${m.zone}">${zoneLabel(m.zone)}</div>
                <div class="mem-text">${esc(m.text)}</div>
                <div class="mem-meta">
                    <span>heat ${m.heat.toFixed(2)}</span>
                    <span>spark ${m.spark.toFixed(2)}</span>
                    <span>wt ${m.weight.toFixed(1)}</span>
                    <span>conf ${m.confidence.toFixed(2)}</span>
                    <span>${m.emotion}</span>
                    <span>${m.age_days.toFixed(0)}d</span>
                    <span>${m.bonds} bonds</span>
                    ${m.is_anchor ? '<span style="color:var(--violet)">ANCHOR</span>' : ''}
                </div>
            </div>`
        ).join('');
    } catch { grid.innerHTML = '<p class="muted">Could not load memories</p>'; }
}

function filterZone(z, btn) {
    document.querySelectorAll('.pill').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    loadMemories(z);
}

async function searchMemories() {
    const q = el('searchInput').value.trim();
    if (!q) { loadMemories(); return; }
    const grid = el('memGrid');
    try {
        const res = await fetch(`${API}/search`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: q, top_k: 20 }),
        });
        const results = await res.json();
        if (!results.length) { grid.innerHTML = '<p class="muted">No matches</p>'; return; }
        grid.innerHTML = results.map(m =>
            `<div class="mem-card" onclick="viewNrn('${m.id}')">
                <div class="mem-zone ${m.zone}">${zoneLabel(m.zone)}</div>
                <div class="mem-text">${esc(m.text)}</div>
                <div class="mem-meta">
                    <span>score ${m.score.toFixed(3)}</span>
                    <span>heat ${m.heat.toFixed(2)}</span>
                    <span>${m.emotion}</span>
                </div>
            </div>`
        ).join('');
    } catch { grid.innerHTML = '<p class="muted">Search failed</p>'; }
}

// ── BONDS ──
async function loadBonds() {
    const list = el('bondList');
    try {
        const bonds = await (await fetch(`${API}/bonds`)).json();
        if (!bonds.length) { list.innerHTML = '<p class="muted">No bonds yet</p>'; return; }
        list.innerHTML = bonds.map(b =>
            `<div class="bond-row">
                <div class="bond-node">
                    <div class="bond-id">${b.from_id}</div>
                    <div class="bond-txt">${esc(b.from_text || '')}</div>
                </div>
                <div class="bond-mid">
                    <span class="bond-type">${b.type}</span>
                    <div class="bond-bar"><div class="bond-bar-fill" style="width:${b.synapse*100}%"></div></div>
                    <span class="bond-val">${b.synapse.toFixed(2)}</span>
                </div>
                <div class="bond-node">
                    <div class="bond-id">${b.to_id}</div>
                    <div class="bond-txt">${esc(b.to_text || '')}</div>
                </div>
            </div>`
        ).join('');
    } catch { list.innerHTML = '<p class="muted">Could not load bonds</p>'; }
}

// ── NRNLANG ──
async function viewNrn(id) {
    switchPanel('nrnlang');
    try {
        const d = await (await fetch(`${API}/nrnlang/${id}`)).json();
        el('nrnOutput').textContent = d.nrnlang;
    } catch { el('nrnOutput').textContent = 'Error loading NRNLANG data'; }
}

async function exportBrain() {
    el('nrnOutput').textContent = 'Exporting brain...';
    try {
        const d = await (await fetch(`${API}/nrnlang-brain`)).json();
        el('nrnOutput').textContent = d.nrnlang;
    } catch { el('nrnOutput').textContent = 'Export failed — is the server running?'; }
}

// ── HELPERS ──
function el(id) { return document.getElementById(id); }
function esc(s) { if(!s)return'';const d=document.createElement('div');d.textContent=s;return d.innerHTML; }
function zoneLabel(z) { return { H:'HOT', W:'WARM', C:'COLD', S:'SILENT', A:'ANCHOR' }[z] || z; }

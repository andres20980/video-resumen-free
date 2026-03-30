/**
 * Video Resumen Free — Frontend
 * Loads results from data/index.json, renders cards, and shows summaries.
 */

const REPO_OWNER = 'andres20980';
const REPO_NAME = 'video-resumen-free';
const REPO_URL = `https://github.com/${REPO_OWNER}/${REPO_NAME}`;
const ISSUE_NEW_URL = `${REPO_URL}/issues/new?template=summarize.yml`;
const ACTIONS_URL = `${REPO_URL}/actions`;
const DATA_BASE = 'data';

// ─── Init ────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    // Set dynamic links
    document.getElementById('new-summary-btn').href = ISSUE_NEW_URL;
    document.getElementById('actions-link').href = ACTIONS_URL;
    document.getElementById('repo-link').href = REPO_URL;

    // Route
    window.addEventListener('hashchange', route);
    route();
});

function route() {
    const hash = location.hash || '#/';

    if (hash.startsWith('#/result/')) {
        const id = hash.replace('#/result/', '');
        showDetail(id);
    } else {
        showList();
    }
}

// ─── List View ───────────────────────────────────────────────────────────────

async function showList() {
    document.getElementById('hero').style.display = '';
    document.getElementById('results').style.display = '';
    document.getElementById('result-detail').style.display = 'none';

    const container = document.getElementById('results-list');
    container.innerHTML = '<div class="loading">Cargando resultados...</div>';

    try {
        const resp = await fetch(`${DATA_BASE}/index.json`);
        if (!resp.ok) throw new Error('No results yet');
        const results = await resp.json();

        if (!results.length) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>No hay resúmenes todavía</h3>
                    <p>Crea el primero usando el botón "Nuevo Resumen" ↑</p>
                </div>`;
            return;
        }

        container.innerHTML = results.map(r => `
            <a href="#/result/${r.id}" class="result-card">
                <h3>${escapeHtml(r.title)}</h3>
                <div class="meta">
                    <span>⏱️ ${r.duration_minutes} min</span>
                    <span>📝 ${r.transcript_chars.toLocaleString()} chars</span>
                    <span>🖼️ ${r.frames_analyzed} frames</span>
                    <span>💚 $${r.cost_usd.toFixed(2)}</span>
                    <span>📅 ${formatDate(r.timestamp)}</span>
                </div>
            </a>
        `).join('');
    } catch (e) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>No hay resúmenes todavía</h3>
                <p>Crea el primero pulsando "Nuevo Resumen" y pegando una URL de video.</p>
            </div>`;
    }
}

// ─── Detail View ─────────────────────────────────────────────────────────────

async function showDetail(id) {
    document.getElementById('hero').style.display = 'none';
    document.getElementById('results').style.display = 'none';
    document.getElementById('result-detail').style.display = '';

    const metaEl = document.getElementById('result-meta');
    const contentEl = document.getElementById('result-content');

    metaEl.innerHTML = '<div class="loading">Cargando...</div>';
    contentEl.innerHTML = '';

    try {
        // Load metadata
        const metaResp = await fetch(`${DATA_BASE}/${id}.json`);
        const meta = await metaResp.json();

        metaEl.innerHTML = `
            <h2>${escapeHtml(meta.title)}</h2>
            <div class="meta">
                <span>⏱️ ${meta.duration_minutes} min</span>
                <span>📝 ${meta.transcript_chars.toLocaleString()} chars transcripción</span>
                <span>🖼️ ${meta.frames_analyzed} frames analizados</span>
                <span>💚 Coste: $${meta.cost_usd.toFixed(2)}</span>
                <span>🤖 ${meta.models.summary}</span>
                <span>📅 ${formatDate(meta.timestamp)}</span>
            </div>`;

        // Load summary markdown
        const mdResp = await fetch(`${DATA_BASE}/${id}.md`);
        const md = await mdResp.text();
        contentEl.innerHTML = marked.parse(md);
    } catch (e) {
        metaEl.innerHTML = '';
        contentEl.innerHTML = `<div class="empty-state"><h3>Resultado no encontrado</h3></div>`;
    }
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function formatDate(isoString) {
    try {
        return new Date(isoString).toLocaleDateString('es-ES', {
            year: 'numeric', month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit',
        });
    } catch {
        return isoString;
    }
}

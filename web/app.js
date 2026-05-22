/* 三国文字Roguelike - Web UI Client */
const API = '/api';

let currentState = null;

// ── API Calls ────────────────────────────────────────
async function apiGetState() {
    const res = await fetch(`${API}/state`);
    return res.json();
}

async function apiNewGame() {
    const res = await fetch(`${API}/new_game`, { method: 'POST' });
    return res.json();
}

async function apiTick() {
    const res = await fetch(`${API}/tick`, { method: 'POST' });
    return res.json();
}

async function apiMove(target) {
    const res = await fetch(`${API}/move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target })
    });
    return res.json();
}

async function apiCombat(choice, skill = null) {
    const res = await fetch(`${API}/combat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ choice: String(choice), skill })
    });
    return res.json();
}

async function apiNpc(choice) {
    const res = await fetch(`${API}/npc`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ choice: String(choice) })
    });
    return res.json();
}

async function apiMarket(cmd) {
    const res = await fetch(`${API}/market`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cmd })
    });
    return res.json();
}

async function apiIntel() {
    const res = await fetch(`${API}/intel`, { method: 'POST' });
    return res.json();
}

async function apiMap() {
    const res = await fetch(`${API}/map`, { method: 'POST' });
    return res.json();
}

async function apiStatus() {
    const res = await fetch(`${API}/status`, { method: 'POST' });
    return res.json();
}

// ── UI Functions ──────────────────────────────────────
function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
}

function scrollToBottom() {
    const el = document.getElementById('narrative-area');
    if (el) el.scrollTop = el.scrollHeight;
}

function addNarrative(text) {
    const area = document.getElementById('narrative-area');
    if (!area || !text) return;
    const lines = text.split('\n');
    lines.forEach(line => {
        if (!line.trim()) return;
        const div = document.createElement('div');
        div.className = 'narrative-entry';
        div.textContent = line;
        area.appendChild(div);
    });
    scrollToBottom();
}

function clearNarrative() {
    const area = document.getElementById('narrative-area');
    if (area) area.innerHTML = '';
}

function updateStats(state) {
    const p = state.player;
    document.getElementById('disp-time').textContent = state.time;
    document.getElementById('disp-loc').textContent = p.location;
    document.getElementById('disp-rank').textContent = p.rank;
    document.getElementById('disp-name').textContent = p.name;

    document.getElementById('val-hp').textContent = p.hp;
    document.getElementById('bar-hp').style.width = p.hp + '%';
    document.getElementById('val-morale').textContent = p.morale;
    document.getElementById('bar-morale').style.width = p.morale + '%';
    document.getElementById('val-stamina').textContent = p.stamina;
    document.getElementById('bar-stamina').style.width = p.stamina + '%';
    document.getElementById('val-gold').textContent = p.gold;
    document.getElementById('val-food').textContent = p.food;
    document.getElementById('val-exp').textContent = p.exp;

    const stats = p.stats;
    document.getElementById('stat-wu').textContent = stats['武'] || 0;
    document.getElementById('stat-zhi').textContent = stats['智'] || 0;
    document.getElementById('stat-ming').textContent = stats['名'] || 0;
    document.getElementById('stat-mei').textContent = stats['魅'] || 0;
    document.getElementById('stat-yun').textContent = stats['运'] || 0;
}

function renderActionPanel(state) {
    const panel = document.getElementById('action-panel');
    if (!panel) return;
    panel.innerHTML = '';

    const ui = state.ui_state;

    if (ui === 'combat') {
        renderCombat(state, panel);
    } else if (ui === 'npc') {
        renderNpc(state, panel);
    } else if (ui === 'market') {
        renderMarket(state, panel);
    } else {
        renderNormalActions(state, panel);
    }
}

function renderCombat(state, panel) {
    const cd = state.combat_data;
    let html = `<div class="combat-enemy">
        <div class="enemy-name">⚔️ ${cd.enemy.name}</div>
        <div class="enemy-stats">敌军：${cd.enemy.troops}人 | 士气：${cd.enemy.morale} | 地形：${cd.enemy.terrain}</div>
        <div class="enemy-stats">我军：${cd.player_army}人 | 士气：${cd.player_morale}</div>
    </div>`;

    html += '<div class="action-row">';
    cd.actions.forEach(a => {
        html += `<button class="action-btn primary" onclick="doCombat(${a.id})">${a.label}<div class="btn-sub">${a.desc}</div></button>`;
    });
    html += '</div>';

    if (cd.skills && cd.skills.length > 0) {
        html += '<div class="action-row" style="margin-top:6px">';
        cd.skills.forEach(s => {
            html += `<button class="action-btn skill-btn" onclick="doCombatSkill('${s.id}')">${s.name}<div class="btn-sub">${s.desc}</div></button>`;
        });
        html += '</div>';
    }

    panel.innerHTML = html;
}

function renderNpc(state, panel) {
    const nd = state.npc_data;
    let html = `<div class="npc-info">
        <div class="npc-name">🎭 ${nd.name}（${nd.rank}）</div>
        <div class="rel-tag">${nd.relation_tag} 好感度：${nd.relation}</div>
    </div>`;

    html += '<div class="action-row">';
    nd.options.forEach(opt => {
        const disabled = (opt.id === '2' && state.player.gold < 30) ||
                        (opt.id === '4' && state.player.gold < 20) ||
                        (opt.id === '3' && state.player.stats['名'] < 50) ? 'disabled' : '';
        html += `<button class="action-btn" onclick="doNpc('${opt.id}')" ${disabled}>${opt.label}<div class="btn-sub">${opt.desc}</div></button>`;
    });
    html += '</div>';

    panel.innerHTML = html;
}

function renderMarket(state, panel) {
    const md = state.market_data;
    panel.innerHTML = `
        <div class="market-info">💰 金：${md.player_gold} | 🍖 粮草：${md.player_food}</div>
        <div class="action-row">
            <button class="action-btn" onclick="doMarket('buy food 10')">买粮草10💰5金</button>
            <button class="action-btn" onclick="doMarket('sell food 10')">卖粮草10💰+5金</button>
        </div>
        <div class="action-row" style="margin-top:6px">
            <button class="action-btn danger" onclick="doMarket('leave')">离开市集</button>
        </div>
    `;
}

function renderNormalActions(state, panel) {
    const moves = state.available_moves || [];
    let html = '<div class="action-row">';
    moves.forEach(city => {
        const isAdjacent = true; // all returned cities are adjacent
        html += `<button class="action-btn" onclick="doMove('${city}')">📍 ${city}</button>`;
    });
    html += '</div>';
    panel.innerHTML = html;
}

function renderMap(state, panel) {
    const map = state.map;
    let html = '<div class="map-area">';
    Object.entries(map.regions).forEach(([regKey, regData]) => {
        html += `<div class="map-region-title">${regData.name}</div>`;
        regData.cities.forEach(city => {
            let cls = 'map-city';
            if (city === map.current) cls += ' current';
            else if (map.current && state.available_moves && state.available_moves.includes(city)) cls += ' adjacent';
            html += `<div class="${cls}">${city === map.current ? '★ ' : '　 '}${city}</div>`;
        });
    });
    html += '</div>';
    html += '<div class="action-row" style="margin-top:8px"><button class="action-btn" onclick="renderActionPanel(currentState)">返回</button></div>';
    panel.innerHTML = html;
}

// ── Action Handlers ──────────────────────────────────
async function newGame() {
    const state = await apiNewGame();
    if (!state || state.game_status === 'error') {
        alert('创建游戏失败');
        return;
    }
    currentState = state;
    showScreen('game-screen');
    clearNarrative();
    updateStats(state);
    renderActionPanel(state);
    if (state.narrative) addNarrative(state.narrative);
}

async function refreshState(state) {
    if (!state) state = await apiGetState();
    currentState = state;
    updateStats(state);
    renderActionPanel(state);
    if (state.narrative) addNarrative(state.narrative);
}

async function doTick() {
    const state = await apiTick();
    if (!state || state.game_status === 'error') return;
    currentState = state;
    updateStats(state);
    renderActionPanel(state);
    if (state.narrative) addNarrative(state.narrative);
}

async function doMove(target) {
    const state = await apiMove(target);
    if (!state || state.game_status === 'error') return;
    currentState = state;
    updateStats(state);
    renderActionPanel(state);
    if (state.narrative) addNarrative(state.narrative);
}

async function doCombat(actionId) {
    const state = await apiCombat(actionId);
    if (!state || state.game_status === 'error') return;
    currentState = state;
    updateStats(state);
    renderActionPanel(state);
    if (state.narrative) addNarrative(state.narrative);
}

async function doCombatSkill(skillId) {
    const state = await apiCombat(1, skillId);
    if (!state || state.game_status === 'error') return;
    currentState = state;
    updateStats(state);
    renderActionPanel(state);
    if (state.narrative) addNarrative(state.narrative);
}

async function doNpc(choiceId) {
    const state = await apiNpc(choiceId);
    if (!state || state.game_status === 'error') return;
    currentState = state;
    updateStats(state);
    renderActionPanel(state);
    if (state.narrative) addNarrative(state.narrative);
}

async function doMarket(cmd) {
    const state = await apiMarket(cmd);
    if (!state || state.game_status === 'error') return;
    currentState = state;
    updateStats(state);
    renderActionPanel(state);
    if (state.narrative) addNarrative(state.narrative);
}

async function apiMap() {
    const state = await apiMap();
    if (!state || state.game_status === 'error') return;
    currentState = state;
    const panel = document.getElementById('action-panel');
    if (panel) renderMap(state, panel);
    if (state.narrative) addNarrative(state.narrative);
}

async function apiStatus() {
    const state = await apiStatus();
    if (!state || state.game_status === 'error') return;
    currentState = state;
    updateStats(state);
    renderActionPanel(state);
    if (state.narrative) addNarrative(state.narrative);
}

// ── Init ─────────────────────────────────────────────
document.getElementById('btn-new-game').addEventListener('click', newGame);

// Auto-refresh state on page load
apiGetState().then(state => {
    if (state && state.game_status === 'playing') {
        currentState = state;
        showScreen('game-screen');
        updateStats(state);
        if (state.narrative) addNarrative(state.narrative);
        renderActionPanel(state);
    }
}).catch(() => {});
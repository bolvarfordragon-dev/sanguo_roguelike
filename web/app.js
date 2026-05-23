/* 三国文字Roguelike - Web UI Client */
const API = '/api';

let currentState = null;

// ── API Calls ────────────────────────────────────────
async function callAPI(method, endpoint, body) {
    const res = await fetch(`${API}${endpoint}`, {
        method,
        headers: body ? { 'Content-Type': 'application/json' } : {},
        body: body ? JSON.stringify(body) : undefined,
    });
    return res.json();
}

async function apiGetState() {
    return callAPI('GET', '/state');
}

async function apiNewGame() {
    return callAPI('POST', '/new_game');
}

async function apiTick() {
    return callAPI('POST', '/tick');
}

async function apiMove(target) {
    return callAPI('POST', '/move', { target });
}

async function apiCombat(choice, skill) {
    return callAPI('POST', '/combat', { choice: String(choice), skill });
}

async function apiNpc(choice) {
    return callAPI('POST', '/npc', { choice: String(choice) });
}

async function apiMarket(cmd) {
    return callAPI('POST', '/market', { cmd });
}

async function apiIntel() {
    return callAPI('POST', '/intel');
}

async function apiShowMap() {
    return callAPI('POST', '/map');
}

async function apiShowStatus() {
    return callAPI('POST', '/status');
}

async function apiEnterMarket() {
    return callAPI('POST', '/enter_market');
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
    if (!state || !state.player) return;
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

function applyState(state) {
    currentState = state;
    updateStats(state);
    renderActionPanel(state);
    if (state.narrative) addNarrative(state.narrative);
}

// ── Render action panel by ui_state ──────────────────
function renderActionPanel(state) {
    const panel = document.getElementById('action-panel');
    if (!panel) return;
    panel.innerHTML = '';

    const ui = state.ui_state;
    if (ui === 'combat') renderCombat(state, panel);
    else if (ui === 'npc') renderNpc(state, panel);
    else if (ui === 'market') renderMarket(state, panel);
    else renderNormal(state, panel);
}

function renderCombat(state, panel) {
    const cd = state.combat_data;
    panel.innerHTML = `
        <div class="combat-enemy">
            <div class="enemy-name">⚔️ ${cd.enemy.name}</div>
            <div class="enemy-stats">敌军：${cd.enemy.troops}人 | 士气：${cd.enemy.morale} | 地形：${cd.enemy.terrain}</div>
            <div class="enemy-stats">我军：${cd.player_army}人 | 士气：${cd.player_morale}</div>
        </div>
        <div class="action-row">
            ${cd.actions.map(a => `
                <button class="action-btn primary" onclick="doCombat(${a.id})">${a.label}<div class="btn-sub">${a.desc}</div></button>
            `).join('')}
        </div>
        ${cd.skills && cd.skills.length > 0 ? `
            <div class="action-row" style="margin-top:6px">
                ${cd.skills.map(s => `
                    <button class="action-btn skill-btn" onclick="doCombatSkill('${s.id}')">${s.name}<div class="btn-sub">${s.desc}</div></button>
                `).join('')}
            </div>
        ` : ''}
    `;
}

function renderNpc(state, panel) {
    const nd = state.npc_data;
    panel.innerHTML = `
        <div class="npc-info">
            <div class="npc-name">🎭 ${nd.name}（${nd.rank}）</div>
            <div class="rel-tag">${nd.relation_tag} 好感度：${nd.relation}</div>
        </div>
        <div class="action-row">
            ${nd.options.map(opt => {
                const disabled = (opt.id === '2' && state.player.gold < 30) ||
                                (opt.id === '4' && state.player.gold < 20) ||
                                (opt.id === '3' && state.player.stats['名'] < 50) ? 'disabled' : '';
                return `<button class="action-btn" onclick="doNpc('${opt.id}')" ${disabled}>${opt.label}<div class="btn-sub">${opt.desc}</div></button>`;
            }).join('')}
        </div>
    `;
}

function renderMarket(state, panel) {
    const md = state.market_data;
    panel.innerHTML = `
        <div class="market-info">💰 金：${md.player_gold} | 🍖 粮草：${md.player_food}</div>
        <div class="action-row">
            <button class="action-btn" onclick="doMarket('buy')">🏪 买粮草<div class="btn-sub">10金 → 15粮</div></button>
            <button class="action-btn" onclick="doMarket('sell')">💰 卖粮草<div class="btn-sub">15粮 → 8金</div></button>
        </div>
        <div class="action-row" style="margin-top:6px">
            <button class="action-btn danger" onclick="doMarket('leave')">🚶 离开市集</button>
        </div>
    `;
}

function renderNormal(state, panel) {
    // ── Render normal (city arrival) state ──
    // Show: adjacent city moves + market/intel shortcuts
    const moves = state.available_moves || [];
    let html = '<div class="action-row city-actions">';
    html += `<button class="action-btn market-btn" onclick="doMarketAuto()">🏪 市集<div class="btn-sub">买卖粮草</div></button>`;
    html += `<button class="action-btn intel-btn" onclick="doIntelAuto()">📰 情报<div class="btn-sub">20金打听NPC</div></button>`;
    html += '</div>';

    if (moves.length > 0) {
        html += '<div class="action-row">';
        moves.forEach(city => {
            html += `<button class="action-btn" onclick="doMove('${city}')">📍 ${city}</button>`;
        });
        html += '</div>';
    }
    panel.innerHTML = html;
}

function renderMapView(state, panel) {
    const map = state.map;
    let html = '<div class="map-grid">';
    Object.entries(map.regions).forEach(([regKey, regData]) => {
        html += `<div class="map-region">
            <div class="map-region-title">${regData.name}</div>`;
        regData.cities.forEach(city => {
            let cls = 'map-city-btn';
            if (city === map.current) cls += ' current';
            else if (map.current && state.available_moves && state.available_moves.includes(city)) cls += ' adjacent';
            const icon = city === map.current ? '★' : (state.available_moves && state.available_moves.includes(city) ? '→' : '·');
            html += `<button class="${cls}" onclick="doMove('${city}')">${icon} ${city}</button>`;
        });
        html += '</div>';
    });
    html += '</div>';
    html += '<div class="action-row" style="margin-top:8px"><button class="action-btn" onclick="renderActionPanel(currentState)">← 返回</button></div>';
    panel.innerHTML = html;
}

// ── Action Handlers ──────────────────────────────────
async function newGame() {
    const state = await apiNewGame();
    if (!state || state.game_status === 'error') {
        alert('创建游戏失败');
        return;
    }
    showScreen('game-screen');
    clearNarrative();
    applyState(state);
}

async function doTick() {
    const state = await apiTick();
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

async function doMove(target) {
    const state = await apiMove(target);
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

async function doCombat(actionId) {
    const state = await apiCombat(actionId, null);
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

async function doCombatSkill(skillId) {
    const state = await apiCombat(1, skillId);
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

async function doNpc(choiceId) {
    const state = await apiNpc(choiceId);
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

async function doMarket(cmd) {
    const state = await apiMarket(cmd);
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

// Enter market UI
async function doMarketAuto() {
    const state = await apiEnterMarket();
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

// Intel without full state replacement (adds to narrative only)
async function doIntelAuto() {
    const state = await apiIntel();
    if (!state || state.game_status === 'error') return;
    if (state.narrative) addNarrative(state.narrative);
    if (currentState && state.player) {
        currentState.player.gold = state.player.gold;
        document.getElementById('val-gold').textContent = state.player.gold;
    }
}

async function doShowMap() {
    const state = await apiShowMap();
    if (!state || state.game_status === 'error') return;
    const panel = document.getElementById('action-panel');
    if (panel) renderMapView(state, panel);
    if (state.narrative) addNarrative(state.narrative);
}

async function doShowStatus() {
    const state = await apiShowStatus();
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

async function doIntel() {
    const state = await apiIntel();
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

// ── Init ─────────────────────────────────────────────
document.getElementById('btn-new-game').addEventListener('click', newGame);

// Auto-load state on page load
apiGetState().then(state => {
    if (state && state.game_status === 'playing') {
        currentState = state;
        showScreen('game-screen');
        updateStats(state);
        if (state.narrative) addNarrative(state.narrative);
        renderActionPanel(state);
    }
}).catch(() => {});
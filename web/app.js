/* 三国文字Roguelike - Web UI Client (v3 with campaigns, choices, equipment) */
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

async function apiVisitTavern() {
    return callAPI('POST', '/tavern');
}

async function apiTavernChoice(choiceIdx) {
    return callAPI('POST', '/tavern_choice', { choice: String(choiceIdx) });
}

async function apiCampaignChoice(accept, side) {
    return callAPI('POST', '/campaign_choice', { accept, side });
}

async function apiChoice(choiceId) {
    return callAPI('POST', '/choice', { choice_id: String(choiceId) });
}

async function apiEquipment(action, slotIndex) {
    return callAPI('POST', '/equipment', { action, slot_index: slotIndex });
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

    // Show city favorability next to location
    const locEl = document.getElementById('disp-loc');
    const fav = (state.city_favorability && state.city_favorability[p.location]) || 50;
    const favColor = fav >= 70 ? '#88cc88' : (fav <= 30 ? '#cc4444' : '#9a7620');
    const favBar = `<span style="font-size:11px;color:${favColor};margin-left:4px">❤${fav}</span>`;
    if (!locEl.dataset.favbar) {
        locEl.dataset.favbar = '1';
        const wrapper = document.createElement('span');
        wrapper.id = 'fav-bar';
        locEl.parentNode.insertBefore(wrapper, locEl.nextSibling);
    }
    const fb = document.getElementById('fav-bar');
    if (fb) fb.innerHTML = favBar;

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
    renderRunStats(state);
    renderActionPanel(state);
    renderEquipmentPanel(state);
    if (state.narrative) addNarrative(state.narrative);
}

// ── Run stats bar ─────────────────────────────────
function renderRunStats(state) {
    const el = document.getElementById('run-stats-row');
    if (!el) return;
    const rs = state.run_stats;
    if (!rs) { el.style.display = 'none'; return; }

    const total = (rs.wins || 0) + (rs.losses || 0);
    const winRate = total > 0 ? Math.round((rs.wins || 0) / total * 100) : 0;
    const streak = (rs.win_streak || 0) > 0
        ? `连胜${rs.win_streak}`
        : (rs.lose_streak || 0) > 0 ? `连败${rs.lose_streak}` : '';

    const months = state.player && state.player._engine_ref
        ? (function() {
            const y = state.year || 184;
            const m = state.month || 1;
            return (y - 184) * 12 + m;
        })()
        : 0;

    el.style.display = 'flex';
    el.innerHTML = `
        <span>⚔️ 战斗${total}场</span>
        <span style="color:${winRate>=50?'#2ecc71':'#e74c3c'}">胜率${winRate}%</span>
        ${streak ? `<span style="color:#f39c12">${streak}</span>` : ''}
        <span>🎭 招募${(rs.npcs_recruited_this_run||[]).length}人</span>
        <span>📅 第${months}月</span>
    `;
}


function renderActionPanel(state) {
    const panel = document.getElementById('action-panel');
    if (!panel) return;
    panel.innerHTML = '';

    // Show campaign/choice banners above the panel
    renderTopBanners(state);

    const ui = state.ui_state;
    if (ui === 'combat') renderCombat(state, panel);
    else if (ui === 'npc') renderNpc(state, panel);
    else if (ui === 'market') renderMarket(state, panel);
    else if (ui === 'tavern_choice') renderTavernChoice(state, panel);
    else renderNormal(state, panel);
}

function renderTopBanners(state) {
    const banners = document.getElementById('top-banners');
    if (banners) banners.innerHTML = '';
    else return;

    // Campaign pending banner
    if (state.pending_campaign) {
        renderCampaignPendingBanner(state, banners);
    }
    // Choice event banner
    if (state.pending_choice && state.pending_choice.id) {
        renderChoicePendingBanner(state, banners);
    }
    // Equipment drop banner
    if (state.pending_equipment) {
        renderEquipDropBanner(state, banners);
    }
    // Active campaign indicator
    if (state.active_campaign) {
        renderActiveCampaignBanner(state, banners);
    }
}

function renderCampaignPendingBanner(state, container) {
    const c = state.pending_campaign;
    const div = document.createElement('div');
    div.className = 'campaign-panel';
    let rewardsHtml = '';
    if (c.rewards && c.rewards.length) {
        rewardsHtml = c.rewards.map(r =>
            `<div>·「${r.name}」- ${r.desc}</div>`
        ).join('');
    }
    const acceptBtn = `<button class="action-btn primary" onclick="doCampaignAccept()">⚔️ 参加战役</button>`;
    const declineBtn = `<button class="action-btn danger" onclick="doCampaignDecline()">🚶 婉拒</button>`;
    const sideSection = c.side_choice ? `
        <div class="side-choice-panel">
            <div style="font-size:12px;color:#9a7620;margin-bottom:4px;text-align:center">请选择阵营：</div>
            <div class="action-row">
                <button class="action-btn" onclick="doCampaignAccept('wu')">🤝 联吴抗曹</button>
                <button class="action-btn" onclick="doCampaignAccept('wei')">⚔️ 联曹灭吴</button>
            </div>
        </div>` : '';

    div.innerHTML = `
        <div class="campaign-title">⚔️ 【${c.name}】</div>
        <div class="campaign-desc">${c.description}</div>
        <div class="campaign-info">
            <span class="campaign-badge">⏱️ 持续${c.duration}月</span>
            <span class="campaign-badge">⚠️ 粮草消耗翻倍</span>
        </div>
        ${c.rewards && c.rewards.length ? `
        <div class="campaign-rewards">
            <div class="campaign-rewards-title">🏆 战役奖励</div>
            ${rewardsHtml}
        </div>` : ''}
        <div class="campaign-actions">${acceptBtn}${declineBtn}</div>
        ${sideSection}
    `;
    container.appendChild(div);
}

function renderChoicePendingBanner(state, container) {
    const c = state.pending_choice;
    const div = document.createElement('div');
    div.className = 'choice-panel';
    const optionsHtml = (c.options || []).map(opt => `
        <button class="choice-btn" onclick="doChoice('${opt.id}')">
            <span class="choice-btn-label">${opt.label}</span>
            <span class="choice-btn-desc">${opt.desc}</span>
        </button>
    `).join('');
    div.innerHTML = `
        <div class="choice-title">⚖️ 【${c.name}】</div>
        <div class="choice-desc">${c.description}</div>
        <div class="choice-options">${optionsHtml}</div>
    `;
    container.appendChild(div);
}

function renderEquipDropBanner(state, container) {
    const eq = state.pending_equipment;
    const div = document.createElement('div');
    const tier = eq.tier || '普通';
    const tierCls = {
        '普通': 'tier-common',
        '精良': 'tier-fine',
        '史诗': 'tier-epic',
        '传奇': 'tier-legendary',
    }[tier] || 'tier-common';
    div.className = `equip-drop-banner ${tierCls}`;
    div.id = 'equip-drop-banner';
    const tierIcon = {'普通':'⚪','精良':'🔵','史诗':'🟣','传奇':'🟠'}[tier] || '⚪';
    const slots = state.player && state.player.equipment ? state.player.equipment : [];
    const slotsHtml = slots.length < 3 ? '' :
        `<div style="font-size:12px;color:#9a7620;margin-top:6px">⚠️ 装备槽已满，请选择一个装备替换：</div>
        <div class="action-row" style="margin-top:4px">
            ${slots.map((s, i) => `<button class="action-btn" onclick="doEquipReplace(${i})">${s.name}</button>`).join('')}
            <button class="action-btn danger" onclick="doEquipDrop()">丢弃新装备</button>
        </div>`;
    div.innerHTML = `
        <span class="equip-name">${tierIcon} 拾获装备「${eq.name}」</span>
        <span class="equip-desc">${eq.desc}</span>
        ${slots.length >= 3 ? slotsHtml : `
        <div class="equip-actions">
            <button class="action-btn primary" onclick="doEquipReplace(null)">自动装备</button>
            <button class="action-btn danger" onclick="doEquipDrop()">丢弃</button>
        </div>`}
    `;
    container.appendChild(div);
}

function renderActiveCampaignBanner(state, container) {
    const ac = state.active_campaign;
    if (!ac) return;
    const div = document.createElement('div');
    div.className = 'campaign-active-badge';
    div.textContent = `⚔️ 战役进行中：${ac.name}`;
    container.appendChild(div);
}

function renderEquipmentPanel(state) {
    const panel = document.getElementById('equipment-panel');
    if (!panel) return;
    panel.innerHTML = '';

    const equip = (state.player && state.player.equipment) ? state.player.equipment : [];
    const slots = [];
    for (let i = 0; i < 3; i++) {
        slots.push(equip[i] || null);
    }

    const typeIcons = {
        "weapon": "⚔️", "accessory": "💍", "banner": "🚩",
        "mount": "🐎", "book": "📖", "armor": "🛡️"
    };

    let html = `<div class="equipment-panel">
        <div class="equipment-title">⚙️ 装备（${equip.length}/3）</div>
        <div class="equipment-slots">`;
    const tierCls = {
        '普通': 'equip-common',
        '精良': 'equip-fine',
        '史诗': 'equip-epic',
        '传奇': 'equip-legendary',
    };
    slots.forEach((item, idx) => {
        if (item) {
            const icon = typeIcons[item.type] || '📦';
            const statsStr = Object.entries(item.stats || {}).map(([k, v]) => `${k}+${v}`).join(' ');
            const t = item.tier || '普通';
            html += `<div class="eq-slot filled ${tierCls[t] || ''}" title="${item.name}\n${item.desc}\n${statsStr}" onclick="doUnequipSlot(${idx})">
                <div class="eq-slot-icon">${icon}</div>
                <div class="eq-slot-name">${item.name}</div>
                <div class="eq-slot-stats">${statsStr}</div>
            </div>`;
        } else {
            html += `<div class="eq-slot" title="空装备槽">
                <div class="eq-slot-icon">➕</div>
                <div class="eq-slot-name empty-label">空槽位</div>
            </div>`;
        }
    });
    html += `</div></div>`;
    panel.innerHTML = html;
}

function renderCombat(state, panel) {
    const cd = state.combat_data;
    panel.innerHTML = `
        <div class="combat-enemy">
            <div class="enemy-name">⚔️ ${cd.enemy.name}</div>
            <div class="enemy-stats">敌军：${cd.enemy.troops}人 | 地形：${cd.enemy.terrain}</div>
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
                    <button class="action-btn skill-btn" onclick='showSkillModal(${JSON.stringify(s).replace(/'/g, "\\'")})'>${s.name}<div class="btn-sub">${s.desc}</div></button>
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

function renderTavernChoice(state, panel) {
    const npcs = state.tavern_npcs || [];
    let html = '<div class="tavern-info">🍶 酒馆中有数人，请选择拜访：</div>';
    html += '<div class="action-row" style="flex-direction:column;gap:6px">';
    npcs.forEach(npc => {
        html += `<button class="action-btn" onclick="doTavernChoice('${npc.id}')">${npc.name}（${npc.rank}）</button>`;
    });
    html += '</div>';
    html += '<div class="action-row" style="margin-top:6px"><button class="action-btn" onclick="doTavernCancel()">← 离开酒馆</button></div>';
    panel.innerHTML = html;
}

function renderNormal(state, panel) {
    const moves = state.available_moves || [];
    let html = '<div class="action-row city-actions">';
    html += `<button class="action-btn market-btn" onclick="doMarketAuto()">🏪 市集<div class="btn-sub">买卖粮草</div></button>`;
    html += `<button class="action-btn tavern-btn" onclick="doVisitTavern()">🍶 酒馆<div class="btn-sub">拜访/打听</div></button>`;
    html += `<button class="action-btn intel-btn" onclick="doIntelAuto()">📰 情报<div class="btn-sub">20金打听NPC</div></button>`;
    html += `<button class="action-btn map-btn" onclick="doShowMap()">🗺️ 地图<div class="btn-sub">查看地图</div></button>`;
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
    const cf = state.city_favorability || {};
    function getFavColor(city) {
        const fav = cf[city] || 50;
        if (fav >= 70) return '#2e8b57';
        if (fav >= 90) return '#88cc88';
        if (fav <= 30) return '#8b0000';
        return '#9a7620';
    }
    function getFavBar(city) {
        const fav = cf[city] || 50;
        const color = getFavColor(city);
        return `<span style="display:inline-block;width:30px;height:4px;background:${color};border-radius:2px;vertical-align:middle;margin-left:4px"></span>`;
    }
    let html = '<div class="map-grid">';
    Object.entries(map.regions).forEach(([regKey, regData]) => {
        html += `<div class="map-region">
            <div class="map-region-title">${regData.name}</div>`;
        regData.cities.forEach(city => {
            const isCurrent = city === map.current;
            const isAdjacent = state.available_moves && state.available_moves.includes(city);
            let cls = 'map-city-btn';
            if (isCurrent) cls += ' current';
            else if (isAdjacent) cls += ' adjacent';
            else cls += ' other-city';
            const icon = isCurrent ? '★' : (isAdjacent ? '→' : '·');
            const favBar = getFavBar(city);
            html += `<div class="map-city-wrap"><button class="${cls}" onclick="doMove('${city}')">${icon} ${city}</button>${favBar}</div>`;
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

// =============================================
// 技能详情弹窗
// =============================================
function showSkillModal(skill) {
    // 如果已显示则关闭
    const existing = document.getElementById('skill-modal-overlay');
    if (existing) { existing.remove(); return; }

    const typeLabel = skill.skill_type === 'active' ? '「主动」' : '「被动」';
    const typeColor = skill.skill_type === 'active' ? '#e74c3c' : '#3498db';

    // 属性要求HTML
    let reqHtml = '';
    if (skill.stat_req) {
        const entries = Object.entries(skill.stat_req);
        reqHtml = entries.map(([k, v]) => {
            const playerStat = state.player.stats[k];
            const ok = playerStat >= v;
            return `<span style="color:${ok ? '#2ecc71' : '#e74c3c'}">${k} ${playerStat}/${v}</span>`;
        }).join(' ');
    }

    // 消耗
    const costHtml = skill.cost === 0
        ? '<span style="color:#f39c12">NPC赠送</span>'
        : `<span style="color:#f1c40f">消耗碎片：${skill.cost}枚</span>`;

    // 前置
    const prereqHtml = skill.prereq
        ? `<div style="margin-top:6px;color:#e67e22">前置：需要先学会 [${skill.prereq}]</div>`
        : '';

    const overlay = document.createElement('div');
    overlay.id = 'skill-modal-overlay';
    overlay.style.cssText = `
        position:fixed;top:0;left:0;right:0;bottom:0;
        background:rgba(0,0,0,0.7);z-index:1000;
        display:flex;align-items:flex-end;justify-content:center;
        padding:20px;
    `;
    overlay.onclick = (e) => { if (e.target===overlay) overlay.remove(); };

    overlay.innerHTML = `
        <div style="
            background:#1a1a2e;color:#eee;
            border-radius:16px;padding:20px;max-width:360px;width:100%;
            font-family:'Noto Serif SC',serif;
            box-shadow:0 -4px 30px rgba(0,0,0,0.5);
        ">
            <div style="font-size:20px;font-weight:700;margin-bottom:10px">
                ⚔️ ${skill.name}
                <span style="font-size:14px;color:${typeColor};margin-left:8px">${typeLabel}</span>
            </div>
            <div style="font-size:14px;color:#b0b0b0;margin-bottom:12px;line-height:1.5">
                ${skill.desc}
            </div>
            ${reqHtml ? `<div style="margin-bottom:8px">📋 属性要求：${reqHtml}</div>` : ''}
            <div style="margin-bottom:8px">💎 ${costHtml}</div>
            ${prereqHtml}
            <button onclick="this.closest('#skill-modal-overlay').remove(); doCombatSkill('${skill.id}')"
                style="
                    width:100%;margin-top:14px;padding:12px;
                    background:#c0392b;color:#fff;border:none;border-radius:10px;
                    font-size:15px;font-weight:700;cursor:pointer;
                ">使用技能</button>
        </div>
    `;
    document.body.appendChild(overlay);
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

async function doMarketAuto() {
    const state = await apiEnterMarket();
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

async function doIntelAuto() {
    const state = await apiIntel();
    if (!state || state.game_status === 'error') return;
    if (state.narrative) addNarrative(state.narrative);
    if (currentState && state.player) {
        currentState.player.gold = state.player.gold;
        document.getElementById('val-gold').textContent = state.player.gold;
    }
}

async function doVisitTavern() {
    const state = await apiVisitTavern();
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

async function doTavernChoice(npcId) {
    const state = await apiTavernChoice(npcId);
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

async function doTavernCancel() {
    const state = await apiTavernChoice(0);
    if (!state || state.game_status === 'error') return;
    applyState(state);
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

// ── Campaign handlers ─────────────────────────────────
async function doCampaignAccept(side) {
    const state = await apiCampaignChoice(true, side || null);
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

async function doCampaignDecline() {
    const state = await apiCampaignChoice(false, null);
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

// ── Choice event handlers ─────────────────────────────
async function doChoice(choiceId) {
    const state = await apiChoice(choiceId);
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

// ── Equipment handlers ────────────────────────────────
async function doEquipReplace(slotIndex) {
    const state = await apiEquipment('replace', slotIndex);
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

async function doEquipDrop() {
    const state = await apiEquipment('drop', null);
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

async function doUnequipSlot(slotIndex) {
    const state = await apiEquipment('drop', slotIndex);
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

// ── Achievements ──────────────────────────────────────
async function doShowAchievements() {
    const data = await callAPI('GET', '/achievements');
    renderAchievementsPanel(data);
    showScreen('achievements-panel');
}

function renderAchievementsPanel(data) {
    const list = document.getElementById('ach-list');
    if (!list || !data) return;
    list.innerHTML = `<div class="ach-summary">已解锁：${data.unlocked} / ${data.total}</div>`;
    data.achievements.forEach(ach => {
        const cls = ach.unlocked ? 'ach-item unlocked' : 'ach-item locked';
        const status = ach.unlocked ? '✅' : '🔒';
        const desc = ach.unlocked ? ach.desc : '???';
        list.innerHTML += `
            <div class="${cls}">
                <div class="ach-icon">${ach.icon}</div>
                <div class="ach-info">
                    <div class="ach-name">${status} ${ach.name}</div>
                    <div class="ach-desc">${desc}</div>
                </div>
            </div>`;
    });
}

function closeAchievements() {
    showScreen('game-screen');
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
        renderEquipmentPanel(state);
    }
}).catch(() => {});
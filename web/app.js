/* 三国文字Roguelike - Web UI Client (v3 with campaigns, choices, equipment) */
const API = '/api';
const SAVE_KEY = 'sanguo_game_v1';

let currentState = null;

// ── localStorage Save / Load ──────────────────────────
async function saveGame(state) {
    try {
        localStorage.setItem(SAVE_KEY, JSON.stringify(state));
    } catch (e) {
        console.warn('localStorage save failed:', e);
    }
}

function loadSavedGame() {
    try {
        const raw = localStorage.getItem(SAVE_KEY);
        return raw ? JSON.parse(raw) : null;
    } catch (e) {
        return null;
    }
}

function clearSavedGame() {
    try { localStorage.removeItem(SAVE_KEY); } catch(e) {}
}

// ── Loading indicator ──────────────────────────────
function showLoading(show) {
    let el = document.getElementById('loading-indicator');
    if (!el) {
        el = document.createElement('div');
        el.id = 'loading-indicator';
        el.innerHTML = '<div class="loading-spinner"></div>';
        document.body.appendChild(el);
    }
    el.style.display = show ? 'flex' : 'none';
}

// ── API Calls ────────────────────────────────────────
async function callAPI(method, endpoint, body) {
    showLoading(true);
    const res = await fetch(`${API}${endpoint}`, {
        method,
        headers: body ? { 'Content-Type': 'application/json' } : {},
        body: body ? JSON.stringify(body) : undefined,
    });
    const data = await res.json();
    showLoading(false);
    // Auto-save after every API call (if valid game state)
    if (data && data.game_status && data.game_status !== 'error') {
        saveGame(data);
    }
    return data;
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

async function apiCampaignRetreat() {
    return callAPI('POST', '/campaign_retreat', {});
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

// ── Pull-down to next month ───────────────────────────
let pullTouchStartY = 0;
let pullTouchStartX = 0;
let pullTouchMoved = false;
let isScrolledToBottom = true;

function initPullToRefresh() {
    const el = document.getElementById('narrative-area');
    if (!el) return;

    el.addEventListener('touchstart', (e) => {
        // Only activate when scrolled to bottom
        isScrolledToBottom = el.scrollHeight - el.scrollTop <= el.clientHeight + 60;
        pullTouchStartY = e.touches[0].clientY;
        pullTouchStartX = e.touches[0].clientX;
        pullTouchMoved = false;
    }, { passive: true });

    el.addEventListener('touchmove', (e) => {
        const dy = e.touches[0].clientY - pullTouchStartY;
        const dx = e.touches[0].clientX - pullTouchStartX;
        // Detect downward pull (dy > 20, |dx| < dy/2, scrolled to bottom)
        if (dy > 20 && Math.abs(dx) < dy / 2) {
            pullTouchMoved = true;
        }
    }, { passive: true });

    el.addEventListener('touchend', () => {
        if (pullTouchMoved && isScrolledToBottom) {
            // Show a brief "pulling..." indicator
            showPullHint('↓ 下月推进中...');
            setTimeout(() => hidePullHint(), 800);
            doTick();
        }
        pullTouchMoved = false;
    }, { passive: true });

    // Update scroll position tracking
    el.addEventListener('scroll', () => {
        isScrolledToBottom = el.scrollHeight - el.scrollTop <= el.clientHeight + 60;
    }, { passive: true });
}

function showPullHint(text) {
    let el = document.getElementById('pull-hint');
    if (!el) {
        el = document.createElement('div');
        el.id = 'pull-hint';
        el.style.cssText = 'position:fixed;top:0;left:0;right:0;padding:8px;text-align:center;background:rgba(212,160,23,0.9);color:#1a0800;font-size:13px;font-weight:bold;z-index:9999;transform:translateY(-100%);transition:transform 0.2s;font-family:"Noto Serif SC",serif';
        document.body.appendChild(el);
    }
    el.textContent = text;
    el.style.transform = 'translateY(0)';
}

function hidePullHint() {
    const el = document.getElementById('pull-hint');
    if (el) el.style.transform = 'translateY(-100%)';
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
    const wu = stats['武'] || 0;
    const zhi = stats['智'] || 0;
    const ming = stats['名'] || 0;
    const mei = stats['魅'] || 0;
    const yun = stats['运'] || 0;
    document.getElementById('stat-wu').textContent = wu;
    document.getElementById('stat-zhi').textContent = zhi;
    document.getElementById('stat-ming').textContent = ming;
    document.getElementById('stat-mei').textContent = mei;
    document.getElementById('stat-yun').textContent = yun;
    // Update color bars (max display width = 200 for full bar)
    const maxStat = 100;
    document.getElementById('attr-fill-wu').style.width = Math.min(100, wu) + '%';
    document.getElementById('attr-fill-zhi').style.width = Math.min(100, zhi) + '%';
    document.getElementById('attr-fill-ming').style.width = Math.min(100, ming) + '%';
    document.getElementById('attr-fill-mei').style.width = Math.min(100, mei) + '%';
    document.getElementById('attr-fill-yun').style.width = Math.min(100, yun) + '%';
}

function applyState(state) {
    currentState = state;
    updateStats(state);
    renderRunStats(state);
    renderActionPanel(state);
    renderEquipmentPanel(state);
    if (state.narrative) addNarrative(state.narrative);
    if (state.pending_achievements && state.pending_achievements.length > 0) {
        state.pending_achievements.forEach(msg => showAchievementToast(msg));
    }
    if (state.pending_rank_up) {
        showRankUpToast(state.pending_rank_up);
    }
    if (state.pending_monthly_report) {
        showMonthlyReport(state.pending_monthly_report);
    }
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
    else if (ui === 'intel') renderIntel(state, panel);
    else if (ui === 'death_shop') renderDeathShop(state, panel);
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
    const retreatBtn = document.createElement('button');
    retreatBtn.className = 'action-btn danger';
    retreatBtn.style.cssText = 'margin-left:8px;font-size:12px;padding:2px 8px';
    retreatBtn.textContent = '🚶 撤退';
    retreatBtn.onclick = doCampaignRetreat;
    div.appendChild(retreatBtn);
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
    let powerHtml = '';
    if (cd.power) {
        const wr = cd.power.win_rate;
        const wrColor = wr >= 60 ? '#88cc88' : wr >= 45 ? '#cccc44' : '#cc6666';
        const wrLabel = wr >= 60 ? '优势' : wr >= 45 ? '均势' : '劣势';
        powerHtml = `<div class="combat-power">
            <div class="power-row">
                <span class="power-label">我军战力</span>
                <span class="power-bar-wrap"><span class="power-bar player" style="width:${Math.min(100, wr)}%"></span></span>
                <span class="power-value">${cd.power.player}</span>
            </div>
            <div class="power-row">
                <span class="power-label">敌军战力</span>
                <span class="power-bar-wrap"><span class="power-bar enemy" style="width:${Math.min(100, 100-wr+50)}%"></span></span>
                <span class="power-value">${cd.power.enemy}</span>
            </div>
            <div class="win-rate-row">
                <span>胜率</span>
                <span class="win-rate-val" style="color:${wrColor}">${wr}%</span>
                <span class="wr-tag" style="color:${wrColor}">【${wrLabel}】</span>
                <span class="power-terrain">地形：${cd.power.terrain}</span>
            </div>
        </div>`;
    }
    panel.innerHTML = `
        <div class="combat-enemy">
            <div class="enemy-name">⚔️ ${cd.enemy.name}</div>
            <div class="enemy-stats">敌军：${cd.enemy.troops}人 | 地形：${cd.enemy.terrain}</div>
            <div class="enemy-stats">我军：${cd.player_army}人 | 士气：${cd.player_morale}</div>
        </div>
        ${powerHtml}
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
            <div class="npc-portrait">${nd.icon || "🎭"}</div>
            <div class="npc-meta">
                <div class="npc-name-lg">${nd.name}</div>
                <div class="npc-rank-lg">${nd.rank}</div>
                <div class="rel-tag">${nd.relation_tag} 好感度：${nd.relation}</div>
            </div>
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

function renderIntel(state, panel) {
    const intel = state.pending_intel;
    if (!intel) { renderNormal(state, panel); return; }
    let html = `<div class="intel-header">📰 江湖消息（花费${intel.cost}金）</div>`;
    html += '<div class="intel-list">';
    intel.npcs.forEach(npc => {
        const cls = npc.is_here ? 'intel-npc here' : (npc.is_leader ? 'intel-npc leader' : 'intel-npc');
        html += `<div class="${cls}">
            <span class="intel-icon">${npc.icon}</span>
            <span class="intel-name">${npc.name}</span>
            <span class="intel-loc">${npc.location_hint}</span>
            ${npc.is_leader ? '<span class="intel-tag">阵营领袖</span>' : ''}
            ${npc.is_recruited ? '<span class="intel-tag recruited">✅已招募</span>' : ''}
        </div>`;
    });
    html += '</div>';
    html += `<div class="intel-footer">💰 剩余金钱：${intel.gold_left}</div>`;
    html += '<div class="action-row" style="margin-top:8px"><button class="action-btn" onclick="renderActionPanel(currentState)">← 返回</button></div>';
    panel.innerHTML = html;
}

function renderTavernChoice(state, panel) {
    const npcs = state.tavern_npcs || [];
    if (npcs.length === 0) {
        panel.innerHTML = '<div style="text-align:center;color:#888;padding:20px">酒馆里无人</div>';
        return;
    }
    let html = '<div class="tavern-header">🍶 酒馆中数人聚坐，点击其中一人开始交谈</div>';
    html += '<div class="tavern-npc-list">';
    npcs.forEach(npc => {
        const typeIcon = npc.npc_type === '文官' ? '📚' : '⚔️';
        html += `<button class="tavern-npc-btn" onclick="doTavernChoice('${npc.id}')">
            <span class="tavern-npc-icon">${typeIcon}</span>
            <span class="tavern-npc-name">${npc.name}</span>
            <span class="tavern-npc-rank">${npc.rank}</span>
        </button>`;
    });
    html += '</div>';
    html += '<div class="action-row" style="margin-top:8px"><button class="action-btn" onclick="doTavernCancel()">← 离开酒馆</button></div>';
    panel.innerHTML = html;
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

function renderDeathShop(state, panel) {
    const shop = state.pending_death_shop;
    if (!shop) { renderNormal(state, panel); return; }
    const summary = shop.death_summary;
    const years = Math.floor(summary.months / 12);
    const months = summary.months % 12;
    panel.innerHTML = `
        <div class="death-shop-header">
            <div class="death-title">💀 陨于乱世</div>
            <div class="death-summary">
                存活：<b>${years}年${months}月</b> | 战斗：<b>${summary.battles}次</b> | 招募：<b>${summary.npcs_recruited}人</b><br>
                最高官职：<b>${summary.highest_rank}</b> | 获得经验：<b>${summary.exp_earned}</b>
            </div>
        </div>
        <div class="death-fragments">
            🎁 本局获得传承碎片：<b style="color:#d4a017">+${shop.fragments_earned}枚</b><br>
            💎 当前碎片余额：<b style="color:#d4a017">${shop.fragments_balance}枚</b>
        </div>
        <div class="death-section-title">⚔️ 传承主动技能</div>
        <div class="death-skills">
            ${shop.active_skills.map(sk => `
                <div class="death-skill ${sk.can_learn ? 'available' : 'locked'}">
                    <div class="death-skill-header">
                        <span class="death-skill-name">${sk.name}</span>
                        <span class="death-skill-cost">💠${sk.cost}碎片</span>
                    </div>
                    <div class="death-skill-desc">${sk.desc}</div>
                    ${sk.can_learn
                        ? `<button class="death-buy-btn" onclick="doBuySkill('${sk.id}')">购买</button>`
                        : `<div class="death-skill-locked">${sk.fail_reason || '暂不可学习'}</div>`
                    }
                </div>`).join('')}
        </div>
        <div class="death-section-title">🛡️ 传承被动技能</div>
        <div class="death-skills">
            ${shop.passive_skills.map(sk => `
                <div class="death-skill ${sk.can_learn ? 'available' : 'locked'}">
                    <div class="death-skill-header">
                        <span class="death-skill-name">${sk.name}</span>
                        <span class="death-skill-cost">💠${sk.cost}碎片</span>
                    </div>
                    <div class="death-skill-desc">${sk.desc}</div>
                    ${sk.can_learn
                        ? `<button class="death-buy-btn" onclick="doBuySkill('${sk.id}')">购买</button>`
                        : `<div class="death-skill-locked">${sk.fail_reason || '暂不可学习'}</div>`
                    }
                </div>`).join('')}
        </div>
        <div class="action-row" style="margin-top:14px">
            <button class="action-btn primary" onclick="doReincarnate()">🌟 转世重来</button>
        </div>
    `;
}

async function doBuySkill(skillId) {
    const state = await apiBuySkill(skillId);
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

async function doReincarnate() {
    showConfirmSheet(
        '🌟 确认转世',
        '转世将重新开始游戏，当前属性和进度将重置。确定要转世重来吗？',
        async () => {
            const state = await apiReincarnate();
            if (!state || state.game_status === 'error') return;
            clearNarrative();
            applyState(state);
        },
        '确认转世',
        true
    );
}

function renderNormal(state, panel) {
    const moves = state.available_moves || [];
    let html = '<div class="action-row city-actions">';
    html += `<button class="action-btn market-btn" onclick="doMarketAuto()">🏪 市集<div class="btn-sub">买卖粮草</div></button>`;
    html += `<button class="action-btn tavern-btn" onclick="doVisitTavern()">🍶 酒馆<div class="btn-sub">拜访/打听</div></button>`;
    html += `<button class="action-btn intel-btn" onclick="doIntelAuto()">📰 情报<div class="btn-sub">20金打听NPC</div></button>`;
    html += `<button class="action-btn map-btn" onclick="doShowMap()">🗺️ 地图<div class="btn-sub">查看地图</div></button>`;
    html += `<button class="action-btn history-btn" onclick="doShowHistory()">📜 战报<div class="btn-sub">历史记录</div></button>`;
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

// ── History / Run Record Panel ───────────────────
function doShowHistory() {
    const rs = state.run_history || {};
    const records = rs.records || [];
    const total = rs.total_runs || 0;
    const review = currentState.pending_death_review || {};
    const battles = review.battles || [];
    const events = review.events || [];

    const overlay = document.createElement('div');
    overlay.id = 'history-overlay';
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.85);z-index:900;display:flex;align-items:center;justify-content:center;padding:16px;';
    overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };

    let battlesHtml = '<div style="text-align:center;color:#556;font-size:13px;padding:10px">尚无战斗记录</div>';
    if (battles.length > 0) {
        battlesHtml = battles.slice().reverse().map(b => {
            const r = b.result === 'win' ? '胜' : '负';
            const loot = b.result === 'win' ? `+${b.exp_gain}经验 +${b.gold}金 +${b.food}粮` : '';
            return `<div class="history-item ${b.result}"><span class="battle-time">${b.year}年${b.month}月</span><span style="font-weight:bold;color:${b.result==='win'?'#2ecc71':'#e74c3c'}">${r}</span><span style="flex:1;text-align:center">${b.enemy}</span>${loot ? `<span style="font-size:12px;color:#8a6a14">${loot}</span>` : ''}</div>`;
        }).join('');
    }

    let eventsHtml = '<div style="text-align:center;color:#556;font-size:13px;padding:10px">尚无历史事件</div>';
    if (events.length > 0) {
        eventsHtml = events.slice().reverse().map(ev => {
            return `<div class="history-item"><span class="battle-time">${ev.year}年${ev.month}月</span><span style="color:#d4a017">★</span><span style="flex:1;text-align:center;color:#c8d8f0">${ev.name}</span><span style="font-size:11px;color:#556">${ev.type === 'mandatory' ? '必然' : '条件'}</span></div>`;
        }).join('');
    }

    let recordsHtml = '<div style="text-align:center;color:#556;font-size:13px;padding:10px">尚无历史记录</div>';
    if (records.length > 0) {
        recordsHtml = records.map(r => `<div class="history-item death"><div style="display:flex;gap:8px;align-items:center"><span style="color:#d4a017">⚰</span><span>${r.year||'?'}年${r.month||'?'}月</span><span>${r.player_name||'???'}</span><span style="color:#8a6a14">${r.player_rank||'散兵'}</span></div><div style="font-size:12px;color:#888">${r.death_cause||'陨落'} | 经验 ${r.exp||0}</div></div>`).join('');
    }

    overlay.innerHTML = `
        <div style="background:#1a1a2e;color:#eee;border-radius:16px;padding:20px;max-width:420px;width:100%;max-height:85vh;overflow-y:auto;font-family:'Noto Serif SC',serif;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
                <span style="font-size:18px;font-weight:700">📜 本局战报</span>
                <span style="font-size:12px;color:#888">共${total}局</span>
            </div>
            <div class="history-section">
                <div class="history-section-title">⚔️ 战斗记录</div>
                ${battlesHtml}
            </div>
            <div class="history-section">
                <div class="history-section-title">★ 历史事件</div>
                ${eventsHtml}
            </div>
            ${records.length > 0 ? `<div class="history-section"><div class="history-section-title">📖 往局回顾</div>${recordsHtml}</div>` : ''}
            <button onclick="this.closest('#history-overlay').remove()" style="width:100%;margin-top:14px;padding:10px;background:#333;color:#aaa;border:none;border-radius:8px;cursor:pointer;font-size:14px">关闭</button>
        </div>
    `;
    document.body.appendChild(overlay);
}

// ── Map View ────────────────────────────────────
function renderMapView(state, panel) {
    const map = state.map;
    const cf = state.city_favorability || {};
    const current = map.current;
    const connections = map.connections || {};
    const adjacent = map.adjacent_cities || [];

    function getFavColor(city) {
        const fav = cf[city] || 50;
        if (fav >= 90) return '#88cc88';
        if (fav >= 70) return '#2e8b57';
        if (fav <= 30) return '#cc4444';
        return '#9a7620';
    }

    // Build local neighborhood: current + its neighbors + their neighbors (depth-2)
    const depth1 = new Set([current]);
    adjacent.forEach(c => depth1.add(c));
    const depth2 = new Set();
    adjacent.forEach(c => {
        (connections[c] || []).forEach(n => {
            if (!depth1.has(n)) depth2.add(n);
        });
    });
    const visibleCities = [...depth1, ...depth2];

    // Compute simple grid positions (row/col) for each visible city
    // Use a compact grid layout based on connectivity graph
    const pos = {};
    const visited = new Set();
    const queue = [current];
    pos[current] = { col: 1, row: 1 };
    visited.add(current);
    let maxCol = 1, maxRow = 1;

    // BFS to assign positions
    const step = 2;
    const breadth = {};
    const d1Queue = [{ city: current, dist: 0 }];
    for (const c of adjacent) breadth[c] = 1;
    for (const c of depth2) {
        const adjOfAdj = connections[c] || [];
        const d1Neighbor = adjOfAdj.find(n => depth1.has(n));
        if (d1Neighbor && breadth[d1Neighbor] !== undefined) {
            breadth[c] = breadth[d1Neighbor] + 0.5;
        } else {
            breadth[c] = 1;
        }
    }

    // Assign cols based on breadth, rows compactly
    const breadthBuckets = {};
    [...depth1].forEach(c => {
        const b = breadth[c] || 0;
        if (!breadthBuckets[b]) breadthBuckets[b] = [];
        breadthBuckets[b].push(c);
    });
    [...depth2].forEach(c => {
        const b = breadth[c] || 0;
        if (!breadthBuckets[b]) breadthBuckets[b] = [];
        breadthBuckets[b].push(c);
    });

    const sortedBreadths = Object.keys(breadthBuckets).sort((a, b) => a - b);
    sortedBreadths.forEach((b, bi) => {
        const cities = breadthBuckets[b];
        cities.forEach((city, ci) => {
            pos[city] = { col: (bi * 2), row: ci };
            maxCol = Math.max(maxCol, bi * 2);
            maxRow = Math.max(maxRow, ci);
        });
    });

    // SVG node radius and spacing
    const NODE_R = 22;
    const COL_STEP = 72;
    const ROW_STEP = 64;
    const PAD = 24;
    const svgW = (maxCol + 2) * COL_STEP + PAD * 2;
    const svgH = (maxRow + 1) * ROW_STEP + PAD * 2 + 20;

    // Build SVG lines
    let svgLines = '';
    visibleCities.forEach(city => {
        (connections[city] || []).forEach(n => {
            if (pos[city] && pos[n] && visibleCities.includes(n)) {
                const x1 = PAD + pos[city].col * COL_STEP;
                const y1 = PAD + pos[city].row * ROW_STEP + 10;
                const x2 = PAD + pos[n].col * COL_STEP;
                const y2 = PAD + pos[n].row * ROW_STEP + 10;
                const isActive = (city === current || n === current) ? '1' : '0.25';
                const color = (city === current || n === current) ? '#d4a017' : '#4a3520';
                svgLines += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="1.5" opacity="${isActive}" />`;
            }
        });
    });

    // Build SVG city nodes
    let svgNodes = '';
    visibleCities.forEach(city => {
        const p = pos[city] || { col: 1, row: 1 };
        const cx = PAD + p.col * COL_STEP;
        const cy = PAD + p.row * ROW_STEP + 10;
        const isCurrent = city === current;
        const isAdj = adjacent.includes(city);
        const isDim = depth2.has(city);
        const fill = isCurrent ? '#d4a017' : (isAdj ? '#1a2a1a' : '#111111');
        const stroke = isCurrent ? '#fff' : (isAdj ? '#d4a017' : '#4a3520');
        const opacity = isDim ? '0.55' : '1';
        svgNodes += `<g opacity="${opacity}" style="${isAdj && !isDim ? 'cursor:pointer' : ''}" ${isAdj && !isDim ? `onclick="doMove('${city}')"` : ''}>`;
        svgNodes += `<circle cx="${cx}" cy="${cy}" r="${NODE_R}" fill="${fill}" stroke="${stroke}" stroke-width="${isCurrent ? 2.5 : 1.5}" />`;
        const icon = isCurrent ? '★' : (isAdj ? '●' : '·');
        const iconColor = isCurrent ? '#1a1208' : (isAdj ? '#d4a017' : '#6a5a3a');
        svgNodes += `<text x="${cx}" y="${cy + 5}" text-anchor="middle" font-size="13" fill="${iconColor}">${icon}</text>`;
        svgNodes += `<text x="${cx}" y="${cy + NODE_R + 14}" text-anchor="middle" font-size="11" fill="#e8d5a3">${city}</text>`;
        // Favorite bar
        const fav = cf[city] || 50;
        const favW = 24 * fav / 100;
        const favColor = getFavColor(city);
        svgNodes += `<rect x="${cx - 12}" y="${cy + NODE_R + 2}" width="${favW}" height="3" rx="1.5" fill="${favColor}" />`;
        svgNodes += '</g>';
    });

    let html = '';
    // SVG Map
    html += `<div style="overflow-x:auto;overflow-y:hidden;padding:8px 0">
        <svg width="${svgW + 20}" height="${svgH + 20}" style="display:block;margin:0 auto;max-width:100%">
            ${svgLines}
            ${svgNodes}
        </svg>
    </div>`;

    // Adjacent city quick-move buttons (touch-friendly large buttons)
    if (adjacent.length > 0) {
        html += '<div style="padding:8px 4px 4px;font-size:11px;color:#9a7620;margin-bottom:4px">点击相邻城市快速移动</div>';
        html += '<div style="display:flex;flex-wrap:wrap;gap:6px;padding:0 4px;">';
        adjacent.forEach(city => {
            const fav = cf[city] || 50;
            const favColor = getFavColor(city);
            const travelCost = 1; // simplified
            html += `<button class="map-move-btn" onclick="doMove('${city}')">
                <span style="font-size:15px">→</span>
                <span style="font-weight:700">${city}</span>
                <span style="font-size:10px;color:${favColor};margin-left:4px">❤${fav}</span>
            </button>`;
        });
        html += '</div>';
    }

    // Region overview toggle (shows all cities in compact grid)
    html += `<div style="margin-top:12px;border-top:1px solid #2a1a08;padding-top:8px">
        <button class="action-btn" onclick="renderFullMap(state, panel)" style="width:100%">📍 全州一览（${Object.keys(map.regions).length}州${Object.values(map.regions).reduce((s,r)=>s+r.cities.length,0)}城）</button>
    </div>`;

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

// ── Full map (all regions, compact grid) ──────────────
function renderFullMap(state, panel) {
    const map = state.map;
    const cf = state.city_favorability || {};
    const current = map.current;
    const connections = map.connections || {};
    const adjacent = map.adjacent_cities || [];

    function getFavColor(city) {
        const fav = cf[city] || 50;
        if (fav >= 90) return '#88cc88';
        if (fav >= 70) return '#2e8b57';
        if (fav <= 30) return '#cc4444';
        return '#9a7620';
    }

    let html = '<div style="padding:4px;font-size:12px;color:#9a7620;margin-bottom:8px">📍 全州地图 · 点击相邻城市移动</div>';
    html += '<div class="map-full-grid">';
    Object.entries(map.regions).forEach(([regKey, regData]) => {
        const isCurrentRegion = regData.cities.includes(current);
        const regionCls = isCurrentRegion ? 'map-region current-region' : 'map-region';
        html += `<div class="${regionCls}">`;
        html += `<div class="map-region-title">${regData.name}</div>`;
        html += '<div class="region-cities">';
        regData.cities.forEach(city => {
            const isAdj = adjacent.includes(city);
            const isCurr = city === current;
            const fav = cf[city] || 50;
            const favColor = getFavColor(city);
            const cls = isCurr ? 'map-city-btn current' : (isAdj ? 'map-city-btn adjacent' : 'map-city-btn other-city');
            const icon = isCurr ? '★' : (isAdj ? '→' : '·');
            if (isAdj) {
                html += `<button class="${cls}" onclick="doMove('${city}')">${icon} ${city} <span style="font-size:9px;color:${favColor}">❤${fav}</span></button>`;
            } else {
                html += `<button class="${cls}" disabled>${icon} ${city}</button>`;
            }
        });
        html += '</div></div>';
    });
    html += '</div>';
    html += '<div style="margin-top:12px"><button class="action-btn" onclick="renderMapView(state, panel)" style="width:100%">← 返回局部图</button></div>';
    panel.innerHTML = html;
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
    applyState(state);
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

async function apiBuySkill(skillId) {
    return callAPI('POST', '/buy_skill', { skill_id: skillId });
}

async function apiReincarnate() {
    return callAPI('POST', '/reincarnate');
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

async function doCampaignRetreat() {
    showConfirmSheet(
        '⚠️ 确认撤退',
        '撤退将损失名望-20，且无法获得战役奖励。确定要撤退吗？',
        async () => {
            const state = await apiCampaignRetreat();
            if (!state || state.game_status === 'error') return;
            applyState(state);
        },
        '确认撤退',
        true
    );
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
    showConfirmSheet(
        '🗑️ 确认丢弃',
        '丢弃装备后无法恢复，确定要丢弃吗？',
        async () => {
            const state = await apiEquipment('drop', null);
            if (!state || state.game_status === 'error') return;
            applyState(state);
        },
        '确认丢弃',
        true
    );
}

async function doUnequipSlot(slotIndex) {
    const state = await apiEquipment('drop', slotIndex);
    if (!state || state.game_status === 'error') return;
    applyState(state);
}

function showAchievementToast(msg) {
    const existing = document.getElementById('ach-toast');
    if (existing) existing.remove();
    const toast = document.createElement('div');
    toast.id = 'ach-toast';
    toast.className = 'ach-toast';
    toast.innerHTML = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('visible'), 50);
    setTimeout(() => {
        toast.classList.remove('visible');
        setTimeout(() => toast.remove(), 400);
    }, 3500);
}

function showRankUpToast(data) {
    const { old_rank, new_rank } = data;
    const existing = document.getElementById('rankup-toast');
    if (existing) existing.remove();
    const toast = document.createElement('div');
    toast.id = 'rankup-toast';
    toast.className = 'rankup-toast';
    toast.innerHTML = `
        <div class="rankup-title">🎖️ 晋升！</div>
        <div class="rankup-ranks">${old_rank} → <span class="rankup-new">${new_rank}</span></div>
        <div class="rankup-desc">前途光明，继续努力！</div>
        <button class="action-btn primary" onclick="dismissRankUp()">确定</button>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('visible'), 50);
}


async function dismissRankUp() {
    const existing = document.getElementById('rankup-toast');
    if (existing) existing.remove();
    await callAPI('POST', '/rank_up_dismiss', {});
}

function showMonthlyReport(data) {
    const el = document.getElementById('monthly-report');
    if (el) el.remove();
    const div = document.createElement('div');
    div.id = 'monthly-report';
    div.className = 'monthly-report';
    const campNote = data.campaign_active ? '<div style="color:#e74c3c;font-size:12px;margin-top:4px">⚔️ 战役期间粮草消耗翻倍</div>' : '';
    div.innerHTML = `
        <div class="mr-title">📋 本月收支</div>
        <div class="mr-row"><span>粮草消耗</span><span style="color:#e74c3c">-${data.food_cost}粮</span></div>
        <div class="mr-row"><span>基础消耗</span><span>-3 粮</span></div>
        ${data.campaign_active ? '<div class="mr-row" style="color:#e74c3c"><span>战役消耗</span><span>+3 粮</span></div>' : ''}
        <div class="mr-row"><span>金俸禄</span><span style="color:#2ecc71">+${data.salary}金</span></div>
        <div class="mr-row"><span>日常消耗</span><span>-1 金</span></div>
        <div class="mr-row mr-net">
            <span>净收益</span>
            <span style="color:${data.gold_after >= data.gold_before ? '#2ecc71' : '#e74c3c'}">
                金${data.gold_after - data.gold_before >= 0 ? '+' : ''}${data.gold_after - data.gold_before} / 粮${data.food_after - data.food_before >= 0 ? '+' : ''}${data.food_after - data.food_before}
            </span>
        </div>
        <button class="action-btn primary" onclick="dismissMonthlyReport()" style="margin-top:10px">确定</button>
    `;
    document.body.appendChild(div);
    setTimeout(() => div.classList.add('visible'), 50);
}

async function dismissMonthlyReport() {
    const existing = document.getElementById('monthly-report');
    if (existing) existing.remove();
    await callAPI('POST', '/monthly_report_dismiss', {});
}
// ── Bottom Sheet helpers ─────────────────────────────
function openBottomSheet(id) {
    const sheet = document.getElementById(id);
    if (!sheet) return;
    sheet.classList.add('active');
    sheet.onclick = (e) => { if (e.target === sheet) closeBottomSheet(id); };
}

function closeBottomSheet(id) {
    const sheet = document.getElementById(id);
    if (sheet) sheet.classList.remove('active');
}

// ── Reusable confirmation bottom sheet ─────────────────
function showConfirmSheet(title, message, onConfirm, confirmLabel = '确认', danger = false) {
    const existing = document.getElementById('confirm-sheet');
    if (existing) existing.remove();
    const div = document.createElement('div');
    div.id = 'confirm-sheet';
    div.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.6);z-index:9998;display:flex;align-items:flex-end;justify-content:center;padding:16px;';
    div.innerHTML = `
        <div style="background:#1a1208;border:1px solid ${danger?'#8b0000':'#8b6914'};border-radius:16px 16px 0 0;padding:20px;width:100%;max-width:480px;font-family:'Noto Serif SC',serif;">
            <div style="font-size:18px;font-weight:bold;color:#d4a017;text-align:center;margin-bottom:8px">${title}</div>
            <div style="font-size:14px;color:#8a7a5a;text-align:center;margin-bottom:16px;line-height:1.6">${message}</div>
            <div style="display:flex;gap:8px">
                <button id="sheet-cancel-btn" class="action-btn" style="flex:1;min-height:52px">取消</button>
                <button id="sheet-ok-btn" class="action-btn ${danger?'danger':'primary'}" style="flex:1;min-height:52px">${confirmLabel}</button>
            </div>
        </div>
    `;
    document.body.appendChild(div);
    div.querySelector('#sheet-cancel-btn').onclick = () => div.remove();
    div.querySelector('#sheet-ok-btn').onclick = () => { div.remove(); onConfirm(); };
    div.onclick = (e) => { if (e.target === div) div.remove(); };
}

function doShowAchievements() {
    callAPI('GET', '/achievements').then(data => {
        renderAchievementsPanel(data);
        openBottomSheet('achievements-sheet');
    });
}

function renderAchievementsPanel(data) {
    const list = document.getElementById('ach-list');
    const summary = document.getElementById('ach-summary');
    if (!list || !data) return;
    if (summary) summary.textContent = `已解锁：${data.unlocked} / ${data.total}`;
    list.innerHTML = '';
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

function doShowHistory() {
    const content = document.getElementById('history-content');
    if (!content) return;
    const rs = currentState && currentState.run_history ? currentState.run_history : {};
    const records = rs.records || [];
    const total = rs.total_runs || 0;
    const review = currentState && currentState.pending_death_review ? currentState.pending_death_review : {};
    const battles = review.battles || [];
    const events = review.events || [];

    let battlesHtml = '<div style="text-align:center;color:#556;font-size:13px;padding:10px">尚无战斗记录</div>';
    if (battles.length > 0) {
        battlesHtml = battles.slice().reverse().map(b => {
            const r = b.result === 'win' ? '胜' : '负';
            const loot = b.result === 'win' ? `+${b.exp_gain}经验 +${b.gold}金 +${b.food}粮` : '';
            return `<div class="history-item ${b.result}"><span class="battle-time">${b.year}年${b.month}月</span><span style="font-weight:bold;color:${b.result==='win'?'#2ecc71':'#e74c3c'}">${r}</span><span style="flex:1;text-align:center">${b.enemy}</span>${loot ? `<span style="font-size:12px;color:#8a6a14">${loot}</span>` : ''}</div>`;
        }).join('');
    }
    let eventsHtml = '<div style="text-align:center;color:#556;font-size:13px;padding:10px">尚无历史事件</div>';
    if (events.length > 0) {
        eventsHtml = events.slice().reverse().map(ev => {
            return `<div class="history-item"><span class="battle-time">${ev.year}年${ev.month}月</span><span style="color:#d4a017">★</span><span style="flex:1;text-align:center;color:#c8d8f0">${ev.name}</span></div>`;
        }).join('');
    }
    let recordsHtml = '<div style="text-align:center;color:#556;font-size:13px;padding:10px">尚无历史记录</div>';
    if (records.length > 0) {
        recordsHtml = records.map(r => `<div class="history-item death"><div style="display:flex;gap:8px;align-items:center"><span style="color:#d4a017">⚰</span><span>${r.year||'?'}年${r.month||'?'}月</span><span>${r.player_name||'???'}</span><span style="color:#8a6a14">${r.player_rank||'散兵'}</span></div><div style="font-size:12px;color:#888">${r.death_cause||'陨落'} | 经验 ${r.exp||0}</div></div>`).join('');
    }

    content.innerHTML = `
        <div style="font-size:12px;color:#888;text-align:center;margin-bottom:12px">共${total}局</div>
        <div class="history-section">
            <div class="history-section-title">⚔️ 战斗记录</div>
            ${battlesHtml}
        </div>
        <div class="history-section">
            <div class="history-section-title">★ 历史事件</div>
            ${eventsHtml}
        </div>
        ${records.length > 0 ? `<div class="history-section"><div class="history-section-title">📖 往局回顾</div>${recordsHtml}</div>` : ''}
    `;
    openBottomSheet('history-sheet');
}

document.addEventListener('DOMContentLoaded', () => {
    initPullToRefresh();
    const closeAch = document.getElementById('close-ach-sheet');
    if (closeAch) closeAch.onclick = () => closeBottomSheet('achievements-sheet');
    const closeHist = document.getElementById('close-history-sheet');
    if (closeHist) closeHist.onclick = () => closeBottomSheet('history-sheet');
});

// ── Init ─────────────────────────────────────────────
document.getElementById('btn-new-game').addEventListener('click', () => {
    clearSavedGame();
    newGame();
});

function tryResumeGame(savedState) {
    if (!savedState) return false;
    currentState = savedState;
    showScreen('game-screen');
    updateStats(savedState);
    if (savedState.narrative) addNarrative(savedState.narrative);
    renderActionPanel(savedState);
    renderEquipmentPanel(savedState);
    return true;
}

const saved = loadSavedGame();
if (saved && saved.game_status === 'playing') {
    tryResumeGame(saved);
} else {
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
}

const seed = JSON.parse(document.getElementById('initial-roster').textContent);
const statKeys = ['fgm','fga','ftm','fta','threes','pts','reb','ast','stl','blk','tov'];
const statLabels = ['FGM','FGA','FTM','FTA','3PM','PTS','REB','AST','STL','BLK','TO'];
const slots = ['PG','SG','G','SF','PF','F','C','UTIL1','UTIL2'];
const storageKey = 'fivecat-state-v1';
let saved = {};
try { saved = JSON.parse(localStorage.getItem(storageKey) || '{}'); } catch (_) {}
let roster = Array.isArray(saved.roster) ? saved.roster : structuredClone(seed);
let gameOverrides = saved.gameOverrides || {};
let mine = saved.mine || {};
let opponent = saved.opponent || {};
let useMatchup = !!saved.useMatchup;
let playingTeams = [];
let scheduleAvailable = false;
let lastPlan = null;
let refreshTimer;

const $ = id => document.getElementById(id);
const today = new Date();
const localDate = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
$('day').value = localDate;
$('use-matchup').checked = useMatchup;

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function save() {
  localStorage.setItem(storageKey, JSON.stringify({roster, gameOverrides, mine, opponent, useMatchup}));
}
function currentOverrides() { return gameOverrides[$('day').value] || {}; }
function isPlaying(player) {
  const override = currentOverrides()[player.id];
  return override === undefined ? (scheduleAvailable && playingTeams.includes(player.team)) : override;
}
function setPlaying(player, value) {
  const day = $('day').value;
  gameOverrides[day] = gameOverrides[day] || {};
  gameOverrides[day][player.id] = value;
  save(); renderRoster(); schedulePlan();
}
function renderRoster() {
  const active = new Set(lastPlan?.active_ids || []);
  $('roster').innerHTML = roster.map((p, i) => `<div class="roster-row ${active.has(p.id) ? 'active' : ''}" data-index="${i}">
    <div><div class="player-name">${escapeHtml(p.name)}</div><div class="player-meta">${p.source === 'NBA' ? 'NBA avg' : 'Screenshot avg'} · ${escapeHtml(p.team || 'TEAM?')}</div></div>
    <label>TEAM<input class="team" type="text" maxlength="3" value="${escapeHtml(p.team || '')}" aria-label="${escapeHtml(p.name)} NBA team"></label>
    <label>YAHOO POS<input class="positions" type="text" value="${escapeHtml((p.positions || []).join(','))}" aria-label="${escapeHtml(p.name)} Yahoo positions"></label>
    <label>AVAILABLE<input class="available" type="checkbox" ${p.available ? 'checked' : ''} aria-label="${escapeHtml(p.name)} available"></label>
    <label>GAME<input class="playing" type="checkbox" ${isPlaying(p) ? 'checked' : ''} aria-label="${escapeHtml(p.name)} playing today"></label>
    <button class="remove" type="button" title="Remove from roster" aria-label="Remove ${escapeHtml(p.name)}">×</button>
  </div>`).join('');
  $('playing-count').textContent = roster.filter(p => p.available && isPlaying(p)).length;
}
function renderMatchupInputs() {
  $('matchup-inputs').innerHTML = statKeys.map((key, i) => `<div class="totals-row"><span>${statLabels[i]}</span>
    <input inputmode="decimal" type="number" min="0" step="any" data-side="mine" data-key="${key}" value="${mine[key] ?? ''}" aria-label="My ${statLabels[i]}">
    <input inputmode="decimal" type="number" min="0" step="any" data-side="opponent" data-key="${key}" value="${opponent[key] ?? ''}" aria-label="Opponent ${statLabels[i]}"></div>`).join('');
}
function renderPlan(result) {
  lastPlan = result;
  const byId = new Map(roster.map(p => [p.id, p]));
  $('lineup').innerHTML = slots.map(slot => {
    const player = byId.get(result?.slots?.[slot]);
    return `<div class="slot ${player ? '' : 'empty'}"><span class="slot-tag">${slot.replace('UTIL','UTL ')}</span><div><div class="slot-name">${player ? escapeHtml(player.name) : 'Open slot'}</div><div class="slot-detail">${player ? `${escapeHtml(player.team)} · ${Number(player.stats?.pts || 0).toFixed(1)} PTS · ${Number(player.stats?.reb || 0).toFixed(1)} REB` : 'No eligible player selected'}</div></div></div>`;
  }).join('');
  $('active-count').textContent = result?.active_ids?.length ?? 0;
  if (result?.categories) {
    $('win-count').textContent = `${result.matchup_wins}/9`;
    $('win-caption').textContent = result.matchup_wins >= 5 ? 'five-cat target met after today' : 'projected after today';
    $('category-outlook').innerHTML = result.categories.map(c => `<div class="cat ${c.result}"><div><span class="cat-name">${c.name}</span><span class="cat-result">${c.result}</span></div><div class="cat-numbers">${Number(c.mine).toFixed(c.name.includes('%') ? 3 : 1)} <small>vs</small> ${Number(c.opponent).toFixed(c.name.includes('%') ? 3 : 1)}</div></div>`).join('');
  } else {
    $('win-count').textContent = '—';
    $('win-caption').textContent = 'enter matchup totals';
    $('category-outlook').textContent = useMatchup ? 'Enter both teams’ current weekly totals to compare categories.' : 'Enter matchup totals to see projected category wins after today’s games.';
  }
  renderRoster();
}
async function optimize() {
  $('optimize').disabled = true;
  $('optimize').textContent = 'Optimizing…';
  try {
    const useTargets = useMatchup && Object.values(mine).some(v => v !== '') && Object.values(opponent).some(v => v !== '');
    const response = await fetch('/api/plan', {method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({players:roster.map(p => ({...p, playing:isPlaying(p)})), mine, opponent, use_matchup:useTargets})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Could not optimize lineup');
    renderPlan(data);
  } catch (error) {
    $('warning').textContent = error.message;
    $('warning').classList.remove('hidden');
  } finally {
    $('optimize').disabled = false;
    $('optimize').textContent = 'Optimize lineup →';
  }
}
function schedulePlan() { clearTimeout(refreshTimer); refreshTimer = setTimeout(optimize, 180); }
async function loadDay(refresh = false) {
  $('data-status').textContent = 'Loading NBA data…';
  try {
    const response = await fetch('/api/day', {method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({date:$('day').value, player_ids:roster.map(p => p.id), refresh:refresh === true})});
    let data;
    try { data = await response.json(); }
    catch (_) { throw new Error(`NBA service returned HTTP ${response.status}`); }
    if (!response.ok) throw new Error(data.error || 'NBA data request failed');
    scheduleAvailable = data.schedule_available;
    playingTeams = data.playing_teams;
    for (const player of roster) {
      const projection = data.players[player.id];
      if (projection) {
        player.stats = projection.stats;
        player.source = 'NBA';
        if (!player.teamEdited && projection.team && projection.team !== 'TOT') player.team = projection.team;
      }
    }
    save();
    $('data-status').textContent = data.stats_available
      ? (data.warnings.some(w => w.includes('player stats unavailable')) ? 'Using historical NBA averages' : 'NBA averages loaded')
      : 'Using screenshot averages';
    if (data.warnings.length) {
      $('warning').textContent = `${data.warnings.join(' ')} ${!scheduleAvailable ? 'Mark today’s games manually below.' : ''}`;
      $('warning').classList.remove('hidden');
    } else $('warning').classList.add('hidden');
    renderRoster(); await optimize();
  } catch (error) {
    $('data-status').textContent = 'NBA data unavailable';
    $('warning').textContent = `${error.message}. Mark today’s games manually below.`;
    $('warning').classList.remove('hidden');
    renderRoster(); await optimize();
  }
}

$('roster').addEventListener('change', event => {
  const row = event.target.closest('.roster-row');
  if (!row) return;
  const p = roster[Number(row.dataset.index)];
  if (event.target.classList.contains('team')) { p.team = event.target.value.trim().toUpperCase(); p.teamEdited = true; }
  if (event.target.classList.contains('positions')) {
    const positions = event.target.value.toUpperCase().split(',').map(s => s.trim()).filter(s => ['PG','SG','SF','PF','C'].includes(s));
    if (positions.length) p.positions = positions;
  }
  if (event.target.classList.contains('available')) p.available = event.target.checked;
  if (event.target.classList.contains('playing')) return setPlaying(p, event.target.checked);
  save(); renderRoster(); schedulePlan();
});
$('roster').addEventListener('click', event => {
  if (!event.target.classList.contains('remove')) return;
  roster.splice(Number(event.target.closest('.roster-row').dataset.index), 1);
  save(); renderRoster(); schedulePlan();
});
$('matchup-inputs').addEventListener('input', event => {
  if (!event.target.dataset.side) return;
  const target = event.target.dataset.side === 'mine' ? mine : opponent;
  target[event.target.dataset.key] = event.target.value;
  save(); schedulePlan();
});
$('use-matchup').addEventListener('change', event => { useMatchup = event.target.checked; save(); optimize(); });
$('day').addEventListener('change', () => loadDay());
$('refresh').addEventListener('click', () => loadDay(true));
$('optimize').addEventListener('click', optimize);
$('reset-roster').addEventListener('click', () => { if (confirm('Replace your saved roster with the screenshot roster?')) { roster = structuredClone(seed); save(); loadDay(); } });

let searchTimer;
$('search').addEventListener('input', () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(async () => {
    const query = $('search').value.trim();
    if (query.length < 3) { $('search-results').innerHTML = ''; return; }
    try {
      const results = await (await fetch(`/api/search?q=${encodeURIComponent(query)}`)).json();
      $('search-results').innerHTML = results.map(p => `<button type="button" data-id="${p.id}" data-name="${escapeHtml(p.name)}">${escapeHtml(p.name)}</button>`).join('') || '<span class="help">No players found.</span>';
    } catch (_) { $('search-results').textContent = 'Search unavailable'; }
  }, 220);
});
$('search-results').addEventListener('click', event => {
  const button = event.target.closest('button[data-id]');
  if (!button) return;
  const team = $('new-team').value.trim().toUpperCase();
  const positions = $('new-positions').value.toUpperCase().split(',').map(s => s.trim()).filter(s => ['PG','SG','SF','PF','C'].includes(s));
  if (!/^[A-Z]{3}$/.test(team) || !positions.length) { alert('Enter a three-letter NBA team code and at least one Yahoo position first.'); return; }
  const id = Number(button.dataset.id);
  if (roster.some(p => p.id === id)) { alert('That player is already on your roster.'); return; }
  if (roster.length >= 18) { alert('The MVP supports up to 18 players. Remove one first.'); return; }
  roster.push({id, name:button.dataset.name, team, teamEdited:true, positions, available:true,
    stats:Object.fromEntries(statKeys.map(key => [key,0])), source:'NBA'});
  $('search').value = ''; $('search-results').innerHTML = '';
  save(); renderRoster(); loadDay();
});

renderMatchupInputs();
renderRoster();
loadDay();

"use strict";

/* My team: the fantasy roster on a court. Edits here are a plan; make the
   same moves in the official app, then save so the site knows the real team.
   Loaded before app.js, so everything here is only called at runtime. */

const TEAM_FREE_TRANSFERS = 4;
const MULT = { captain: 2, starter: 1, sixth: 1, bench: 0.5 };

const teamState = {
  loaded: false,
  saved: null,
  draft: null,
  sel: null,
  swap: false,
  picker: null,
  pq: "",
  sugg: null,
  suggKey: "",
  suggBusy: false,
  horizon: 1,
  error: null,
  msg: "",
};

async function apiPost(path, body) {
  const res = await fetch(`/api/${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

/* ---------------------------------------------------------------- data */

function playerPool() {
  return new Map((state.picks?.players || []).map((r) => [`${r.key}|${r.team}`, r]));
}

function coachPool() {
  return new Map((state.picks?.coaches || []).map((c) => [`${c.key}|${c.team}`, c]));
}

async function loadTeam() {
  if (teamState.loading) return;
  teamState.loading = true;
  try {
    const d = await api("myteam");
    teamState.saved = d.team;
    const stored = store.get("wn.teamDraft", null);
    teamState.draft = stored && d.team && stored.base === d.team.saved_at ? stored.draft : draftFrom(d.team);
    teamState.error = null;
  } catch (e) {
    teamState.error = e.message;
  }
  teamState.loaded = true;
  teamState.loading = false;
  render();
  requestSuggestions();
}

function draftFrom(team) {
  if (!team) return null;
  return {
    players: [...team.players],
    coach: team.coach,
    lineup: team.lineup ? JSON.parse(JSON.stringify(team.lineup)) : null,
    unlimited: !!team.unlimited,
  };
}

const xfpOf = (pool, id) => pool.get(id)?.xfp ?? 0;
const priceOf = (pool, coaches, id) => pool.get(id)?.price ?? coaches.get(id)?.price ?? 0;

function autoLineup(players, pool) {
  const order = [...players].sort((a, b) => xfpOf(pool, b) - xfpOf(pool, a));
  return { captain: order[0], starters: order.slice(0, 5), sixth: order[5], bench: order.slice(6) };
}

function lineupValid(l, players) {
  if (!l || !Array.isArray(l.starters) || !Array.isArray(l.bench)) return false;
  const all = [...l.starters, l.sixth, ...l.bench];
  return all.length === 10 && players.every((p) => all.includes(p)) && l.starters.includes(l.captain);
}

function ensureLineup(draft, pool) {
  if (!lineupValid(draft.lineup, draft.players)) draft.lineup = autoLineup(draft.players, pool);
  return draft.lineup;
}

function roleOf(l, id) {
  if (l.captain === id) return "captain";
  if (l.starters.includes(id)) return "starter";
  if (l.sixth === id) return "sixth";
  return "bench";
}

function teamTotals(draft, pool, coaches) {
  const l = draft.lineup;
  const total = draft.players.reduce((s, id) => s + xfpOf(pool, id) * MULT[roleOf(l, id)], 0);
  const saved = teamState.saved;
  const budget = saved.players.reduce((s, id) => s + priceOf(pool, coaches, id), 0) + priceOf(pool, coaches, saved.coach) + (saved.bank || 0);
  const spent = draft.players.reduce((s, id) => s + priceOf(pool, coaches, id), 0) + priceOf(pool, coaches, draft.coach);
  const rs = saved.round_start || saved;
  const used = draft.players.filter((id) => !rs.players.includes(id)).length + (draft.coach !== rs.coach ? 1 : 0);
  return { total, budget, spent, bank: budget - spent, used };
}

function draftChanged() {
  store.set("wn.teamDraft", { base: teamState.saved?.saved_at, draft: teamState.draft });
  teamState.msg = "";
  render();
  clearTimeout(teamState._t);
  teamState._t = setTimeout(requestSuggestions, 250);
}

async function requestSuggestions() {
  const d = teamState.draft;
  if (!d || !state.picks) return;
  const pool = playerPool();
  const coaches = coachPool();
  const t = teamTotals(d, pool, coaches);
  const maxMoves = d.unlimited ? 6 : Math.max(0, TEAM_FREE_TRANSFERS - t.used);
  const body = { players: d.players, coach: d.coach, budget: t.budget, max_moves: maxMoves, horizon: teamState.horizon, round: state.picks.round };
  const key = JSON.stringify(body);
  if (key === teamState.suggKey) return;
  teamState.suggKey = key;
  if (!maxMoves) {
    teamState.sugg = { options: [], none: true };
    render();
    return;
  }
  teamState.suggBusy = true;
  render();
  try {
    const res = await apiPost("myteam/suggest", body);
    if (teamState.suggKey === key) teamState.sugg = res;
  } catch (e) {
    teamState.sugg = { error: e.message, options: [] };
  }
  teamState.suggBusy = false;
  render();
}

/* ---------------------------------------------------------------- edits */

function replacePlayer(out, inn) {
  const d = teamState.draft;
  d.players = d.players.map((p) => (p === out ? inn : p));
  const l = d.lineup;
  l.starters = l.starters.map((p) => (p === out ? inn : p));
  l.bench = l.bench.map((p) => (p === out ? inn : p));
  if (l.sixth === out) l.sixth = inn;
  if (l.captain === out) l.captain = inn;
}

function swapSlots(a, b) {
  const l = teamState.draft.lineup;
  const slots = [...l.starters, l.sixth, ...l.bench];
  const ia = slots.indexOf(a);
  const ib = slots.indexOf(b);
  if (ia < 0 || ib < 0) return;
  [slots[ia], slots[ib]] = [slots[ib], slots[ia]];
  l.starters = slots.slice(0, 5);
  l.sixth = slots[5];
  l.bench = slots.slice(6);
  if (!l.starters.includes(l.captain)) {
    const pool = playerPool();
    l.captain = [...l.starters].sort((x, y) => xfpOf(pool, y) - xfpOf(pool, x))[0];
  }
}

async function saveTeam() {
  const d = teamState.draft;
  const t = teamTotals(d, playerPool(), coachPool());
  try {
    const res = await apiPost("myteam", { players: d.players, coach: d.coach, bank: Math.round(t.bank * 10) / 10, lineup: d.lineup, unlimited: d.unlimited });
    teamState.saved = res.team;
    teamState.draft = draftFrom(res.team);
    store.set("wn.teamDraft", null);
    teamState.msg = "Saved. This is now your team.";
  } catch (e) {
    teamState.msg = `Not saved: ${e.message}`;
  }
  render();
}

document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-taction]");
  if (!el) return;
  const action = el.dataset.taction;
  const id = el.dataset.id;
  const d = teamState.draft;
  const pool = playerPool();
  if (action === "sel") {
    if (teamState.swap && teamState.sel && teamState.sel !== id && id !== d.coach) {
      swapSlots(teamState.sel, id);
      teamState.swap = false;
      teamState.sel = null;
      return draftChanged();
    }
    teamState.sel = teamState.sel === id ? null : id;
    teamState.swap = false;
    teamState.picker = null;
  } else if (action === "captain") {
    d.lineup.captain = teamState.sel;
    return draftChanged();
  } else if (action === "swap") {
    teamState.swap = true;
  } else if (action === "sell") {
    const out = teamState.sel;
    teamState.picker = out === d.coach ? { coach: true, out } : { out, pos: pool.get(out)?.pos };
    teamState.pq = "";
  } else if (action === "buy") {
    const { out, coach } = teamState.picker;
    if (coach) d.coach = id;
    else replacePlayer(out, id);
    teamState.picker = null;
    teamState.sel = null;
    return draftChanged();
  } else if (action === "close") {
    teamState.picker = null;
    teamState.sel = null;
    teamState.swap = false;
  } else if (action === "auto") {
    d.lineup = autoLineup(d.players, pool);
    return draftChanged();
  } else if (action === "reset") {
    teamState.draft = draftFrom(teamState.saved);
    teamState.sel = null;
    teamState.picker = null;
    store.set("wn.teamDraft", null);
    return draftChanged();
  } else if (action === "save") {
    return saveTeam();
  } else if (action === "apply") {
    const opt = teamState.sugg?.options?.[Number(id)];
    if (!opt) return;
    for (const [out, inn] of opt.moves) replacePlayer(out, inn);
    d.lineup = autoLineup(d.players, pool);
    return draftChanged();
  } else if (action === "horizon") {
    teamState.horizon = Number(id);
    requestSuggestions();
  } else if (action === "unlimited") {
    d.unlimited = !d.unlimited;
    return draftChanged();
  }
  render();
});

document.addEventListener("input", (e) => {
  if (e.target.id !== "team-pq") return;
  teamState.pq = e.target.value;
  const box = document.getElementById("picker-list");
  if (box) box.innerHTML = pickerRows();
});

/* ---------------------------------------------------------------- rendering */

const lastName = (name) => {
  const parts = String(name).split(" ");
  const suffix = ["Jr.", "Sr.", "II", "III", "IV"];
  return suffix.includes(parts[parts.length - 1]) && parts.length > 2 ? parts.slice(-2).join(" ") : parts.slice(1).join(" ") || name;
};

function shortTime(ts) {
  return ts ? new Date(ts * 1000).toLocaleString("en-GB", { weekday: "short", hour: "2-digit", minute: "2-digit" }) : "";
}

function chip(id, role, pool) {
  const r = pool.get(id);
  const sel = teamState.sel === id;
  const cls = ["pchip", `r-${role}`, sel ? "selected" : "", teamState.swap && !sel ? "swappable" : "", r && (r.severity ?? 3) <= 1 ? "doubt" : ""].join(" ");
  if (!r) return `<button type="button" class="${cls}" data-taction="sel" data-id="${esc(id)}"><span class="pc-name">Unknown player</span></button>`;
  const crest = state.picks.teams?.[r.team]?.crest;
  const mult = MULT[role];
  return `<button type="button" class="${cls}" data-taction="sel" data-id="${esc(id)}" aria-pressed="${sel}">
    ${role === "captain" ? `<span class="pc-badge" title="Captain">C</span>` : ""}
    <span class="pc-top">${crest ? `<img src="${esc(crest)}" alt="" width="18" height="18">` : ""}<span class="pc-pos">${r.pos}</span></span>
    <span class="pc-name">${esc(lastName(r.name))}</span>
    <span class="pc-meta">${r.home ? "vs" : "at"} ${esc(r.opp)}, ${esc(shortTime(r.tip))}</span>
    <span class="pc-pts">${fmt(r.xfp * mult)}<small>${mult === 1 ? "" : mult === 2 ? " ×2" : " ×½"}</small></span>
    <span class="pc-price">${fmt(r.price)} cr${r.status ? ` <span class="st-${r.severity ?? 2}">${esc(r.status)}</span>` : ""}</span>
  </button>`;
}

function coachChip(coaches) {
  const id = teamState.draft.coach;
  const c = coaches.get(id);
  const sel = teamState.sel === id;
  return `<button type="button" class="pchip coach ${sel ? "selected" : ""}" data-taction="sel" data-id="${esc(id)}" aria-pressed="${sel}">
    <span class="pc-top"><span class="pc-pos">Coach</span></span>
    <span class="pc-name">${esc(c ? lastName(c.name) : "Coach")}</span>
    <span class="pc-meta">${c ? `${c.home ? "vs" : "at"} ${esc(c.opp)}, ${esc(shortTime(c.tip))}` : ""}</span>
    <span class="pc-pts">${c ? c.win : "–"}<small>% win</small></span>
    <span class="pc-price">${c ? fmt(c.price) : "–"} cr</span>
  </button>`;
}

const COURT = `<svg class="court-lines" viewBox="0 0 500 420" preserveAspectRatio="none" aria-hidden="true">
  <rect x="2" y="2" width="496" height="416" />
  <path d="M30 418 V330 A220 220 0 0 1 470 330 V418" />
  <rect x="190" y="250" width="120" height="168" />
  <path d="M190 250 A60 60 0 0 1 310 250" />
  <circle cx="250" cy="392" r="8" />
  <line x1="222" y1="404" x2="278" y2="404" />
  <path d="M190 2 A60 60 0 0 0 310 2" />
</svg>`;

function courtView(pool, coaches) {
  const l = teamState.draft.lineup;
  // put guards up top, forwards on the wings and the biggest body in the paint
  const order = { G: 0, F: 1, C: 2 };
  const starters = [...l.starters].sort((a, b) => (order[pool.get(a)?.pos] ?? 1) - (order[pool.get(b)?.pos] ?? 1));
  const spots = starters.map((id, i) => `<div class="spot spot-${i + 1}">${chip(id, roleOf(l, id), pool)}</div>`).join("");
  return `<div class="court-wrap">
    <div class="court">${COURT}${spots}</div>
    <div class="bench">
      <div class="bench-group"><span class="bench-label">Sixth man</span>${chip(l.sixth, "sixth", pool)}</div>
      <div class="bench-group grow"><span class="bench-label">Bench, half points</span><div class="bench-row">${l.bench.map((id) => chip(id, "bench", pool)).join("")}</div></div>
      <div class="bench-group"><span class="bench-label">Coach</span>${coachChip(coaches)}</div>
    </div>
  </div>`;
}

function selectionPanel(pool, coaches, totals) {
  const d = teamState.draft;
  if (teamState.picker) return pickerPanel(pool, coaches, totals);
  const id = teamState.sel;
  if (!id) return `<p class="pick-note">Select a player to make him captain, swap him with a teammate or sell him.</p>`;
  if (teamState.swap) return `<div class="sel-panel"><p class="prose">Now select the player to swap places with.</p><button type="button" class="text-btn" data-taction="close">Cancel</button></div>`;
  if (id === d.coach) {
    const c = coaches.get(id);
    return `<div class="sel-panel"><h3>${esc(c?.name || "Coach")}</h3><p class="pick-note">${c ? `${c.win}% chance to win ${c.home ? "vs" : "at"} ${esc(c.opp)}.` : ""}</p>
      <div class="sel-actions"><button type="button" class="btn" data-taction="sell">Change coach</button><button type="button" class="text-btn" data-taction="close">Done</button></div></div>`;
  }
  const r = pool.get(id);
  const role = roleOf(d.lineup, id);
  const why = r?.reasons?.length ? `<ul class="reasons">${r.reasons.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : "";
  return `<div class="sel-panel">
    <h3>${esc(r?.name || id)} <span class="muted">${esc(r?.team || "")} ${r?.pos || ""}</span></h3>
    <p class="pick-note">${fmt(r?.xfp)} expected points, ${r?.win ?? "–"}% win chance, range ${fmt(r?.floor)} to ${fmt(r?.ceil)} PIR, ${fmt(r?.price)} cr.</p>
    ${why}
    <div class="sel-actions">
      ${role === "starter" ? `<button type="button" class="btn" data-taction="captain">Make captain</button>` : ""}
      <button type="button" class="btn" data-taction="swap">Swap places</button>
      <button type="button" class="btn" data-taction="sell">Sell</button>
      <button type="button" class="text-btn" data-taction="close">Done</button>
    </div>
  </div>`;
}

function pickerRows() {
  const pool = playerPool();
  const coaches = coachPool();
  const d = teamState.draft;
  const t = teamTotals(d, pool, coaches);
  const pk = teamState.picker;
  const room = t.bank + priceOf(pool, coaches, pk.out);
  const q = teamState.pq.trim().toLowerCase();
  if (pk.coach) {
    return [...coaches.values()]
      .filter((c) => `${c.key}|${c.team}` !== d.coach && (!q || c.name.toLowerCase().includes(q) || c.team.toLowerCase().includes(q)))
      .sort((a, b) => b.win - a.win)
      .map((c) => {
        const cid = `${c.key}|${c.team}`;
        const ok = c.price <= room + 1e-9;
        return `<tr class="${ok ? "" : "cant"}"><td class="l"><span class="strong">${esc(c.name)}</span> <span class="muted">${esc(c.team)}</span></td><td class="l muted">${c.home ? "vs" : "at"} ${esc(
          c.opp
        )}</td><td>${fmt(c.price)}</td><td class="strong">${c.win}%</td><td>${
          ok ? `<button type="button" class="btn small" data-taction="buy" data-id="${esc(cid)}">Buy</button>` : `<span class="muted">Too expensive</span>`
        }</td></tr>`;
      })
      .join("");
  }
  const rows = [...pool.values()]
    .filter((r) => r.pos === pk.pos && !d.players.includes(`${r.key}|${r.team}`))
    .filter((r) => !q || r.name.toLowerCase().includes(q) || r.team.toLowerCase().includes(q))
    .sort((a, b) => b.xfp - a.xfp)
    .slice(0, 60);
  return rows
    .map((r) => {
      const rid = `${r.key}|${r.team}`;
      const ok = r.price <= room + 1e-9;
      return `<tr class="${ok ? "" : "cant"}"><td class="l"><span class="strong">${esc(r.name)}</span> <span class="muted">${esc(r.team)}</span>${statusFlag(r)}</td><td class="l muted">${
        r.home ? "vs" : "at"
      } ${esc(r.opp)}</td><td>${fmt(r.price)}</td><td class="strong">${fmt(r.xfp)}</td><td>${fmt(r.value, 2)}</td><td>${
        ok ? `<button type="button" class="btn small" data-taction="buy" data-id="${esc(rid)}">Buy</button>` : `<span class="muted">Too expensive</span>`
      }</td></tr>`;
    })
    .join("");
}

function pickerPanel(pool, coaches, totals) {
  const pk = teamState.picker;
  const out = pk.coach ? coaches.get(pk.out) : pool.get(pk.out);
  const room = totals.bank + priceOf(pool, coaches, pk.out);
  const head = pk.coach
    ? `<tr><th class="l">Coach</th><th class="l">Next</th><th>Price</th><th>Win</th><th></th></tr>`
    : `<tr><th class="l">Player</th><th class="l">Next</th><th>Price</th><th>Exp. pts</th><th>Pts/cr</th><th></th></tr>`;
  return `<div class="sel-panel">
    <h3>Replace ${esc(out?.name || "")}</h3>
    <p class="pick-note">You can spend up to ${fmt(room)} cr: his ${fmt(out?.price)} plus ${fmt(totals.bank)} in the bank.</p>
    <div class="sel-actions"><input class="search" id="team-pq" type="search" placeholder="Find a ${pk.coach ? "coach" : "player"} or team" value="${esc(teamState.pq)}" aria-label="Find a replacement">
      <button type="button" class="text-btn" data-taction="close">Cancel</button></div>
    <div class="tablewrap"><table class="table named picker"><thead>${head}</thead><tbody id="picker-list">${pickerRows()}</tbody></table></div>
  </div>`;
}

function suggestionsPanel(pool) {
  const s = teamState.sugg;
  const d = teamState.draft;
  const horizon = seg("thorizon", [{ key: 1, label: "This round" }, { key: 3, label: "Next 3 rounds" }], teamState.horizon).replaceAll('data-action="thorizon"', 'data-taction="horizon"');
  let body;
  if (teamState.suggBusy && !s) body = skeleton(3);
  else if (!s) body = "";
  else if (s.error) body = `<p class="error">Suggestions could not be worked out: ${esc(s.error)}</p>`;
  else if (s.none) body = `<p class="pick-note">No free transfers left this round. Tick "Unlimited transfers" if this is an unlimited round.</p>`;
  else if (!s.options.length) body = `<p class="pick-note">No transfer within your budget beats the current team. Hold your transfers.</p>`;
  else
    body = s.options
      .map(
        (o, i) => `<div class="sugg">
        <div class="sugg-head"><span class="strong">${o.transfers} transfer${o.transfers > 1 ? "s" : ""}</span><span class="up strong">+${fmt(o.gain)} pts</span></div>
        <ul>${o.moves
          .map(([out, inn]) => {
            const a = pool.get(out);
            const b = pool.get(inn);
            return `<li><span class="muted">Sell</span> ${esc(a?.name || out)} <span class="muted">${fmt(a?.price)}</span> <span class="muted">for</span> ${esc(b?.name || inn)} <span class="muted">${fmt(
              b?.price
            )}</span></li>`;
          })
          .join("")}</ul>
        <div class="sugg-foot"><span class="muted">${fmt(o.bank)} cr left</span><button type="button" class="btn small" data-taction="apply" data-id="${i}">Apply</button></div>
      </div>`
      )
      .join("");
  const note =
    teamState.horizon === 3
      ? "Gains add up expected lineup points over the next three rounds, weighted 100%, 60% and 40%."
      : "Gains are expected lineup points this round, after re-picking captain, starters and bench.";
  return `<section class="panel">
    <div class="panel-head"><h2>Suggested transfers</h2>${horizon}</div>
    ${body}
    <p class="panel-note">${note} Same-position swaps only, within your budget.${d.unlimited ? "" : ` Uses your free transfers left.`}</p>
  </section>`;
}

function gamedayPanel(pool) {
  const l = teamState.draft.lineup;
  const days = new Map();
  for (const id of teamState.draft.players) {
    const r = pool.get(id);
    if (!r?.tip) continue;
    const day = new Date(r.tip * 1000).toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "short" });
    if (!days.has(day)) days.set(day, { ts: r.tip, ids: [] });
    days.get(day).ids.push(id);
  }
  const ordered = [...days.entries()].sort((a, b) => a[1].ts - b[1].ts);
  const label = { captain: "captain", starter: "starter", sixth: "sixth man", bench: "bench" };
  const lastStarter = Math.max(...l.starters.map((id) => pool.get(id)?.tip || 0));
  const firstStarter = Math.min(...l.starters.map((id) => pool.get(id)?.tip || Infinity));
  const cover = l.bench.filter((id) => (pool.get(id)?.tip || 0) > firstStarter);
  const rows = ordered
    .map(
      ([day, v]) => `<div class="gd-day"><span class="gd-date">${esc(day)}</span><span>${v.ids
        .map((id) => {
          const r = pool.get(id);
          const role = roleOf(l, id);
          return `<span class="gd-p ${role}">${esc(lastName(r.name))} <span class="muted">${label[role]}</span></span>`;
        })
        .join("")}</span></div>`
    )
    .join("");
  const tip = cover.length
    ? `${cover.map((id) => esc(lastName(pool.get(id).name))).join(", ")} ${cover.length > 1 ? "play" : "plays"} after your first starters, so ${
        cover.length > 1 ? "they" : "he"
      } can come in for a starter who has a poor game.`
    : lastStarter
    ? "None of your bench players play after your starters, so there is no late cover this round."
    : "";
  return `<section class="panel">
    <div class="panel-head"><h2>Gameday subs</h2></div>
    ${rows}
    <p class="panel-note">${tip} Subs open each morning before the day's first game. A starter who has played can be swapped for a bench player who has not; a bench player whose game is over cannot come in.</p>
  </section>`;
}

function renderTeam() {
  const P = state.picks;
  if (!P) return `<div class="picks">${skeleton(8)}</div>`;
  if (!teamState.loaded) {
    loadTeam();
    return `<div class="picks">${skeleton(8)}</div>`;
  }
  if (teamState.error) return `<div class="picks">${errorBox("Your team", teamState.error)}</div>`;
  if (!teamState.draft) return `<div class="picks"><p class="prose">No team saved yet.</p></div>`;
  const pool = playerPool();
  const coaches = coachPool();
  ensureLineup(teamState.draft, pool);
  const t = teamTotals(teamState.draft, pool, coaches);
  const d = teamState.draft;
  const changed = JSON.stringify([d.players, d.coach, d.lineup]) !== JSON.stringify([teamState.saved.players, teamState.saved.coach, teamState.saved.lineup]);
  const transfers = d.unlimited ? `${t.used} made, unlimited this round` : `${t.used} of ${TEAM_FREE_TRANSFERS} free used`;
  return `<div class="picks myteam">
    <div class="picks-head">
      <div>
        <h2 class="picks-title">My team</h2>
        <p class="picks-sub">Round ${P.round}. Plan changes here, make the same moves in the official app, then save.</p>
      </div>
      <div class="team-actions">
        <button type="button" class="btn" data-taction="auto">Best lineup</button>
        <button type="button" class="btn" data-taction="reset" ${changed ? "" : "disabled"}>Undo changes</button>
        <button type="button" class="btn primary" data-taction="save" ${changed ? "" : "disabled"}>Save team</button>
      </div>
    </div>
    <div class="team-stats">
      <div><span class="ts-big">${fmt(t.total)}</span><span class="ts-label">expected points this round</span></div>
      <div><span class="ts-big ${t.bank < -0.05 ? "down" : ""}">${fmt(t.bank)}</span><span class="ts-label">credits left of ${fmt(t.budget)}</span></div>
      <div><span class="ts-big ${!d.unlimited && t.used > TEAM_FREE_TRANSFERS ? "down" : ""}">${t.used}</span><span class="ts-label">transfers: ${transfers}</span></div>
      <label class="check"><input type="checkbox" data-taction="unlimited" ${d.unlimited ? "checked" : ""}> Unlimited transfers this round</label>
    </div>
    ${teamState.msg ? `<p class="team-msg">${esc(teamState.msg)}</p>` : ""}
    ${t.bank < -0.05 ? `<p class="team-msg down">Over budget by ${fmt(-t.bank)} cr.</p>` : ""}
    <div class="layout">
      <div class="main team-main">${courtView(pool, coaches)}${selectionPanel(pool, coaches, t)}</div>
      <aside class="rail">${suggestionsPanel(pool)}${gamedayPanel(pool)}</aside>
    </div>
    <p class="pick-note">Assumes any five positions can start. Points shown are expected fantasy points times each slot's multiplier.</p>
  </div>`;
}

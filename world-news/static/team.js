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
  const body = { players: d.players, coach: d.coach, budget: t.budget, max_moves: maxMoves, round: state.picks.round };
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
    if (teamState.suggKey === key) {
      teamState.sugg = res;
      teamState.suggFor = key;
    }
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
    d.lineup = opt.lineup && lineupValid(opt.lineup, d.players) ? JSON.parse(JSON.stringify(opt.lineup)) : autoLineup(d.players, pool);
    return draftChanged();
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
        <div class="sugg-head"><span class="strong">${o.rebuild ? `Full rebuild, ${o.transfers} transfers` : `${o.transfers} transfer${o.transfers > 1 ? "s" : ""}`}</span><span class="up strong">+${fmt(o.gain)}</span></div>
        <ul>${o.moves
          .map(([out, inn]) => {
            const a = pool.get(out);
            const b = pool.get(inn);
            return `<li><span class="muted">Sell</span> ${esc(a?.name || out)} <span class="muted">${fmt(a?.price)}</span> <span class="muted">for</span> ${esc(b?.name || inn)} <span class="muted">${fmt(
              b?.price
            )}</span></li>`;
          })
          .join("")}</ul>
        <div class="sugg-foot"><span class="muted">${fmt(o.sim.mean)} with subs, likely ${fmt(o.sim.p10)} to ${fmt(o.sim.p90)}. ${fmt(o.bank)} cr left.</span><button type="button" class="btn small" data-taction="apply" data-id="${i}">Apply</button></div>
      </div>`
      )
      .join("");
  return `<section class="panel">
    <div class="panel-head"><h2>Suggested transfers</h2>${teamState.suggBusy && s ? `<span class="muted">Updating…</span>` : ""}</div>
    ${body}
    <p class="panel-note">The mathematically best team for each number of transfers, within your budget and positions, judged on this round. Gains are expected lineup points (captain ×2, bench ×½); "with subs" plays the round 4,000 times including your morning subs. Planning further ahead tested worse, so this looks at one round.${
      d.unlimited ? "" : " Uses the free transfers you have left."
    }</p>
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
  if (!teamState.liveLoaded) {
    loadLive();
    return `<div class="picks">${skeleton(8)}</div>`;
  }
  if (teamState.view == null) teamState.view = teamState.live && !teamState.live.done ? "live" : "plan";
  if (teamState.view === "live" && teamState.live) return renderLive();
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
      ${viewSwitch()}
      <div class="team-actions">
        <button type="button" class="btn" data-taction="auto">Best lineup</button>
        <button type="button" class="btn" data-taction="reset" ${changed ? "" : "disabled"}>Undo changes</button>
        <button type="button" class="btn primary" data-taction="save" ${changed ? "" : "disabled"}>Save team</button>
      </div>
    </div>
    <div class="team-stats">
      <div><span class="ts-big">${fmt(t.total)}</span><span class="ts-label">expected points this round${
        teamState.sugg?.current?.sim && teamState.suggFor === teamState.suggKey ? `, ${fmt(teamState.sugg.current.sim.mean)} with daily subs` : ""
      }</span></div>
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

/* ---------------------------------------------------------------- live round */

teamState.view = null; // "live" or "plan"
teamState.live = null;
teamState.liveLoading = false;
teamState.liveDraft = null; // lineup being edited for the round in progress
teamState.liveSel = null;
teamState.liveSwap = false;
teamState.liveMsg = "";

const cloneLineup = (l) => JSON.parse(JSON.stringify(l));
const sameLineup = (a, b) => JSON.stringify(a) === JSON.stringify(b);

async function loadLive() {
  if (teamState.liveLoading) return;
  teamState.liveLoading = true;
  try {
    const live = (await api("myteam/live")).live;
    const editing = teamState.liveDraft && teamState.live && !sameLineup(teamState.liveDraft, teamState.live.lineup);
    teamState.live = live;
    if (!editing && live) teamState.liveDraft = cloneLineup(live.lineup); // keep unsaved edits through refreshes
    teamState.liveError = null;
  } catch (e) {
    teamState.liveError = e.message;
  }
  teamState.liveLoading = false;
  teamState.liveLoaded = true;
  render();
}

// keep live scores moving while games are on
setInterval(() => {
  if (document.visibilityState !== "visible" || state.tab !== "team" || teamState.view !== "live") return;
  const L = teamState.live;
  if (!L || L.done) return;
  const now = Date.now() / 1000;
  if (L.players.some((p) => p.state === "in" || (p.state === "pre" && p.tip && p.tip < now))) loadLive();
}, 60_000);

function viewSwitch() {
  const L = teamState.live;
  if (!L || L.done) return "";
  return seg(
    "tview",
    [
      { key: "live", label: `Round ${L.round} now` },
      { key: "plan", label: `Round ${state.picks?.round} plan` },
    ],
    teamState.view
  ).replaceAll('data-action="tview"', 'data-taction="view"');
}

/* roles and rules ------------------------------------------------- */

function liveRole(l, id) {
  if (l.captain === id) return "captain";
  if (l.starters.includes(id)) return "starter";
  return l.sixth === id ? "sixth" : "bench";
}

const liveMult = { captain: 2, starter: 1, sixth: 1, bench: 0.5 };
const isFull = (role) => role !== "bench";

function livePlayer(id) {
  return teamState.live.players.find((p) => p.id === id);
}

const hasStarted = (id) => ["in", "post"].includes(livePlayer(id)?.state);

/* Why a swap between a and b is not allowed, or "" if it is. */
function swapProblem(a, b) {
  const l = teamState.liveDraft;
  const saved = teamState.live.lineup;
  const ra = liveRole(l, a);
  const rb = liveRole(l, b);
  if (a === b) return "Pick a different player.";
  if (!isFull(ra) && !isFull(rb)) return "Both are on the bench; swapping them changes nothing.";
  if (ra === "captain" || rb === "captain") {
    if (!isFull(ra) || !isFull(rb)) return "Make someone else captain before moving him to the bench.";
  }
  for (const [x, rx, ry] of [
    [a, ra, rb],
    [b, rb, ra],
  ]) {
    // whoever moves into a full-point slot from the bench must not have played yet
    if (!isFull(rx) && isFull(ry) && hasStarted(x) && !isFull(liveRole(saved, x))) {
      return `${livePlayer(x).name}'s game has started, so he cannot come off the bench.`;
    }
  }
  return "";
}

function captainProblem(id) {
  const l = teamState.liveDraft;
  const savedCap = teamState.live.lineup.captain;
  if (!l.starters.includes(id)) return "The captain has to be one of the five starters.";
  if (id === l.captain) return "He is already captain.";
  if (hasStarted(savedCap)) return "Your captain has already played, so the captaincy is fixed for this round.";
  if (hasStarted(id)) return "A new captain must be someone whose game has not started.";
  return "";
}

function liveSwap(a, b) {
  const l = teamState.liveDraft;
  const slots = [...l.starters, l.sixth, ...l.bench];
  const ia = slots.indexOf(a);
  const ib = slots.indexOf(b);
  [slots[ia], slots[ib]] = [slots[ib], slots[ia]];
  l.starters = slots.slice(0, 5);
  l.sixth = slots[5];
  l.bench = slots.slice(6);
}

function liveTotals() {
  const l = teamState.liveDraft;
  let banked = 0;
  let live = 0;
  let toCome = 0;
  for (const p of teamState.live.players) {
    const m = liveMult[liveRole(l, p.id)];
    if (p.state === "post") banked += (p.fp || 0) * m;
    else if (p.state === "in") live += (p.fp || 0) * m;
    else toCome += (p.xfp || 0) * m;
  }
  return { banked, live, toCome, total: banked + live + toCome };
}

/* events ------------------------------------------------------------ */

document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-taction]");
  if (!el) return;
  const action = el.dataset.taction;
  const id = el.dataset.id;
  if (action === "view") {
    teamState.view = id;
  } else if (action === "lsel") {
    if (teamState.liveSwap && teamState.liveSel && teamState.liveSel !== id) {
      const problem = swapProblem(teamState.liveSel, id);
      if (problem) {
        teamState.liveMsg = problem;
      } else {
        liveSwap(teamState.liveSel, id);
        teamState.liveMsg = "";
        teamState.liveSel = null;
        teamState.liveSwap = false;
      }
    } else {
      teamState.liveSel = teamState.liveSel === id ? null : id;
      teamState.liveSwap = false;
      teamState.liveMsg = "";
    }
  } else if (action === "lcaptain") {
    const problem = captainProblem(teamState.liveSel);
    if (problem) teamState.liveMsg = problem;
    else {
      teamState.liveDraft.captain = teamState.liveSel;
      teamState.liveMsg = "";
    }
  } else if (action === "lswap") {
    teamState.liveSwap = true;
    teamState.liveMsg = "";
  } else if (action === "lclose") {
    teamState.liveSel = null;
    teamState.liveSwap = false;
    teamState.liveMsg = "";
  } else if (action === "lsuggest") {
    teamState.liveDraft = cloneLineup(teamState.live.subs.lineup);
    teamState.liveSel = null;
    teamState.liveSwap = false;
    teamState.liveMsg = "Suggested subs filled in. Check them, then press Save subs.";
  } else if (action === "lundo") {
    teamState.liveDraft = cloneLineup(teamState.live.lineup);
    teamState.liveSel = null;
    teamState.liveSwap = false;
    teamState.liveMsg = "";
  } else if (action === "lsave") {
    apiPost("myteam/live", { lineup: teamState.liveDraft })
      .then((d) => {
        teamState.live = d.live;
        teamState.liveDraft = cloneLineup(d.live.lineup);
        teamState.liveMsg = "Subs saved.";
        render();
      })
      .catch((err) => {
        teamState.liveMsg = `Not saved: ${err.message}`;
        render();
      });
    return;
  } else return;
  render();
});

/* rendering --------------------------------------------------------- */

function resultLine(p) {
  if (p.state === "post") {
    const [h, a] = p.score || [];
    const mine = p.home ? h : a;
    const theirs = p.home ? a : h;
    return `<span class="${p.won ? "up" : "down"}">${p.won ? "W" : "L"} ${mine}-${theirs}</span> ${p.home ? "vs" : "at"} ${esc(p.opp)}`;
  }
  if (p.state === "in") {
    const [h, a] = p.score || [];
    return `<span class="live">${esc(p.detail || "Live")}</span> ${p.home ? h : a}-${p.home ? a : h}`;
  }
  return `${p.home ? "vs" : "at"} ${esc(p.opp || "")}, ${esc(shortTime(p.tip))}`;
}

function liveChip(id) {
  const p = livePlayer(id);
  if (!p) return "";
  const l = teamState.liveDraft;
  const role = liveRole(l, id);
  const mult = liveMult[role];
  const savedRole = liveRole(teamState.live.lineup, id);
  const crest = state.picks?.teams?.[p.team]?.crest;
  const multTxt = mult === 2 ? " ×2" : mult === 0.5 ? " ×½" : "";
  let big, small, line;
  if (p.state === "pre") {
    big = fmt(p.xfp * mult);
    small = `expected${multTxt}`;
    line = `${fmt(p.price)} cr${p.status ? ` <span class="st-${p.severity ?? 2}">${esc(p.status)}</span>` : ""}`;
  } else if (!p.played) {
    big = "0";
    small = p.state === "post" ? "did not play" : "not in yet";
    line = "";
  } else {
    big = fmt((p.fp || 0) * mult);
    small = `${p.pir} PIR${p.won ? " +10%" : ""}${multTxt}`;
    line = `${p.pts} pts, ${p.reb} reb, ${p.ast} ast, ${p.min} min`;
  }
  const sel = teamState.liveSel === id;
  const target = teamState.liveSwap && teamState.liveSel && !sel;
  const blocked = target && swapProblem(teamState.liveSel, id);
  const moved = role !== savedRole;
  const cls = [
    "pchip",
    "live-chip",
    `r-${role}`,
    p.state === "post" ? "done" : "",
    p.state === "in" ? "playing" : "",
    (p.severity ?? 3) <= 1 && p.state === "pre" ? "doubt" : "",
    sel ? "selected" : "",
    target && !blocked ? "swappable" : "",
    blocked ? "blocked" : "",
    moved ? "moved" : "",
  ].join(" ");
  return `<button type="button" class="${cls}" data-taction="lsel" data-id="${esc(id)}" aria-pressed="${sel}" ${blocked ? `title="${esc(blocked)}"` : ""}>
    ${role === "captain" ? `<span class="pc-badge" title="Captain">C</span>` : ""}
    <span class="pc-top">${crest ? `<img src="${esc(crest)}" alt="" width="18" height="18">` : ""}<span class="pc-pos">${p.pos || ""}</span></span>
    <span class="pc-name">${esc(lastName(p.name))}</span>
    <span class="pc-meta">${resultLine(p)}</span>
    <span class="pc-pts">${big}<small> ${small}</small></span>
    <span class="pc-price">${line}</span>
  </button>`;
}

function liveCourt(L) {
  const l = teamState.liveDraft;
  const order = { G: 0, F: 1, C: 2 };
  const starters = [...l.starters].sort((a, b) => (order[livePlayer(a)?.pos] ?? 1) - (order[livePlayer(b)?.pos] ?? 1));
  const spots = starters.map((id, i) => `<div class="spot spot-${i + 1}">${liveChip(id)}</div>`).join("");
  const c = L.coach;
  let coachChip = "";
  if (c) {
    const res = c.state === "post" ? `<span class="${c.won ? "up" : "down"}">${c.won ? "Won" : "Lost"}</span>` : c.state === "in" ? `<span class="live">Live</span>` : esc(shortTime(c.tip));
    coachChip = `<div class="pchip live-chip coach"><span class="pc-top"><span class="pc-pos">Coach</span></span><span class="pc-name">${esc(lastName(c.name || ""))}</span><span class="pc-meta">${
      c.home ? "vs" : "at"
    } ${esc(c.opp || "")}</span><span class="pc-pts" style="font-size:1rem">${res}</span></div>`;
  }
  return `<div class="court-wrap">
    <div class="court">${COURT}${spots}</div>
    <div class="bench">
      <div class="bench-group"><span class="bench-label">Sixth man</span>${liveChip(l.sixth)}</div>
      <div class="bench-group grow"><span class="bench-label">Bench, half points</span><div class="bench-row">${l.bench.map((id) => liveChip(id)).join("")}</div></div>
      <div class="bench-group"><span class="bench-label">Coach</span>${coachChip}</div>
    </div>
  </div>`;
}

function liveSelectionPanel() {
  const id = teamState.liveSel;
  const msg = teamState.liveMsg ? `<p class="team-msg">${esc(teamState.liveMsg)}</p>` : "";
  if (!id) return `${msg}<p class="pick-note">Select a player to make him captain or swap him with someone else.</p>`;
  const p = livePlayer(id);
  if (teamState.liveSwap) {
    return `<div class="sel-panel"><p class="prose">Now select who ${esc(p.name)} swaps with. Greyed-out players cannot swap with him.</p>${msg}
      <button type="button" class="text-btn" data-taction="lclose">Cancel</button></div>`;
  }
  const role = liveRole(teamState.liveDraft, id);
  const capProblem = captainProblem(id);
  const status =
    p.state === "post"
      ? `Finished: ${p.played ? `${p.pir} PIR, ${fmt(p.fp)} fantasy points` : "did not play"}.`
      : p.state === "in"
      ? `Playing now: ${p.pir ?? 0} PIR so far.`
      : `Plays ${shortTime(p.tip)}, expected ${fmt(p.xfp)} fantasy points.`;
  return `<div class="sel-panel">
    <h3>${esc(p.name)} <span class="muted">${esc(p.team)} ${p.pos || ""}, ${role === "sixth" ? "sixth man" : role}</span></h3>
    <p class="pick-note">${status}</p>
    ${msg}
    <div class="sel-actions">
      ${role === "starter" ? `<button type="button" class="btn" data-taction="lcaptain" ${capProblem ? `disabled title="${esc(capProblem)}"` : ""}>Make captain</button>` : ""}
      <button type="button" class="btn" data-taction="lswap">Swap with…</button>
      <button type="button" class="text-btn" data-taction="lclose">Done</button>
    </div>
    ${role === "starter" && capProblem && capProblem !== "He is already captain." ? `<p class="pick-note">${esc(capProblem)}</p>` : ""}
  </div>`;
}

function liveSubsPanel(L) {
  const s = L.subs;
  const name = (id) => esc(livePlayer(id)?.name || id);
  const day = (ts) => {
    if (!ts) return "";
    const d = new Date(ts * 1000);
    return d.toDateString() === new Date().toDateString() ? "this morning" : `${d.toLocaleDateString("en-GB", { weekday: "long" })} morning`;
  };
  const edited = !sameLineup(teamState.liveDraft, L.lineup);
  let body;
  if (!s.moves.length && !s.captain) body = `<p class="prose">No subs worth making for your saved lineup: your full-point slots already hold your best remaining scorers.</p>`;
  else
    body = `${s.moves
      .map(
        (m) => `<div class="sugg"><div class="sugg-head"><span><span class="muted">Bench</span> ${name(m.out)} <span class="muted">for</span> ${name(m.in)}</span><span class="up strong">+${fmt(m.gain)}</span></div>
        <p class="pick-note">${livePlayer(m.out)?.state === "post" ? `${name(m.out)} finished with ${fmt(livePlayer(m.out).fp)}. ` : ""}${name(m.in)} is expected to score ${fmt(
          livePlayer(m.in)?.xfp
        )}. Decide by ${day(m.by)}.</p></div>`
      )
      .join("")}${s.captain ? `<p class="prose">Make ${name(s.captain)} captain.</p>` : ""}
      <div class="sel-actions"><button type="button" class="btn" data-taction="lsuggest">Use suggested subs</button></div>`;
  return `<section class="panel">
    <div class="panel-head"><h2>Suggested subs</h2></div>
    ${edited ? `<p class="pick-note">These are for your saved lineup. Save your changes to refresh them.</p>` : ""}
    ${body}
    <p class="panel-note">A starter whose game is over can go to the bench for a bench player who has not played yet. Bench players whose game has started cannot come in. The captain is fixed once he has played. Swaps worth under 1 point are left out.</p>
  </section>`;
}

function renderLive() {
  const L = teamState.live;
  if (!teamState.liveDraft) teamState.liveDraft = cloneLineup(L.lineup);
  const t = liveTotals();
  const edited = !sameLineup(teamState.liveDraft, L.lineup);
  const playing = L.players.filter((p) => p.state === "in").length;
  return `<div class="picks myteam">
    <div class="picks-head">
      <div>
        <h2 class="picks-title">My team</h2>
        <p class="picks-sub">Round ${L.round}, in progress. Finished games show real points; the rest show what is expected.</p>
      </div>
      ${viewSwitch()}
      <div class="team-actions">
        <button type="button" class="btn" data-taction="lundo" ${edited ? "" : "disabled"}>Undo changes</button>
        <button type="button" class="btn primary" data-taction="lsave" ${edited ? "" : "disabled"}>Save subs</button>
      </div>
    </div>
    <div class="team-stats">
      <div><span class="ts-big">${fmt(t.banked)}</span><span class="ts-label">points from finished games</span></div>
      ${playing ? `<div><span class="ts-big live">${fmt(t.live)}</span><span class="ts-label">in ${playing} game${playing > 1 ? "s" : ""} now</span></div>` : ""}
      <div><span class="ts-big">${fmt(t.toCome)}</span><span class="ts-label">expected from games to come</span></div>
      <div><span class="ts-big">${fmt(t.total)}</span><span class="ts-label">projected round total${edited ? `, ${t.total >= L.projected ? "+" : ""}${fmt(t.total - L.projected)} vs saved` : ""}</span></div>
    </div>
    ${edited ? `<p class="team-msg">Unsaved subs. Make the same moves in the official app, then press Save subs.</p>` : ""}
    <div class="layout">
      <div class="main team-main">${liveCourt(L)}${liveSelectionPanel()}</div>
      <aside class="rail">${liveSubsPanel(L)}</aside>
    </div>
  </div>`;
}

"use strict";

/* ================================================================ helpers */

const $ = (sel, el = document) => el.querySelector(sel);
const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const nowSec = () => Date.now() / 1000;

function timeAgo(ts) {
  const d = nowSec() - ts;
  if (d < 90) return "just now";
  if (d < 3600) return `${Math.round(d / 60)} min ago`;
  if (d < 86400) return `${Math.round(d / 3600)}h ago`;
  return new Date(ts * 1000).toLocaleString("en-GB", { weekday: "short", hour: "2-digit", minute: "2-digit" });
}

function clock(ts) {
  return new Date(ts * 1000).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

function dayStamp(ts) {
  return new Date(ts * 1000).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

function gameTime(ts) {
  if (!ts) return "Time to be confirmed";
  const d = new Date(ts * 1000);
  const today = new Date();
  const tomorrow = new Date();
  tomorrow.setDate(today.getDate() + 1);
  const t = clock(ts);
  if (d.toDateString() === today.toDateString()) return `Today ${t}`;
  if (d.toDateString() === tomorrow.toDateString()) return `Tomorrow ${t}`;
  return d.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" }) + ` ${t}`;
}

async function api(path, fresh = false) {
  const res = await fetch(`/api/${path}${fresh ? "?fresh=1" : ""}`);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || `Request failed (${res.status})`);
  return body;
}

const store = {
  get(k, fallback) {
    try {
      const v = localStorage.getItem(k);
      return v == null ? fallback : JSON.parse(v);
    } catch {
      return fallback;
    }
  },
  set(k, v) {
    try {
      localStorage.setItem(k, JSON.stringify(v));
    } catch {
      /* private mode: fine */
    }
  },
};

/* ================================================================ state */

const SPORT_TABS = [
  { id: "euroleague", title: "EuroLeague", topic: "euroleague", league: "euroleague" },
  { id: "fantasy", title: "Fantasy" },
  { id: "nba", title: "NBA", topic: "nba", league: "nba" },
  { id: "gbl", title: "Greek league", topic: "greek", league: "gbl" },
];

const LEAGUE_INFO = {
  euroleague: { homeFirst: true, note: "Top 6 go to the playoffs, 7–10 to the play-in." },
  nba: { homeFirst: false, note: "Top 6 in each conference go to the playoffs, 7–10 to the play-in." },
  gbl: { homeFirst: true, note: "Top 8 go to the playoffs." },
};

const state = {
  meta: null,
  tab: "work",
  sub: { work: "all", sports: "euroleague", other: "all" },
  news: {},
  leagues: {},
  fantasy: null,
  markets: null,
  errors: {},
  round: {},
  group: {},
  perfRound: null,
  injFilter: store.get("wn.injFilter", "all"),
  injQuery: "",
  baseline: null,
  refreshing: false,
};

/* "New" means published after you last had the page open. A visit counts as
   new once the page has been closed for more than two hours, so reloading
   during the same morning keeps the same markers. */
function initVisit() {
  const v = store.get("wn.visit", {});
  const now = nowSec();
  if (!v.lastSeen || now - v.lastSeen > 2 * 3600) v.baseline = v.lastSeen || null;
  v.lastSeen = now;
  store.set("wn.visit", v);
  state.baseline = v.baseline;
  const touch = () => {
    const cur = store.get("wn.visit", {});
    cur.lastSeen = nowSec();
    store.set("wn.visit", cur);
  };
  setInterval(() => document.visibilityState === "visible" && touch(), 60_000);
  document.addEventListener("visibilitychange", touch);
}

const isNew = (item) => state.baseline && item.ts > state.baseline;

function favourite(team) {
  const favs = state.meta?.favorite_teams || [];
  if (!favs.length || !team) return false;
  const hay = `${team.name || ""} ${team.full || ""} ${team.code || ""}`.toLowerCase();
  return favs.some((f) => hay.includes(String(f).toLowerCase()));
}

/* ================================================================ data loading */

async function load(kind, arg, fresh = false) {
  const key = arg ? `${kind}:${arg}` : kind;
  try {
    if (kind === "news") state.news[arg] = await api(`news/${arg}`, fresh);
    else if (kind === "sports") state.leagues[arg] = await api(`sports/${arg}`, fresh);
    else if (kind === "fantasy") state.fantasy = await api("fantasy", fresh);
    else if (kind === "markets") state.markets = await api("markets", fresh);
    delete state.errors[key];
  } catch (e) {
    state.errors[key] = e.message;
  }
  render();
}

function loadAll(fresh = false) {
  const jobs = [];
  for (const s of state.meta.sections) jobs.push(load("news", s.id, fresh && s.id === state.tab));
  const sportsFresh = fresh && state.tab === "sports";
  for (const lg of ["euroleague", "nba", "gbl"]) jobs.push(load("sports", lg, sportsFresh));
  jobs.push(load("markets", null, fresh && state.tab === "other"));
  jobs.push(load("fantasy", null, sportsFresh));
  return Promise.all(jobs);
}

/* ================================================================ routing */

function readHash() {
  const [tab, sub] = location.hash.replace(/^#/, "").split("/");
  if (["work", "sports", "other"].includes(tab)) {
    state.tab = tab;
    if (sub) state.sub[tab] = sub;
  }
}

function go(tab, sub) {
  state.tab = tab;
  if (sub) state.sub[tab] = sub;
  const s = state.sub[tab];
  history.replaceState(null, "", `#${tab}${s && s !== "all" ? "/" + s : ""}`);
  render();
  window.scrollTo({ top: Math.min(window.scrollY, $(".tabs").offsetTop - 12) });
}

/* ================================================================ rendering: chrome */

function renderMasthead() {
  const now = new Date();
  $("#date").textContent = now.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" });
  const h = now.getHours();
  const hello = h < 5 ? "Up late" : h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
  const name = state.meta?.name;
  let line = `${hello}${name ? `, <strong>${esc(name)}</strong>` : ""}.`;
  const total = ["work", "sports", "other"].reduce((n, s) => n + newCount(s), 0);
  if (state.baseline && total) {
    const when = new Date(state.baseline * 1000).toLocaleString("en-GB", { weekday: "long", hour: "2-digit", minute: "2-digit" });
    line += ` ${total} new ${total === 1 ? "story" : "stories"} since ${when}.`;
  }
  $("#greeting").innerHTML = line;

  const times = Object.values(state.news).map((d) => d.fetched).filter(Boolean);
  const updated = times.length ? Math.min(...times) : null;
  $("#updated").textContent = state.refreshing ? "Refreshing…" : updated ? `Updated ${clock(updated)}` : "";
  $("#refresh").disabled = state.refreshing;
}

function newCount(sectionId) {
  const d = state.news[sectionId];
  if (!d || !state.baseline) return 0;
  return d.topics.reduce((n, t) => n + t.items.filter(isNew).length, 0);
}

function renderTabs() {
  const sections = state.meta?.sections || [];
  $("#tabs").innerHTML = sections
    .map((s, i) => {
      const n = newCount(s.id);
      return `<button type="button" class="tab" role="tab" data-action="tab" data-id="${s.id}"
        aria-selected="${s.id === state.tab}" title="${esc(s.title)} (${i + 1})">${esc(s.title)}${
        n ? `<span class="count" aria-label="${n} new">${n}</span>` : ""
      }</button>`;
    })
    .join("");
}

function subnav(items, active, tab) {
  return `<div class="subnav" role="toolbar" aria-label="Topics">${items
    .map(
      (it) =>
        `<button type="button" class="chip" data-action="sub" data-tab="${tab}" data-id="${it.id}" aria-pressed="${
          it.id === active
        }">${esc(it.title)}</button>`
    )
    .join("")}</div>`;
}

const skeleton = (rows = 6) => `<div class="skeleton" aria-label="Loading">${"<div></div>".repeat(rows)}</div>`;

function errorBox(what, msg) {
  return `<p class="error">${esc(what)} could not be loaded: ${esc(msg)}. Press Refresh to try again.</p>`;
}

/* ================================================================ rendering: stories */

function story(it, compact = false) {
  const meta = [`<span class="src">${esc(it.source)}</span>`, `<time datetime="${new Date(it.ts * 1000).toISOString()}">${timeAgo(it.ts)}</time>`];
  if (it.points != null) meta.push(`<span>${it.points.toLocaleString("en")} points</span>`);
  if (it.comments_url) {
    const c = it.comments != null ? `${it.comments.toLocaleString("en")} comments` : "Comments";
    meta.push(`<a href="${esc(it.comments_url)}" target="_blank" rel="noopener">${c}</a>`);
  }
  return `<article class="story${isNew(it) ? " is-new" : ""}">
    <a class="story-title" href="${esc(it.link)}" target="_blank" rel="noopener">${esc(it.title)}</a>
    ${!compact && it.summary ? `<p class="story-summary">${esc(it.summary)}</p>` : ""}
    <div class="meta">${meta.join("")}</div>
  </article>`;
}

function topicGroup(t, { limit, tab, showMore = true, compact = false } = {}) {
  const items = limit ? t.items.slice(0, limit) : t.items;
  const more =
    showMore && limit && t.items.length > limit
      ? `<button type="button" class="text-btn" data-action="sub" data-tab="${tab}" data-id="${t.id}">See all ${t.items.length}</button>`
      : "";
  return `<section class="group">
    <div class="group-head"><h2 class="group-title">${esc(t.title)}</h2>${more}</div>
    ${items.length ? items.map((i) => story(i, compact)).join("") : `<p class="empty">Nothing new here in the last few days.</p>`}
  </section>`;
}

function railTopic(t) {
  return `<section class="rail-block compact">
    <div class="rail-head"><h2>${esc(t.title)}</h2></div>
    ${t.items.length ? t.items.map((i) => story(i, true)).join("") : `<p class="empty">Nothing to show yet.</p>`}
  </section>`;
}

function renderNewsSection(id) {
  const sec = state.meta.sections.find((s) => s.id === id);
  const data = state.news[id];
  const mainTopics = sec.topics.filter((t) => t.placement !== "rail");
  const active = state.sub[id] && (state.sub[id] === "all" || mainTopics.some((t) => t.id === state.sub[id])) ? state.sub[id] : "all";
  const nav = subnav([{ id: "all", title: "All" }, ...mainTopics], active, id);

  let main;
  let rail = "";
  if (!data) {
    main = state.errors[`news:${id}`] ? errorBox(sec.title, state.errors[`news:${id}`]) : skeleton(10);
  } else {
    const topics = data.topics.filter((t) => t.placement !== "rail");
    main =
      active === "all"
        ? topics.map((t) => topicGroup(t, { limit: 5, tab: id })).join("")
        : topicGroup(topics.find((t) => t.id === active) || topics[0], { tab: id });
    rail = data.topics.filter((t) => t.placement === "rail").map(railTopic).join("");
  }
  if (id === "other") rail = marketsPanel() + rail;
  return nav + `<div class="layout"><div class="main">${main}</div>${rail ? `<aside class="rail">${rail}</aside>` : ""}</div>`;
}

/* ================================================================ rendering: markets */

function marketsPanel() {
  const m = state.markets;
  let body;
  if (!m) body = state.errors.markets ? `<p class="empty">Market data is unavailable right now.</p>` : skeleton(4);
  else if (!m.quotes.length) body = `<p class="empty">Market data is unavailable right now.</p>`;
  else
    body = `<div class="quotes">${m.quotes
      .map(
        (q) => `<div class="quote"><span class="q-label">${esc(q.label)}</span><span class="q-last">${esc(q.last)}</span><span class="q-pct ${q.dir}">${esc(
          q.pct
        )}</span></div>`
      )
      .join("")}</div>`;
  const note = m?.fetched ? `<p class="panel-note">Checked ${clock(m.fetched)}. Quotes can be delayed.</p>` : "";
  return `<section class="panel"><div class="panel-head"><h2>Markets</h2></div>${body}${note}</section>`;
}

/* ================================================================ rendering: sports */

function seg(action, options, active, extra = "") {
  return `<div class="seg" role="group">${options
    .map(
      (o) =>
        `<button type="button" data-action="${action}" data-id="${esc(o.key)}" ${extra} aria-pressed="${String(o.key) === String(active)}">${esc(
          o.label
        )}</button>`
    )
    .join("")}</div>`;
}

function teamRow(t, side, g) {
  const cls = ["team"];
  if (g.state === "post" && g.winner) cls.push(g.winner === side ? "win" : "lose");
  if (favourite(t)) cls.push("fav");
  const crest = t.crest ? `<img src="${esc(t.crest)}" alt="" loading="lazy" width="20" height="20">` : "<span></span>";
  const rec = t.record ? `<span class="rec">${esc(t.record)}</span>` : "";
  return `<div class="${cls.join(" ")}">${crest}<span class="tname">${esc(t.name)}${rec}</span><span class="score">${t.score ?? ""}</span></div>`;
}

function gameCard(g, league) {
  const order = LEAGUE_INFO[league].homeFirst ? ["home", "away"] : ["away", "home"];
  let status;
  if (g.state === "post") status = "Final";
  else if (g.state === "in") status = `<span class="live">${esc(g.detail || "Live")}</span>`;
  else status = gameTime(g.ts);
  let lead = "";
  if (g.leaders?.length) {
    const top = [...g.leaders].sort((a, b) => parseFloat(b.value) - parseFloat(a.value))[0];
    lead = `${esc(top.name)} ${esc(top.value)} pts`;
  } else if (g.state === "pre" && g.tv) lead = esc(g.tv);
  const inner = `${teamRow(g[order[0]], order[0], g)}${teamRow(g[order[1]], order[1], g)}
    <div class="game-foot"><span>${status}</span><span class="lead">${lead}</span></div>`;
  return g.link
    ? `<a class="game" href="${esc(g.link)}" target="_blank" rel="noopener">${inner}</a>`
    : `<div class="game">${inner}</div>`;
}

function scoreboard(L, league) {
  const key = state.round[league] ?? L.default;
  const round = L.rounds.find((r) => String(r.key) === String(key)) || L.rounds[L.rounds.length - 1];
  const head = `<div class="panel-head"><h2>Scores</h2>${L.rounds.length > 1 ? seg("round", L.rounds, round?.key, `data-league="${league}"`) : ""}</div>`;
  const games = round?.games?.length
    ? `<div class="games">${round.games.map((g) => gameCard(g, league)).join("")}</div>`
    : `<p class="empty">No games ${league === "nba" ? "on this day" : "in this round"}.</p>`;
  return `<section class="panel">${head}${games}</section>`;
}

function standingsPanel(L, league) {
  const groups = L.standings || [];
  if (!groups.length || !groups.some((g) => g.rows.length))
    return `<section class="panel"><div class="panel-head"><h2>Standings</h2></div><p class="empty">Standings are unavailable right now.</p></section>`;
  const gi = Math.min(state.group[league] ?? 0, groups.length - 1);
  const grp = groups[gi];
  const switcher = groups.length > 1 ? seg("group", groups.map((g, i) => ({ key: i, label: g.label })), gi, `data-league="${league}"`) : "";
  const cols =
    league === "nba"
      ? [["W", "w"], ["L", "l"], ["GB", "gb"], ["Strk", "streak"]]
      : league === "gbl"
      ? [["W", "w"], ["L", "l"], ["Pts", "pts"], ["+/−", "diff"]]
      : [["W", "w"], ["L", "l"], ["+/−", "diff"]];
  const cuts = new Set(grp.lines || []);
  const rows = grp.rows
    .map((r, i) => {
      const cls = [cuts.has(i + 1) ? "cut" : "", favourite(r) ? "fav" : ""].join(" ").trim();
      const crest = r.crest ? `<img src="${esc(r.crest)}" alt="" loading="lazy" width="18" height="18">` : "";
      const cells = cols
        .map(([, k], ci) => {
          let v = r[k] ?? "";
          if (k === "diff" && typeof v === "number" && v > 0) v = `+${v}`;
          return `<td class="${ci === 0 ? "strong" : k === "diff" || k === "streak" ? "muted" : ""}">${esc(v)}</td>`;
        })
        .join("");
      return `<tr class="${cls}"><td>${r.rank}</td><td class="l team-cell"><div>${crest}<span>${esc(r.name)}</span></div></td>${cells}</tr>`;
    })
    .join("");
  return `<section class="panel">
    <div class="panel-head"><h2>Standings</h2>${switcher}</div>
    <table class="table"><thead><tr><th>#</th><th class="l">Team</th>${cols.map(([h]) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows}</tbody></table>
    <p class="panel-note">${LEAGUE_INFO[league].note}</p>
  </section>`;
}

function sportsNews(topicId) {
  const d = state.news.sports;
  if (!d) return state.errors["news:sports"] ? errorBox("Sports news", state.errors["news:sports"]) : skeleton(6);
  const t = d.topics.find((x) => x.id === topicId);
  return t ? topicGroup(t, { showMore: false }) : "";
}

function renderLeague(tab) {
  const L = state.leagues[tab.league];
  let scores, standings;
  if (!L) {
    const err = state.errors[`sports:${tab.league}`];
    scores = `<section class="panel">${err ? errorBox(`${tab.title} scores`, err) : skeleton(4)}</section>`;
    standings = "";
  } else {
    scores = scoreboard(L, tab.league);
    standings = standingsPanel(L, tab.league);
  }
  return `<div class="layout"><div class="main">${scores}${sportsNews(tab.topic)}</div><aside class="rail">${standings}</aside></div>`;
}

/* ================================================================ rendering: fantasy */

function injuryIndex() {
  const idx = new Map();
  for (const t of state.fantasy?.injuries?.teams || []) for (const p of t.players) idx.set(p.key, p);
  return idx;
}

function injuryList() {
  const inj = state.fantasy?.injuries;
  if (!inj) return "";
  const q = state.injQuery.trim().toLowerCase();
  const keep = (p, team) => {
    if (state.injFilter === "out" && p.severity !== 0) return false;
    if (state.injFilter === "gtd" && (p.severity === 0 || p.severity === 3)) return false;
    if (q && !p.name.toLowerCase().includes(q) && !team.toLowerCase().includes(q)) return false;
    return true;
  };
  const html = inj.teams
    .map((t) => {
      const ps = t.players.filter((p) => keep(p, t.team));
      if (!ps.length) return "";
      return `<section class="inj-team">
        <h3>${t.logo ? `<img src="${esc(t.logo)}" alt="" loading="lazy" width="22" height="22">` : ""}${esc(t.team)}</h3>
        ${ps
          .map(
            (p) => `<div class="inj">
            <div class="who">${p.link ? `<a href="${esc(p.link)}" target="_blank" rel="noopener">${esc(p.name)}</a>` : esc(p.name)}<span class="pos">${esc(
              p.pos
            )}</span></div>
            <div><span class="st st-${p.severity}">${esc(p.status)}</span></div>
            <div class="note">${p.comment_link ? `<a href="${esc(p.comment_link)}" target="_blank" rel="noopener">${esc(p.comment)}</a>` : esc(p.comment)}<span class="rnd">${esc(
              p.round
            )}</span></div>
          </div>`
          )
          .join("")}
      </section>`;
    })
    .join("");
  return html || `<p class="empty">No players match. Clear the search or switch to All.</p>`;
}

function injuryPanel() {
  const F = state.fantasy;
  if (!F) return `<section class="group">${state.errors.fantasy ? errorBox("Fantasy data", state.errors.fantasy) : skeleton(8)}</section>`;
  const inj = F.injuries;
  if (!inj) return `<section class="group"><h2 class="group-title">Injury report</h2><p class="error">The BasketNews injury report could not be loaded. Press Refresh to try again.</p></section>`;
  const total = inj.teams.reduce((n, t) => n + t.players.length, 0);
  const out = inj.teams.reduce((n, t) => n + t.players.filter((p) => p.severity === 0).length, 0);
  const filters = seg(
    "inj",
    [
      { key: "all", label: `All ${total}` },
      { key: "out", label: `Out ${out}` },
      { key: "gtd", label: "Game-time calls" },
    ],
    state.injFilter
  );
  const updated = inj.updated ? `updated ${dayStamp(inj.updated)}` : "";
  return `<section class="group">
    <div class="group-head"><h2 class="group-title">Injury report</h2><a class="text-btn" href="${esc(inj.source)}" target="_blank" rel="noopener">BasketNews ${updated}</a></div>
    <div class="inj-tools">${filters}<input class="search" id="inj-search" type="search" placeholder="Find a player or team" value="${esc(
      state.injQuery
    )}" aria-label="Find a player or team"></div>
    <div id="inj-list">${injuryList()}</div>
  </section>`;
}

function flagFor(key, idx) {
  const p = idx.get(key);
  return p ? `<span class="flag st-${p.severity}" title="${esc(p.comment)}">${esc(p.status)}</span>` : "";
}

function performersPanel() {
  const F = state.fantasy;
  if (!F) return "";
  const rounds = F.rounds || [];
  if (!rounds.length) return `<section class="panel"><div class="panel-head"><h2>Top PIR by round</h2></div><p class="empty">No finished games yet this season.</p></section>`;
  const fullRounds = rounds.filter((r) => r.played === r.total);
  const fallback = (fullRounds[fullRounds.length - 1] || rounds[rounds.length - 1]).key;
  const key = state.perfRound ?? fallback;
  const r = rounds.find((x) => String(x.key) === String(key)) || rounds[rounds.length - 1];
  const idx = injuryIndex();
  const opts = rounds.map((x) => ({ key: x.key, label: x.played < x.total ? `${x.label} (${x.played}/${x.total})` : x.label }));
  const list = r.players
    .map(
      (p, i) => `<div class="perf">
      <span class="rank">${i + 1}</span>
      <span class="who">${esc(p.name)}<span class="team-code">${esc(p.team)}</span>${flagFor(p.key, idx)}</span>
      <span class="pir">${p.pir}<small>PIR</small></span>
      <span class="line">${p.pts} pts, ${p.reb} reb, ${p.ast} ast in ${p.min} min</span>
    </div>`
    )
    .join("");
  return `<section class="panel"><div class="panel-head"><h2>Top PIR by round</h2>${rounds.length > 1 ? seg("perf", opts, r.key) : ""}</div>${list}</section>`;
}

function leadersPanel() {
  const F = state.fantasy;
  if (!F?.leaders?.length) return "";
  const idx = injuryIndex();
  const rows = F.leaders
    .map(
      (p, i) => `<tr><td>${i + 1}</td><td class="l"><span class="strong">${esc(p.name)}</span> <span class="muted">${esc(p.team)}</span>${flagFor(
        p.key,
        idx
      )}</td><td class="muted">${p.gp}</td><td class="muted">${p.min}</td><td class="strong">${p.pir}</td></tr>`
    )
    .join("");
  return `<section class="panel">
    <div class="panel-head"><h2>Season PIR leaders</h2></div>
    <table class="table"><thead><tr><th>#</th><th class="l">Player</th><th>GP</th><th>Min</th><th>PIR</th></tr></thead><tbody>${rows}</tbody></table>
    <p class="panel-note">Per game, among players with at least half of the possible games played. Players on the injury report are flagged.</p>
  </section>`;
}

function renderFantasy() {
  return `<div class="layout"><div class="main">${injuryPanel()}</div><aside class="rail">${performersPanel()}${leadersPanel()}</aside></div>`;
}

function renderSports() {
  const active = SPORT_TABS.some((t) => t.id === state.sub.sports) ? state.sub.sports : "euroleague";
  const nav = subnav(SPORT_TABS, active, "sports");
  const tab = SPORT_TABS.find((t) => t.id === active);
  return nav + (tab.id === "fantasy" ? renderFantasy() : renderLeague(tab));
}

/* ================================================================ render */

function render() {
  if (!state.meta) return;
  renderMasthead();
  renderTabs();
  const view = $("#view");
  const focused = document.activeElement?.id;
  const caret = focused === "inj-search" ? document.activeElement.selectionStart : null;
  view.innerHTML = state.tab === "sports" ? renderSports() : renderNewsSection(state.tab);
  if (focused === "inj-search") {
    const el = $("#inj-search");
    el.focus();
    el.setSelectionRange(caret, caret);
  }
}

/* ================================================================ events */

document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-action]");
  if (!el) return;
  const { action, id } = el.dataset;
  if (action === "tab") go(id);
  else if (action === "sub") go(el.dataset.tab, id);
  else if (action === "round") (state.round[el.dataset.league] = id), render();
  else if (action === "group") (state.group[el.dataset.league] = Number(id)), render();
  else if (action === "perf") (state.perfRound = id), render();
  else if (action === "inj") {
    state.injFilter = id;
    store.set("wn.injFilter", id);
    render();
  } else if (action === "refresh") refresh();
});

document.addEventListener("input", (e) => {
  if (e.target.id !== "inj-search") return;
  state.injQuery = e.target.value;
  $("#inj-list").innerHTML = injuryList();
});

document.addEventListener("keydown", (e) => {
  if (e.metaKey || e.ctrlKey || e.altKey || e.target.matches("input, textarea")) return;
  const sections = state.meta?.sections || [];
  const n = Number(e.key);
  if (n >= 1 && n <= sections.length) go(sections[n - 1].id);
  else if (e.key === "r" || e.key === "R") refresh();
});

window.addEventListener("hashchange", () => {
  readHash();
  render();
});

async function refresh() {
  if (state.refreshing) return;
  state.refreshing = true;
  render();
  await loadAll(true);
  state.refreshing = false;
  render();
}

/* ================================================================ boot */

async function boot() {
  initVisit();
  readHash();
  try {
    state.meta = await api("meta");
  } catch (e) {
    $("#view").innerHTML = errorBox("The site", e.message);
    return;
  }
  render();
  await loadAll();

  // Quietly keep things current while the tab is open.
  setInterval(() => document.visibilityState === "visible" && loadAll(), 10 * 60_000);
  setInterval(() => {
    if (document.visibilityState !== "visible") return;
    for (const [lg, L] of Object.entries(state.leagues)) {
      if (L.rounds.some((r) => r.games.some((g) => g.state === "in"))) load("sports", lg);
    }
    renderMasthead(); // keeps "x min ago" and the greeting honest
  }, 60_000);
}

boot();

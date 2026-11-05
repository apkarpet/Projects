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
  { id: "picks", title: "Picks" },
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
  picks: null,
  pick: { round: null, sort: "proj", dir: -1, pos: "all", max: null, q: "", hideOut: true, open: null },
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
    else if (kind === "picks") state.picks = await api(`picks${arg ? "/" + arg : ""}`, fresh);
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
  jobs.push(load("picks", state.pick.round, sportsFresh));
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
  $("#date").textContent = now.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });
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
  if (tab.id === "fantasy") return nav + renderFantasy();
  if (tab.id === "picks") return nav + renderPicks();
  return nav + renderLeague(tab);
}


/* ================================================================ rendering: picks */

const pid = (r) => `${r.key}|${r.team}`;
const fmt = (v, d = 1) => (v == null ? "–" : Number(v).toFixed(d));
const signed = (v, d = 1) => (v > 0 ? `+${v.toFixed(d)}` : v.toFixed(d));

function matchupCell(r) {
  const pct = Math.round((r.dvp - 1) * 100);
  const cls = pct >= 4 ? "up" : pct <= -4 ? "down" : "muted";
  return `<span class="${cls}" title="Opponent ranks #${r.dvp_rank} of 20 for PIR allowed to this position (1 = most generous)">${pct > 0 ? "+" : ""}${pct}%</span>`;
}

function statusFlag(r) {
  if (!r.status) return "";
  return `<span class="flag st-${r.severity ?? 2}">${esc(r.status)}</span>`;
}

function pickLine(r, i, metric) {
  const fixture = `${r.home ? "vs" : "at"} ${esc(r.opp)}`;
  const big = metric === "value" ? `${fmt(r.value, 2)}<small>PIR/cr</small>` : `${fmt(r.proj)}<small>proj</small>`;
  return `<div class="perf">
    <span class="rank">${i + 1}</span>
    <span class="who">${esc(r.name)}<span class="team-code">${esc(r.team)}</span>${statusFlag(r)}</span>
    <span class="pir">${big}</span>
    <span class="line">${fixture}, ${fmt(r.price)} cr${metric === "pop" || metric === "fade" ? `, ${fmt(r.popularity)}% own` : ""}${
      metric === "value" ? `, ${fmt(r.proj)} proj` : ""
    }</span>
  </div>`;
}

function pickList(title, note, keys, by, metric) {
  const rows = keys.map((k) => by.get(k)).filter(Boolean);
  return `<section class="pick-list">
    <h3>${title}</h3>
    <p class="pick-note">${note}</p>
    ${rows.length ? rows.map((r, i) => pickLine(r, i, metric)).join("") : `<p class="empty">Nobody fits this round.</p>`}
  </section>`;
}

function gameBars(r) {
  const games = r.games || [];
  if (!games.length) return `<p class="empty">No games logged yet this season.</p>`;
  const w = 34, gap = 8, h = 120, top = 18, base = h - 22;
  const max = Math.max(30, ...games.map((g) => g.pir), r.proj);
  const y = (v) => base - (Math.max(0, v) / max) * (base - top);
  const bars = games
    .map((g, i) => {
      const x = i * (w + gap);
      const el = g.comp === "EL";
      const label = new Date(g.ts * 1000).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
      return `<g><title>${esc(el ? "EuroLeague" : g.comp)} ${label} vs ${esc(g.opp)}: ${g.pir} PIR in ${g.min} min${g.est ? " (PIR estimated)" : ""}</title>
        <rect x="${x}" y="${y(g.pir)}" width="${w}" height="${Math.max(1, base - y(g.pir))}" rx="2" class="${el ? "bar-el" : "bar-dom"}"></rect>
        <text x="${x + w / 2}" y="${y(g.pir) - 4}" class="bar-val">${g.pir}</text>
        <text x="${x + w / 2}" y="${h - 8}" class="bar-lab">${esc(String(g.opp).slice(0, 3))}</text></g>`;
    })
    .join("");
  const width = games.length * (w + gap) - gap;
  const py = y(r.proj);
  return `<svg class="bars" viewBox="0 -2 ${width + 70} ${h + 2}" width="${width + 70}" height="${h + 2}" role="img" aria-label="Last ${games.length} games PIR">
    ${bars}
    <line x1="0" x2="${width}" y1="${py}" y2="${py}" class="proj-line"></line>
    <text x="${width + 6}" y="${py + 4}" class="proj-lab">Proj ${fmt(r.proj)}</text>
  </svg>
  <p class="legend"><span class="key key-el"></span>EuroLeague <span class="key key-dom"></span>Domestic league or cup <span class="key key-proj"></span>This projection</p>`;
}

function pickDetail(r) {
  const reasons = r.reasons.length ? `<ul class="reasons">${r.reasons.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : `<p class="pick-note">No special factors: a straight read of minutes, rate and matchup.</p>`;
  const facts = [
    ["Projected minutes", fmt(r.minutes)],
    ["PIR per minute", fmt(r.rate, 3)],
    ["Range (±1 sd)", `${fmt(r.floor)} to ${fmt(r.ceil)}`],
    ["Starts", `${r.starts} of ${r.gp}`],
    ["Free throws per 40", fmt(r.fta40)],
    ["Venue factor", `${r.venue > 1 ? "+" : ""}${Math.round((r.venue - 1) * 1000) / 10}%`],
    ["FantasyEdgeIQ projection", fmt(r.feiq_proj)],
  ];
  return `<div class="pick-detail">
    <div class="pd-chart"><h4>Last games</h4>${gameBars(r)}</div>
    <div class="pd-why"><h4>Why ${fmt(r.proj)}</h4>${reasons}
      <dl class="facts">${facts.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join("")}</dl>
    </div>
  </div>`;
}

const PICK_COLS = [
  ["name", "Player", "l"],
  ["opp", "Next", "l"],
  ["price", "Price"],
  ["proj", "Proj"],
  ["value", "PIR/cr"],
  ["minutes", "Min"],
  ["season", "Season"],
  ["l3", "Last 3"],
  ["dom_l3", "Domestic"],
  ["usage", "Shot share"],
  ["dvp", "Matchup"],
  ["popularity", "Owned"],
];

function picksTable() {
  const P = state.picks;
  if (!P) return "";
  const f = state.pick;
  const q = f.q.trim().toLowerCase();
  let rows = P.players.filter(
    (r) =>
      (f.pos === "all" || r.pos === f.pos) &&
      (!f.max || r.price <= f.max + 1e-9) &&
      (!f.hideOut || !(r.severity === 0 || r.proj === 0)) &&
      (!q || r.name.toLowerCase().includes(q) || r.team.toLowerCase().includes(q) || r.opp.toLowerCase().includes(q))
  );
  const k = f.sort;
  rows = rows.sort((a, b) => {
    const va = a[k] ?? -Infinity, vb = b[k] ?? -Infinity;
    return (typeof va === "string" ? va.localeCompare(vb) : va - vb) * f.dir;
  });
  const shown = rows.slice(0, 150);
  const head = PICK_COLS.map(
    ([key, label, align]) =>
      `<th class="${align || ""}" aria-sort="${f.sort === key ? (f.dir > 0 ? "ascending" : "descending") : "none"}"><button type="button" data-action="psort" data-id="${key}">${label}${
        f.sort === key ? (f.dir > 0 ? " ↑" : " ↓") : ""
      }</button></th>`
  ).join("");
  const body = shown
    .map((r) => {
      const id = pid(r);
      const open = f.open === id;
      const chg = r.price_change ? `<span class="${r.price_change > 0 ? "up" : "down"} chg">${signed(r.price_change)}</span>` : "";
      const row = `<tr class="prow${open ? " open" : ""}${(r.severity ?? 3) <= 1 ? " out" : ""}" data-action="popen" data-id="${esc(id)}" tabindex="0" aria-expanded="${open}">
        <td class="l"><span class="strong">${esc(r.name)}</span> <span class="muted">${esc(r.team)} ${r.pos}</span>${statusFlag(r)}</td>
        <td class="l muted">${r.home ? "vs" : "at"} ${esc(r.opp)}</td>
        <td>${fmt(r.price)}${chg}</td>
        <td class="strong">${fmt(r.proj)}</td>
        <td>${fmt(r.value, 2)}</td>
        <td>${fmt(r.minutes)}</td>
        <td>${fmt(r.season)}</td>
        <td>${fmt(r.l3)}</td>
        <td class="muted">${r.dom_l3 == null ? "–" : fmt(r.dom_l3) + (r.dom_est ? "*" : "")}</td>
        <td class="muted">${r.usage == null ? "–" : Math.round(r.usage) + "%"}</td>
        <td>${matchupCell(r)}</td>
        <td class="muted">${fmt(r.popularity)}%</td>
      </tr>`;
      return open ? row + `<tr class="pdrow"><td colspan="${PICK_COLS.length}">${pickDetail(r)}</td></tr>` : row;
    })
    .join("");
  const more = rows.length > shown.length ? `<p class="pick-note">Showing the first 150 of ${rows.length}. Narrow the filters to see the rest.</p>` : "";
  return `<div class="tablewrap"><table class="table ptable"><thead><tr>${head}</tr></thead><tbody>${
    body || `<tr><td colspan="${PICK_COLS.length}" class="l muted">No players match these filters.</td></tr>`
  }</tbody></table></div>${more}`;
}

function backtestPanel(bt) {
  if (!bt?.rounds?.length) return "";
  const s = bt.summary;
  const better = s.model.mae < s.season.mae;
  const rows = bt.rounds
    .map(
      (r) => `<tr><td class="l">Round ${r.round}</td><td class="strong">${fmt(r.model.mae, 2)}</td><td>${fmt(r.season.mae, 2)}</td><td>${fmt(r.last3.mae, 2)}</td><td class="strong">${fmt(
        r.model.top20
      )}</td><td>${fmt(r.season.top20)}</td><td>${fmt(r.last3.top20)}</td></tr>`
    )
    .join("");
  return `<section class="group">
    <div class="group-head"><h2 class="group-title">How accurate is this?</h2></div>
    <p class="prose">Each finished round was replayed using only what was known before tip-off, then compared with what actually happened.
    The model's average miss is <strong>${fmt(s.model.mae, 2)} PIR</strong> per player, against ${fmt(s.season.mae, 2)} for simply using the season average
    and ${fmt(s.last3.mae, 2)} for the last three games${better ? "" : ", so it is not yet beating the simple baseline"}. Its top 20 projected players went on to average
    <strong>${fmt(s.model.top20)} PIR</strong>.${s.hindsight ? ` For scale: a predictor allowed to see the future, using each player's average over all his other games this season, misses by ${fmt(s.hindsight.mae, 2)}. Most of what is left is single-game luck that no model can see coming, so treat the range column seriously.` : " Single games are noisy: treat the range column seriously."}</p>
    <div class="tablewrap"><table class="table bt named">
      <thead><tr><th class="l">Round</th><th>Model miss</th><th>Season avg miss</th><th>Last 3 miss</th><th>Model top 20</th><th>Season top 20</th><th>Last 3 top 20</th></tr></thead>
      <tbody>${rows}</tbody>
    </table></div>
    <p class="pick-note">Miss is the mean absolute error in PIR. "Top 20" is the average actual PIR of each method's 20 highest projections. Injuries are not replayed, so live projections should do a little better.</p>
  </section>`;
}

function coachPanel(coaches) {
  if (!coaches?.length) return "";
  const rows = coaches
    .slice(0, 8)
    .map(
      (c) => `<tr><td class="l"><span class="strong">${esc(c.name)}</span> <span class="muted">${esc(c.team)}</span></td><td class="l muted">${c.home ? "vs" : "at"} ${esc(c.opp)}</td><td>${fmt(
        c.price
      )}</td><td class="strong">${c.win}%</td><td class="muted">${fmt(c.popularity)}%</td></tr>`
    )
    .join("");
  return `<section class="panel">
    <div class="panel-head"><h2>Coaches</h2></div>
    <table class="table named"><thead><tr><th class="l">Coach</th><th class="l">Next</th><th>Price</th><th>Win</th><th>Owned</th></tr></thead><tbody>${rows}</tbody></table>
    <p class="panel-note">Coaches score on results, so they are ranked by win chance from this season's point margins plus home court.</p>
  </section>`;
}

function renderPicks() {
  const P = state.picks;
  if (!P) {
    const err = state.errors[`picks:${state.pick.round}`] || state.errors.picks;
    return `<div class="picks">${err ? errorBox("Pick suggestions", err) : `<p class="pick-note">Crunching every box score of the season. The first load takes a few seconds.</p>${skeleton(8)}`}</div>`;
  }
  const by = new Map(P.players.map((r) => [pid(r), r]));
  const prices = P.players.map((r) => r.price);
  const maxPrice = Math.max(...prices);
  if (state.pick.max == null) state.pick.max = maxPrice;
  const lock = P.lock ? new Date(P.lock * 1000).toLocaleString("en-GB", { weekday: "long", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "";
  const roundSwitch = P.rounds.length > 1 ? seg("pround", P.rounds.map((r) => ({ key: r, label: `Round ${r}` })), P.round) : "";
  const posSeg = seg("ppos", [{ key: "all", label: "All" }, { key: "G", label: "Guards" }, { key: "F", label: "Forwards" }, { key: "C", label: "Centers" }], state.pick.pos);
  const src = P.sources;
  return `<div class="picks">
    <div class="picks-head">
      <div>
        <h2 class="picks-title">Round ${P.round} picks</h2>
        <p class="picks-sub">${P.round === P.next_round ? "Lineups lock" : "First tip-off"} ${esc(lock)}. Projected PIR for each player's next EuroLeague game, against his price in credits.</p>
      </div>
      ${roundSwitch}
    </div>

    <div class="pick-lists">
      ${pickList("Top projected", "Most PIR expected, whatever the price.", P.lists.top, by, "proj")}
      ${pickList("Best value", "Most projected PIR per credit (9+ PIR).", P.lists.value, by, "value")}
      ${pickList("Differentials", "12+ PIR projected, owned by under 8% of managers.", P.lists.differentials, by, "pop")}
      ${pickList("Fades", "Popular picks that are out, doubtful or poor value this round.", P.lists.fades, by, "fade")}
    </div>

    <section class="group">
      <div class="group-head"><h2 class="group-title">All players</h2></div>
      <div class="pick-tools">
        ${posSeg}
        <label class="range">Max price <input id="pick-max" type="range" min="4" max="${maxPrice}" step="0.1" value="${state.pick.max}"> <span id="pick-max-label">${fmt(
    state.pick.max
  )} cr</span></label>
        <label class="check"><input id="pick-out" type="checkbox" ${state.pick.hideOut ? "checked" : ""}> Hide players ruled out</label>
        <input class="search" id="pick-q" type="search" placeholder="Find a player, team or opponent" value="${esc(state.pick.q)}" aria-label="Find a player, team or opponent">
      </div>
      <div id="picks-table">${picksTable()}</div>
      <p class="pick-note">Select a player to see his recent games and the reasons behind his projection. Matchup is how much more (or less) PIR the opponent allows to his position than the league average. Domestic values marked * use PIR estimated without fouls.</p>
    </section>

    <div class="layout picks-bottom">
      <div class="main">${backtestPanel(P.backtest)}
        <section class="group">
          <div class="group-head"><h2 class="group-title">How the projection works</h2></div>
          <p class="prose">Projected PIR = projected minutes × PIR per minute × matchup × home or away × availability.
          Minutes come from recent EuroLeague games (the latest count most), plus minutes inherited when a teammate in the rotation has just been ruled out.
          PIR per minute starts from last season's rate and is updated with every EuroLeague minute this season; domestic games count 30% as much.
          The result is scaled by 0.9 because PIR is lopsided: a few huge games pull the average above what a typical night looks like.
          Matchup compares the PIR the opponent allows to guards, forwards or centers with the league average, shrunk towards average while samples are small.
          Doubtful players are scaled to 40%, uncertain ones to 75%, and players ruled out drop to zero.</p>
          <p class="pick-note">Sources: EuroLeague box scores (${src.games} games), domestic box scores and official-game prices from FantasyEdgeIQ (domestic data from ${esc(src.domestic || "n/a")}, prices checked ${
    src.prices ? clock(src.prices) : "n/a"
  }), injuries from BasketNews${src.injuries ? ` (updated ${dayStamp(src.injuries)})` : ""}.</p>
        </section>
      </div>
      <aside class="rail">${coachPanel(P.coaches)}</aside>
    </div>
  </div>`;
}

/* ================================================================ render */

function render() {
  if (!state.meta) return;
  renderMasthead();
  renderTabs();
  const view = $("#view");
  const focused = document.activeElement?.id;
  const caret = focused === "inj-search" || focused === "pick-q" ? document.activeElement.selectionStart : null;
  view.innerHTML = state.tab === "sports" ? renderSports() : renderNewsSection(state.tab);
  if (focused === "inj-search" || focused === "pick-q") {
    const el = $(`#${focused}`);
    if (el) {
      el.focus();
      el.setSelectionRange(caret, caret);
    }
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
  else if (action === "pround") {
    state.pick.round = id;
    state.pick.open = null;
    state.picks = null;
    render();
    load("picks", id);
  } else if (action === "psort") {
    state.pick.dir = state.pick.sort === id ? -state.pick.dir : id === "name" || id === "price" ? 1 : -1;
    state.pick.sort = id;
    $("#picks-table").innerHTML = picksTable();
  } else if (action === "ppos") {
    state.pick.pos = id;
    render();
  } else if (action === "popen") {
    state.pick.open = state.pick.open === id ? null : id;
    $("#picks-table").innerHTML = picksTable();
  }
});

document.addEventListener("keydown", (e) => {
  if ((e.key === "Enter" || e.key === " ") && e.target.matches("tr[data-action='popen']")) {
    e.preventDefault();
    e.target.click();
  }
});

document.addEventListener("input", (e) => {
  const t = e.target;
  if (t.id === "pick-q" || t.id === "pick-max" || t.id === "pick-out") {
    if (t.id === "pick-q") state.pick.q = t.value;
    if (t.id === "pick-max") {
      state.pick.max = Number(t.value);
      $("#pick-max-label").textContent = `${state.pick.max.toFixed(1)} cr`;
    }
    if (t.id === "pick-out") state.pick.hideOut = t.checked;
    $("#picks-table").innerHTML = picksTable();
    return;
  }
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

/* Split the nameplate into letters so it can ink in one by one. */
function setupNameplate() {
  const el = $("#nameplate");
  const text = el.textContent.trim();
  el.setAttribute("aria-label", text);
  el.innerHTML = [...text]
    .map((c, i) => (c === " " ? `<span class="sp" aria-hidden="true"></span>` : `<span class="ch" aria-hidden="true" style="--i:${i}">${esc(c)}</span>`))
    .join("");
}

async function boot() {
  setupNameplate();
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

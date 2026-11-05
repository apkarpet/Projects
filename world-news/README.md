# World News

A personal morning news site on `http://localhost:8420`. It has three sections:

- **Work:** AI and models, big tech, chips and hardware, with Hacker News and Lobsters alongside.
- **Sports:** EuroLeague, NBA and the Greek league, each with scores, standings and news, plus a **Fantasy** tab: the BasketNews injury report, top PIR per round and season PIR leaders. Injured players are flagged in the PIR lists.
- **Picks** (under Sports): EuroLeague Fantasy Challenge suggestions for the next round, using the official scoring (PIR, +10% when the team wins, captain ×2). Every player gets expected fantasy points from projected minutes × PIR per minute × matchup × venue × injury status × win chance, which is divided by his official price. The page has captain picks, top projected, best value, differentials and fades lists, coaches by win chance, a sortable table of every player with reasons and team ratings, a backtest against simple baselines and a hindsight noise floor, and a live track record. Projections are saved before each lineup lock in `~/.local/share/world-news/tracking/` and scored after the round.
- **Other:** world, US politics, economy, Greece and Europe, and science, with a markets panel.

Stories published since your last visit get a dot, and links you have opened fade.

## Run

```sh
news            # start in the background if needed, then open the browser
news stop       # stop it
news restart    # after editing Python code
news logs       # follow the server log
news fg         # run in the foreground
```

`news` is a symlink from `~/.local/bin/news` to `bin/news`. It needs only Python 3.11+ and its standard library; there is nothing to install.

In the browser, press `1` `2` `3` to switch sections and `R` to refresh.

## Change topics

Everything lives in `config.json`, and the server reloads it automatically. A topic is a list of feeds:

```json
{"rss": "https://example.com/feed.xml", "name": "Example", "cap": 3}
{"google": "search terms", "sources": "tech", "max": 12}
{"google_topic": "BUSINESS", "sources": "news"}
```

- `sources` keeps Google News results from the outlets in that `source_lists` entry only. This is what stops low-quality results from getting in.
- `match` (regex) keeps only matching titles. `exclude` on a topic, or `exclude_titles` globally, drops matching titles.
- `cap` limits how many stories one outlet can have in a topic.
- `placement: "rail"` puts a topic in the side column.
- `favorite_teams`, e.g. `["Panathinaikos"]`, highlights those teams in scores and standings.

## Data sources

| Data | Source |
| --- | --- |
| News | Publisher RSS feeds, Google News (filtered), HN Algolia API |
| EuroLeague scores, standings, box scores, PIR | Official EuroLeague feeds |
| NBA scores, standings, news | ESPN public API |
| Greek league scores and standings | esake.gr (Greek team names are translated) |
| Injury report | BasketNews "EuroLeague Injury Report (updated daily)" |
| Fantasy prices, popularity, domestic box scores | FantasyEdgeIQ public CSV and domestic-competitions page |
| Markets | CNBC quotes |

Responses are cached in `~/.cache/world-news/` for 15 minutes for news, 10 minutes for scores (1 minute while a game is live) and 30 minutes for fantasy data. Finished box scores are cached for good. If a source is down, the last good copy is served.

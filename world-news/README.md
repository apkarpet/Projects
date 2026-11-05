# Fantasy

A local EuroLeague Fantasy Challenge assistant with basketball scores, on `http://localhost:8420`.

```sh
fantasy          # starts the server if needed and opens the site
fantasy stop     # stop it
fantasy restart  # after editing Python code
fantasy logs     # follow the server log
```

It needs Python 3.11+ with numpy and scipy. Press `1` to `4` to switch tabs and `R` to refresh.

## Tabs

- **My team**:
  - **Live round:** while a round is being played, your lineup is on a court with real points for finished games (PIR, +10% for a win, then the slot multiplier), live scores, and expected points for games to come. It also suggests morning subs that follow the official rules, including a captain change between gamedays (even after your captain has played, to a starter who has not), and says by which morning to make each one.
  - **Next round:** plan transfers on the court. Click a player to make him captain, swap him or sell him. Suggestions are the mathematically best team for 1 to 4 transfers, or a full rebuild in unlimited rounds, each checked by simulating the round 4,000 times with daily subs.
  - Plan here, make the same moves in the official app, then press Save. The team is kept in `~/.local/share/fantasy/my-team.json`.
- **Picks**:
  - Captain choices, top projected, best value, differentials and fades.
  - The best team from scratch for your budget.
  - A sortable table of every player with the reasons behind his number.
  - How well the model's teams would have scored in past rounds, and a live track record of saved pre-lock projections.
- **Injuries & form**: the BasketNews injury report, top PIR by round and season PIR leaders.
- **Scores**: EuroLeague, NBA and Greek league scores and standings.

## How the numbers are made

Projected PIR = projected minutes × PIR per minute × matchup × home or away × availability.

Expected fantasy points add the 10% win bonus times the team's win chance. Lineups count the captain ×2, the other starters and sixth man ×1, and the bench ×0.5.

| Piece | Where it lives |
| --- | --- |
| Projections and backtests | `newsdesk/picks.py` |
| Exact team optimisation (mixed-integer programming) and the Monte Carlo round simulator | `newsdesk/optimize.py` |

Every model change was tested by replaying finished rounds with only the information available before tip-off. Ideas that did not beat noise were left switched off, and the code comments say which.

## Data

| Data | Source |
| --- | --- |
| Box scores, schedule, standings, PIR | Official EuroLeague feeds |
| Official-game prices, popularity, domestic box scores | FantasyEdgeIQ public CSV and pages |
| Injury report | BasketNews "EuroLeague Injury Report (updated daily)" |
| NBA and Greek league scores | ESPN public API, esake.gr |

Kept in `~/.local/share/fantasy/`:

- `tracking/`: pre-lock projections for each round
- `prices.jsonl`: one price snapshot a day
- `my-team.json`: your team

Caches are in `~/.cache/fantasy/`.

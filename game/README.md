# game/ (Student A)

`protocol.py`, `server.py`, `client.py`: A's game, kept exactly as written.

Localhost development:
```bash
python3 server.py
python3 client.py --name P1          # in more terminals: P2, P3 ...
```
For measured experiments, `measurement/game_runner.py` runs these same files and adds the CSV log
(see `docs/CONTRACT.md`, section 4 for the names that must stay stable).

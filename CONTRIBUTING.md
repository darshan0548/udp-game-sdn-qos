# Contributing

## Ground rules

- Each person edits **only their own folder** (`game/`, `sdn/`, `measurement/`).
  Shared files (`README.md`, `docs/`, `report/`) are changed through a pull request.
- Never commit directly to `main`. Work on a branch, open a pull request, get one review.
- Small, frequent commits with clear messages.

## Branches

```
feature/<area>-<short-description>     e.g. feature/game-sequence-numbers
fix/<area>-<short-description>         e.g. fix/sdn-queue-setup
```

## Daily workflow

```bash
git checkout main && git pull
git checkout -b feature/measurement-jitter
# ... work ...
git add measurement/
git commit -m "measurement: add RFC 3550 jitter"
git push -u origin feature/measurement-jitter
# open a Pull Request on GitHub, ask a teammate to review, then Merge
```

## Commit message style

`<area>: <what changed>` in the present tense, e.g.
`game: drop stale packets using sequence numbers`, `sdn: install priority flow for UDP 5000`.

## What not to commit

Logs from experiments (`measurement/logs/*.csv`), generated graphs, `__pycache__`, virtual
environments. Final figures used in the report go in `report/figures/`.

## Integration checkpoints

1. Contract agreed (`docs/CONTRACT.md` merged)
2. Game runs inside Mininet on the basic controller
3. QoS controller working
4. All scenarios run, graphs generated
5. Report and demo

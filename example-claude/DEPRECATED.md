# DEPRECATED — this folder is gone

`example-claude/` was the copy-into-your-project installable bundle (`cp -r ./example-claude ./.claude`). It has been removed.

The four tier agents (Architect, Strategist, Feature Lead, Sub-Agent) and every operational skill now ship as Claude Code plugins, installed through the marketplace instead of copied by hand:

```
/plugin marketplace add .
/plugin install fractal-core@fractal-marketplace
```

See [`README.md`](../README.md) for the full install walkthrough and [`SETUP-CLAUDE-CODE.md`](../SETUP-CLAUDE-CODE.md) for the manual path (no plugin support).

This stub exists only so a link into the old `example-claude/` path fails softly instead of 404ing. No installable content remains here.

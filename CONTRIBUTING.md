# Contributing

Keep `SKILL.md` compatible with both Claude Code and Kimi Code. Shared behavior belongs in the main skill; host-specific frontmatter must remain optional.

Before submitting a change, run:

```bash
npm test
npm pack --dry-run
```

Test installer changes against a temporary `--project` directory: fresh install, rerun without `--force`, then `--force`. Never test by overwriting your active user-level skill.

For behavior changes, run the relevant scenarios in `evals/` with and without the skill in both agents. Keep `package.json`, `SKILL.md` `metadata.version`, and the top `CHANGELOG.md` release at the same version.

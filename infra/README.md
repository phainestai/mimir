# Mimir CDK

**Platform (no secrets):** `eb_live_platform_settings.json` — export from live EB.

**Secrets:** `infra/.env` or repo `.env` (gitignored). See `.env.example`.

```bash
cp infra/.env.example infra/.env   # fill in values

.venv/bin/python infra/scripts/export_eb_live_settings.py
.venv/bin/python infra/scripts/diff_eb_live_vs_cdk.py   # 0 platform diffs

cd infra && cdk deploy --all --require-approval never
```

Then run the app pipeline for Docker deploy.

Migration-only: `-c eb_minimal_import=true` (not for DR).

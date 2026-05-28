# Mimir CDK

Infrastructure as code for Mimir on AWS. **Goal:** `cdk deploy --all` recreates the stack; the GitHub **build-and-deploy** pipeline pushes the Docker app to the idle EB env.

## Stacks

| Stack | Purpose |
|-------|---------|
| `MimirNetwork` | VPC lookup, `mimir-eb` security group, RDS ingress |
| `MimirSes` | SES configuration set + send policy |
| `MimirApp` | EB app, `mimir-prod` / `mimir-idle`, `mimir-ci` IAM, alarms |
| `MimirBackups` | S3 pre-migrate backup bucket |
| `MimirDns` | Route53 CNAME → EB prod CNAME |

Context in `cdk.json` (account, VPC, ACM cert, domain).

## Two sources of truth

| What | Where |
|------|--------|
| EB **platform** settings (VPC, ALB, instance type, non-secret env vars) | `eb_live_platform_settings.json` — exported from live |
| EB **secrets** | `infra/.env` or repo-root `.env` (gitignored) — see `.env.example` |

At synth/deploy, `MimirApp` loads the JSON and merges secrets from env (`stacks/eb_env.py`). Nothing sensitive is committed.

**Refresh platform snapshot** after console changes:

```bash
.venv/bin/python infra/scripts/export_eb_live_settings.py
```

**Verify CDK matches live** (secrets excluded):

```bash
.venv/bin/python infra/scripts/diff_eb_live_vs_cdk.py
```

Expect **0** platform diffs before a full EB-touching deploy.

## Disaster recovery (new region / account)

1. Copy secrets: `cp infra/.env.example infra/.env` and fill in.
2. Deploy infra: `cd infra && cdk deploy --all --require-approval never`
3. Set any remaining EB env vars if needed (pipeline also sets `MIMIR_GIT_REVISION`, etc.).
4. Run **build-and-deploy** (workflow_dispatch) — backup on idle, then image deploy.
5. `make swap` when ready to promote.

Subnet/SG IDs in the JSON are for the current VPC. After network changes in a new account, re-export or edit the snapshot.

## App deploy (routine)

CDK does **not** run on every release. CI does:

1. Build → ECR push  
2. `scripts/deploy-idle.sh` — S3 DB backup, then deploy to **idle** env  
3. Staging smoke on idle CNAME  
4. Human: `make swap` for prod  

## Scripts

| Script | Role |
|--------|------|
| `scripts/export_eb_live_settings.py` | Regenerate `eb_live_platform_settings.json` from AWS |
| `scripts/diff_eb_live_vs_cdk.py` | Compare live EB vs synthesized template |
| `scripts/cfn_import_resources.py` | One-off CFN IMPORT (migration); not routine deploy |

## Tests

```bash
cd infra && ../.venv/bin/python -m pytest tests/ -q
```

## Migration-only context flags

Do **not** use for DR:

| Flag | Effect |
|------|--------|
| `eb_minimal_import=true` | EB envs without `option_settings` (import only) |
| `eb_environments=false` | Omit EB env resources |
| `ci_deploy=false` | Skip CI IAM in template |
| `eb_unhealthy_alarms=legacy` | Single legacy unhealthy alarm |

# Activity: Define Backup & Recovery

**Activity ID**: TBD
**Order**: 15
**Phase**: Operations
**Dependencies**: Predecessor: DTA-05 (Define Data Architecture)

## Description

Define Backup & Recovery

## Guidance

# Define Backup & Recovery

## Objective

Define backup schedule, retention policy, RTO/RPO targets, disaster recovery plan, and data export/import procedures.

---

## Decisions to Make

### 1. Backup Schedule & Retention

- **Backup frequency**: Hourly, daily, weekly, continuous (WAL archiving)
- **Backup type**: Full, incremental, differential
- **Retention policy**: How long are backups kept?
  - Daily backups: keep 7 days
  - Weekly backups: keep 4 weeks
  - Monthly backups: keep 12 months
- **Storage**: Where are backups stored? (S3, GCS, local disk, off-site)
- **Encryption**: Are backups encrypted at rest?

### 2. RTO & RPO Targets

- **RPO (Recovery Point Objective)**: Maximum acceptable data loss
  - e.g., "15 minutes" means we can lose at most 15 minutes of data
- **RTO (Recovery Time Objective)**: Maximum acceptable downtime
  - e.g., "1 hour" means the system must be restored within 1 hour
- These targets drive backup frequency and recovery procedure complexity

### 3. Disaster Recovery Plan

- **Failover**: Automatic or manual?
- **Geo-redundancy**: Multi-region, multi-AZ, single region?
- **Recovery procedure**: Step-by-step restoration from backup
- **DR testing**: How often is the recovery procedure tested?
- **Communication plan**: Who is notified during a disaster?

### 4. Data Export/Import

- **Export formats**: JSON, CSV, SQL dump, custom format
- **Export triggers**: Manual, scheduled, API-driven
- **Import validation**: How is imported data validated?
- **Makefile targets**: `make backup`, `make restore`, `make export-data`

### 5. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `BACKUP_DB`
- `BACKUP_DR`

Report coverage and gaps.

---

## Deliverables

- ✅ **Backup schedule** and retention policy defined
- ✅ **RTO/RPO targets** set with rationale
- ✅ **Disaster recovery plan** documented
- ✅ **Data export/import** procedures defined
- ✅ **Skill coverage** assessed for this domain
- ✅ **Decision recorded** for inclusion in SAO.md (DTA-18)

## Artifacts Produced

- Backup & recovery decision → contributes to `artifacts/sao_document_template.md` § "14. Backup & Recovery"

## Artifacts Consumed

- Data architecture decision from DTA-05
- Infrastructure decision from DTA-09

## Notes

No additional notes.

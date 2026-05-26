#!/usr/bin/env bash
# deploy-idle.sh — deploy a new version to the currently idle EB environment and smoke-test it.
# Does NOT swap the prod CNAME — run "make swap" (promote-prod.sh) after human review.
#
# Required env vars:
#   EB_APP              e.g. mimir
#   EB_ENV_A            e.g. mimir-prod  (one of the two physical envs)
#   EB_ENV_B            e.g. mimir-idle  (the other)
#   EB_BUCKET           S3 bucket for deployment bundles
#   ECR_REGISTRY        e.g. 123456789.dkr.ecr.us-east-1.amazonaws.com
#   IMAGE_SUFFIX        e.g. v0.0.41-abc1234  (tag used when building the ECR image)
#   VERSION_LABEL       e.g. v-v0.0.41-abc1234-r42  (unique EB version label)
#   GIT_REVISION        e.g. v0.0.41  (stored as MIMIR_GIT_REVISION env property on EB)
#   DEPLOY_BUNDLE_PATH  path to the pre-built deploy-bundle.zip

set -euo pipefail

: "${EB_APP:?EB_APP not set}"
: "${EB_ENV_A:?EB_ENV_A not set}"
: "${EB_ENV_B:?EB_ENV_B not set}"
: "${EB_BUCKET:?EB_BUCKET not set}"
: "${ECR_REGISTRY:?ECR_REGISTRY not set}"
: "${IMAGE_SUFFIX:?IMAGE_SUFFIX not set}"
: "${VERSION_LABEL:?VERSION_LABEL not set}"
: "${GIT_REVISION:?GIT_REVISION not set}"
: "${DEPLOY_BUNDLE_PATH:?DEPLOY_BUNDLE_PATH not set}"

# ── 1. Resolve live / idle by CNAME inspection ────────────────────────────────
CNAME_A=$(aws elasticbeanstalk describe-environments \
  --application-name "$EB_APP" \
  --environment-names "$EB_ENV_A" \
  --query 'Environments[0].CNAME' --output text)

if echo "$CNAME_A" | grep -q "mimir-prod"; then
  LIVE_ENV="$EB_ENV_A"
  IDLE_ENV="$EB_ENV_B"
else
  LIVE_ENV="$EB_ENV_B"
  IDLE_ENV="$EB_ENV_A"
fi

echo "Live env:  $LIVE_ENV  (mimir-prod CNAME — traffic is here)"
echo "Idle env:  $IDLE_ENV  ← deploying here"
echo "Label:     $VERSION_LABEL"
echo "Revision:  $GIT_REVISION"
echo "Image:     $ECR_REGISTRY/mimir:$IMAGE_SUFFIX"

# Export for callers / GH Actions
echo "IDLE_ENV=${IDLE_ENV}" >> "${GITHUB_OUTPUT:-/dev/null}" 2>/dev/null || true

# ── 2. Upload bundle and create EB application version ───────────────────────
S3_KEY="mimir/${VERSION_LABEL}/deploy-bundle.zip"
aws s3 cp "$DEPLOY_BUNDLE_PATH" "s3://${EB_BUCKET}/${S3_KEY}" --quiet
echo "Uploaded s3://${EB_BUCKET}/${S3_KEY}"

EXISTS=$(aws elasticbeanstalk describe-application-versions \
  --application-name "$EB_APP" \
  --version-labels "$VERSION_LABEL" \
  --query "length(ApplicationVersions)" --output text)
if [ "${EXISTS}" = "0" ]; then
  aws elasticbeanstalk create-application-version \
    --application-name "$EB_APP" \
    --version-label "$VERSION_LABEL" \
    --source-bundle "S3Bucket=${EB_BUCKET},S3Key=${S3_KEY}" \
    --no-auto-create-application \
    --output text > /dev/null
  echo "Created application version: $VERSION_LABEL"
else
  echo "Version $VERSION_LABEL already exists — reusing."
fi

# ── 3. Deploy to idle env ─────────────────────────────────────────────────────
# Build option-settings array: always set MIMIR_GIT_REVISION; optionally propagate
# GH_BUG_REPORT_TOKEN (GitHub PAT for the in-app Feedback widget → Issues: write).
# Setting it here ensures the env var survives across deploys without manual console edits.
OPTION_SETTINGS="Namespace=aws:elasticbeanstalk:application:environment,OptionName=MIMIR_GIT_REVISION,Value=${GIT_REVISION}"
if [ -n "${GH_BUG_REPORT_TOKEN:-}" ]; then
  OPTION_SETTINGS="${OPTION_SETTINGS} Namespace=aws:elasticbeanstalk:application:environment,OptionName=GITHUB_TOKEN,Value=${GH_BUG_REPORT_TOKEN}"
  echo "GH_BUG_REPORT_TOKEN present — will set GITHUB_TOKEN on idle env"
else
  echo "GH_BUG_REPORT_TOKEN not set — GITHUB_TOKEN will keep its existing EB value"
fi

aws elasticbeanstalk update-environment \
  --application-name "$EB_APP" \
  --environment-name "$IDLE_ENV" \
  --version-label "$VERSION_LABEL" \
  --option-settings ${OPTION_SETTINGS} \
  --output text > /dev/null
echo "Deployment triggered on $IDLE_ENV — waiting..."

for i in $(seq 1 40); do
  STATUS=$(aws elasticbeanstalk describe-environments \
    --application-name "$EB_APP" \
    --environment-names "$IDLE_ENV" \
    --query "Environments[0].Status" --output text)
  HEALTH=$(aws elasticbeanstalk describe-environments \
    --application-name "$EB_APP" \
    --environment-names "$IDLE_ENV" \
    --query "Environments[0].Health" --output text)
  echo "  [${i}/40] Status=${STATUS}  Health=${HEALTH}"
  if [ "${STATUS}" = "Ready" ]; then
    [ "${HEALTH}" = "Red" ] && { echo "Environment health is Red — aborting."; exit 1; }
    break
  fi
  sleep 15
done

# ── 4. Staging smoke test: hit idle CNAME, verify revision ───────────────────
IDLE_CNAME=$(aws elasticbeanstalk describe-environments \
  --application-name "$EB_APP" \
  --environment-names "$IDLE_ENV" \
  --query 'Environments[0].CNAME' --output text)

echo "Smoke testing http://${IDLE_CNAME}/health/ ..."
HTTP_STATUS=$(curl -o /tmp/idle-health.json -s -w "%{http_code}" \
  --max-time 30 --retry 15 --retry-delay 10 --retry-all-errors --retry-connrefused \
  "http://${IDLE_CNAME}/health/")

if [ "$HTTP_STATUS" != "200" ]; then
  echo "Idle smoke test FAILED — HTTP $HTTP_STATUS"
  cat /tmp/idle-health.json || true
  exit 1
fi

ACTUAL_REVISION=$(python3 -c 'import json; print(json.load(open("/tmp/idle-health.json")).get("revision","unknown"))')
echo "Idle /health/ revision: $ACTUAL_REVISION  (expected: $GIT_REVISION)"
if [ "$ACTUAL_REVISION" != "$GIT_REVISION" ]; then
  echo "Smoke test FAILED — revision mismatch."
  exit 1
fi

IDLE_URL="http://${IDLE_CNAME}"
echo "IDLE_URL=${IDLE_URL}" >> "${GITHUB_OUTPUT:-/dev/null}" 2>/dev/null || true
echo ""
echo "IDLE DEPLOY OK — review at $IDLE_URL"
echo "Prod is unchanged. Run 'make swap' to promote."

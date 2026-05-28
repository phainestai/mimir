#!/usr/bin/env bash
# run-eb-backup.sh — SSM SendCommand on idle EB EC2: backup via one-off container.
#
# Uses the newly built ECR image (not the running container) so pre_deploy_backup
# is available on first deploy of this feature.
#
# Required env:
#   EB_APP, IDLE_ENV, GIT_REVISION, S3_BACKUP_BUCKET, ECR_REGISTRY, IMAGE_SUFFIX
#   AWS_REGION (optional, default us-east-1)

set -euo pipefail

: "${EB_APP:?EB_APP not set}"
: "${IDLE_ENV:?IDLE_ENV not set}"
: "${GIT_REVISION:?GIT_REVISION not set}"
: "${S3_BACKUP_BUCKET:?S3_BACKUP_BUCKET not set}"
: "${ECR_REGISTRY:?ECR_REGISTRY not set}"
: "${IMAGE_SUFFIX:?IMAGE_SUFFIX not set}"

AWS_REGION="${AWS_REGION:-us-east-1}"
IMAGE="${ECR_REGISTRY}/mimir:${IMAGE_SUFFIX}"

echo "Pre-deploy backup on ${IDLE_ENV} (revision=${GIT_REVISION}, image=${IMAGE})..."

INSTANCE_IDS=$(aws elasticbeanstalk describe-environment-resources \
  --environment-name "$IDLE_ENV" \
  --query 'EnvironmentResources.Instances[*].Id' \
  --output text)

if [ -z "$INSTANCE_IDS" ] || [ "$INSTANCE_IDS" = "None" ]; then
  echo "ERROR: No EC2 instances found for environment ${IDLE_ENV}" >&2
  exit 1
fi

INSTANCE_ID=$(echo "$INSTANCE_IDS" | awk '{print $1}')
echo "Target instance: ${INSTANCE_ID}"

REMOTE_CMD=$(cat <<EOF
set -euo pipefail
CONTAINER=\$(docker ps --filter "publish=80" --format '{{.ID}}' | head -1)
if [ -z "\$CONTAINER" ]; then
  CONTAINER=\$(docker ps -q | head -1)
fi
if [ -z "\$CONTAINER" ]; then
  echo "ERROR: No running Docker container on EB host" >&2
  docker ps -a >&2 || true
  exit 1
fi
echo "Loading EB environment variables from get-config"
ENV_FILE=\$(mktemp)
if [ -x /opt/elasticbeanstalk/bin/get-config ]; then
  /opt/elasticbeanstalk/bin/get-config environment > "\$ENV_FILE"
else
  echo "ERROR: /opt/elasticbeanstalk/bin/get-config not found on EB host" >&2
  exit 1
fi
{
  echo "S3_BACKUP_BUCKET=${S3_BACKUP_BUCKET}"
  echo "MIMIR_GIT_REVISION=${GIT_REVISION}"
  echo "MIMIR_ENV=prod"
  echo "DJANGO_SETTINGS_MODULE=mimir.settings.prod"
} >> "\$ENV_FILE"
if ! grep -q '^DATABASE_URL=' "\$ENV_FILE"; then
  echo "ERROR: DATABASE_URL missing from EB environment settings" >&2
  exit 1
fi
if ! grep -q '^DJANGO_SECRET_KEY=' "\$ENV_FILE"; then
  echo "ERROR: DJANGO_SECRET_KEY missing from EB environment settings" >&2
  exit 1
fi
echo "Logging in to ECR and pulling ${IMAGE}"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
docker pull ${IMAGE}
echo "Running pre_deploy_backup in one-off container (network=container:\$CONTAINER)"
docker run --rm --network "container:\${CONTAINER}" \\
  --env-file "\$ENV_FILE" \\
  --entrypoint python \\
  ${IMAGE} \\
  manage.py pre_deploy_backup
rm -f "\$ENV_FILE"
EOF
)

PARAMS_FILE=$(mktemp)
export REMOTE_CMD
python3 - <<'PY' > "$PARAMS_FILE"
import json
import os

print(json.dumps({"commands": [os.environ["REMOTE_CMD"]]}))
PY
unset REMOTE_CMD

COMMAND_ID=$(aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --comment "mimir pre-deploy backup ${GIT_REVISION}" \
  --parameters "file://${PARAMS_FILE}" \
  --query 'Command.CommandId' \
  --output text)
rm -f "$PARAMS_FILE"

echo "SSM command id: ${COMMAND_ID}"

for i in $(seq 1 60); do
  STATUS=$(aws ssm get-command-invocation \
    --command-id "$COMMAND_ID" \
    --instance-id "$INSTANCE_ID" \
    --query 'Status' \
    --output text 2>/dev/null || echo "Pending")

  echo "  [${i}/60] SSM status=${STATUS}"

  case "$STATUS" in
    Success)
      aws ssm get-command-invocation \
        --command-id "$COMMAND_ID" \
        --instance-id "$INSTANCE_ID" \
        --query 'StandardOutputContent' \
        --output text
      echo "Pre-deploy backup SSM command succeeded."
      exit 0
      ;;
    Failed|Cancelled|TimedOut)
      echo "ERROR: SSM command ${STATUS}" >&2
      aws ssm get-command-invocation \
        --command-id "$COMMAND_ID" \
        --instance-id "$INSTANCE_ID" \
        --query '[StandardOutputContent, StandardErrorContent]' \
        --output text >&2 || true
      exit 1
      ;;
  esac
  sleep 10
done

echo "ERROR: SSM command timed out waiting for completion" >&2
exit 1

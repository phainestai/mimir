# Activity: Deploy & Verify Cloud Environment

**Activity ID**: TBD
**Order**: 7
**Phase**: Verify
**Dependencies**: Predecessor: DCI-06 (Create Infra GH Workflow)

## Description

Deploy & Verify Cloud Environment

## Guidance

# Deploy & Verify Cloud Environment

## Objective

Run the full infrastructure deployment, verify all AWS resources are operational, and confirm the blue/green switching mechanism works end-to-end. This is the acceptance gate for the DCI workflow.

---

## Process

### 1. Full Deployment

```bash
cd {project}-infra
make deploy   # Deploys VPC → EKS → DNS stacks
```

Expected time: ~20-25 minutes (EKS cluster creation dominates).

### 2. Verify VPC

```bash
# List VPCs
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=*{project}*" \
    --query 'Vpcs[].{ID:VpcId,CIDR:CidrBlock,State:State}' --output table

# Verify subnets (2 public + 2 private)
aws ec2 describe-subnets --filters "Name=vpc-id,Values={vpc-id}" \
    --query 'Subnets[].{AZ:AvailabilityZone,CIDR:CidrBlock,Type:Tags[?Key==`Name`].Value|[0]}' --output table

# Verify NAT Gateway
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values={vpc-id}" \
    --query 'NatGateways[].{State:State,PublicIP:NatGatewayAddresses[0].PublicIp}' --output table
```

### 3. Verify EKS

```bash
# Update kubeconfig
aws eks update-kubeconfig --name {cluster-name} --region {region}

# Nodes
kubectl get nodes -o wide
# Expected: 2 nodes, Status=Ready

# Namespaces
kubectl get ns
# Expected: blue, green (plus default, kube-system, etc.)

# Cluster health
kubectl cluster-info
kubectl get componentstatuses 2>/dev/null || kubectl get --raw /healthz
```

### 4. Verify ECR

```bash
# List repos
aws ecr describe-repositories --query 'repositories[].{Name:repositoryName,URI:repositoryUri}' --output table

# Push test image
aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {account}.dkr.ecr.{region}.amazonaws.com
docker pull nginx:alpine
docker tag nginx:alpine {ecr-uri}:verify-test
docker push {ecr-uri}:verify-test

# Deploy test pod from ECR
kubectl run verify-test --image={ecr-uri}:verify-test -n blue --port=80
kubectl get pods -n blue  # Should show Running
kubectl delete pod verify-test -n blue
```

### 5. Verify DNS & Traffic Switching

```bash
# Check DNS resolution
dig prod.{domain}
dig idle.{domain}

# Show current traffic state
make traffic-status

# Test switch
make traffic-switch
# Verify: prod.{domain} now points to the other environment
dig prod.{domain}

# Test rollback
make traffic-rollback
dig prod.{domain}
# Should be back to original
```

### 6. Verify GH Actions Pipeline

1. Make a trivial change to CDK (e.g., add a tag)
2. Push to `main`
3. Verify GH Actions triggers and deploys successfully
4. Manually trigger `traffic-switch` via GitHub Actions UI
5. Verify approval gate works (requires manual approval for production environment)

### 7. Create Verification Checklist

Document results in `docs/architecture/INFRA_VERIFICATION.md`:

```markdown
# Infrastructure Verification

| Check | Status | Details |
|-------|--------|---------|
| VPC created | ✅ | vpc-xxx, 10.0.0.0/16 |
| Subnets (4) | ✅ | 2 public, 2 private across 2 AZs |
| NAT Gateway | ✅ | Running, EIP assigned |
| EKS cluster | ✅ | v1.29, 2 nodes Ready |
| Blue namespace | ✅ | Created |
| Green namespace | ✅ | Created |
| ECR repo | ✅ | Push/pull verified |
| Route53 zone | ✅ | Zone ID: xxx |
| DNS resolution | ✅ | prod + idle resolving |
| Traffic switch | ✅ | Tested switch + rollback |
| GH Actions deploy | ✅ | Pipeline passing |
| GH Actions switch | ✅ | Approval gate works |
```

### 8. Commit

```bash
git add docs/architecture/INFRA_VERIFICATION.md
git commit -m "docs: add infrastructure verification checklist"
```

---

## Deliverables

- ✅ **All CDK stacks** deployed successfully
- ✅ **VPC** — subnets, NAT, security groups verified
- ✅ **EKS** — nodes Ready, namespaces exist, pods can run
- ✅ **ECR** — push/pull verified
- ✅ **DNS** — prod/idle resolving, switch/rollback tested
- ✅ **GH Actions** — deploy on push, manual switch with approval
- ✅ **`docs/architecture/INFRA_VERIFICATION.md`** — checklist documented

## Artifacts Produced

- `docs/architecture/INFRA_VERIFICATION.md`

## Artifacts Consumed

- All DCI stacks (DCI-03, DCI-04, DCI-05)
- GH Actions workflow (DCI-06)
- Infra Makefile targets

## Notes

This is the gate for DCI completion. All checks must pass before proceeding to DCD. If any check fails, fix the underlying stack and re-verify.

# Activity: Build EKS Cluster & ECR Stack

**Activity ID**: 77
**Order**: 4
**Phase**: Elaboration
**Dependencies**: None

## Description

Build EKS Cluster & ECR Stack

## Guidance

# Build EKS Cluster & ECR Stack

## Objective

Implement the EKS CDK stack with a managed Kubernetes cluster, node group, and ECR container registry. The cluster runs in the private subnets created by VPC stack and is the deployment target for the application.

---

## Process

### 1. Implement `stacks/eks_stack.py`

Use the `aws_cdk_python` and `k8s_eks_deployment` skills for reference patterns.

Key constructs:
- **EKS Cluster** with managed node group (2-3 `t3.medium` nodes)
- **ECR Repository** for application container images
- **OIDC Provider** for IAM Roles for Service Accounts (IRSA)
- **kubectl layer** for CDK to interact with cluster
- **Blue/green namespaces** created on cluster

```python
from aws_cdk import Stack, RemovalPolicy, aws_eks as eks, aws_ec2 as ec2, aws_ecr as ecr, aws_iam as iam
from constructs import Construct

class EksStack(Stack):
    def __init__(self, scope: Construct, id: str, vpc: ec2.Vpc, **kwargs):
        super().__init__(scope, id, **kwargs)

        # EKS Cluster
        self.cluster = eks.Cluster(
            self, "Cluster",
            vpc=vpc,
            version=eks.KubernetesVersion.V1_29,
            default_capacity=0,  # We'll add managed node group explicitly
            endpoint_access=eks.EndpointAccess.PUBLIC_AND_PRIVATE,
        )

        # Managed Node Group
        self.cluster.add_nodegroup_capacity(
            "WorkerNodes",
            instance_types=[ec2.InstanceType("t3.medium")],
            min_size=2,
            max_size=4,
            desired_size=2,
            disk_size=50,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
        )

        # ECR Repository
        self.ecr_repo = ecr.Repository(
            self, "AppRepo",
            repository_name="{project}",
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                ecr.LifecycleRule(max_image_count=20, description="Keep last 20 images")
            ],
        )

        # Create blue/green namespaces
        for ns in ["blue", "green"]:
            self.cluster.add_manifest(
                f"{ns}-namespace",
                {
                    "apiVersion": "v1",
                    "kind": "Namespace",
                    "metadata": {"name": ns},
                },
            )
```

### 2. Configure kubectl Access

After deployment, configure local kubectl:

```bash
aws eks update-kubeconfig --name {cluster-name} --region {region}
kubectl get nodes  # Should show 2 worker nodes
kubectl get ns     # Should show blue and green namespaces
```

### 3. Write CDK Tests

```python
# tests/test_eks_stack.py
import aws_cdk as cdk
from aws_cdk.assertions import Template
from stacks.vpc_stack import VpcStack
from stacks.eks_stack import EksStack

def test_eks_cluster_created():
    app = cdk.App()
    vpc = VpcStack(app, "TestVpc")
    stack = EksStack(app, "TestEks", vpc=vpc.vpc)
    template = Template.from_stack(stack)
    template.resource_count_is("Custom::AWSCDK-EKS-Cluster", 1)

def test_ecr_repo_created():
    app = cdk.App()
    vpc = VpcStack(app, "TestVpc")
    stack = EksStack(app, "TestEks", vpc=vpc.vpc)
    template = Template.from_stack(stack)
    template.resource_count_is("AWS::ECR::Repository", 1)
```

### 4. Deploy & Verify

```bash
make deploy   # Deploys VPC + EKS stacks
```

Verify:
- `kubectl get nodes` — 2 nodes Ready
- `kubectl get ns` — blue and green namespaces exist
- AWS Console: ECR repo created
- `docker login` to ECR works

### 5. Test ECR Push

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {account}.dkr.ecr.{region}.amazonaws.com

# Push a test image
docker pull nginx:alpine
docker tag nginx:alpine {account}.dkr.ecr.{region}.amazonaws.com/{project}:test
docker push {account}.dkr.ecr.{region}.amazonaws.com/{project}:test
```

### 6. Commit

```bash
git add stacks/eks_stack.py tests/test_eks_stack.py
git commit -m "infra: implement EKS cluster with node group, ECR repo, blue/green namespaces"
```

---

## Deliverables

- ✅ **`stacks/eks_stack.py`** implemented with EKS, node group, ECR, namespaces
- ✅ **CDK tests** passing
- ✅ **kubectl configured** and nodes visible
- ✅ **Blue/green namespaces** created
- ✅ **ECR repo** accessible, test push successful

## Agent

None

## Skill

**Title**: K8s in EKS Deployment Patterns
**Capability Domain**: CONTAINER_ORCHESTRATION
**Technology Stack**: Kubernetes + AWS EKS

## Rules

None

## Artifacts Produced

None

## Artifacts Consumed

- **Infra Repo Scaffold** (Template) - Required
- **CDK Stack Templates** (Code) - Required

## Notes

No additional notes.

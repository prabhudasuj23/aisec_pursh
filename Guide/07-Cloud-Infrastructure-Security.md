# Chapter 7: Cloud & Infrastructure Security

> **Goal:** Understand the core cloud security concepts that enterprise AppSec engineers need — shared responsibility, IAM, network security, container/Kubernetes security, and how to audit cloud environments. Modern AppSec requires fluency in cloud platforms because applications live there.

---

## 7.1 The Shared Responsibility Model

Cloud security is a shared responsibility between the cloud provider and the customer. Understanding exactly where the boundary is prevents both over-reliance on the provider and under-securing your own configuration.

### AWS Shared Responsibility Model

```
┌─────────────────────────────────────────────────────────┐
│             CUSTOMER RESPONSIBILITY                      │
│                                                         │
│  Customer data                                          │
│  Platform, Applications, Identity & Access Management   │
│  Operating System (on EC2), Network & Firewall Config   │
│  Client-side data encryption                            │
│  Server-side encryption (key management)                │
│  Network traffic protection                             │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│             AWS RESPONSIBILITY                           │
│                                                         │
│  Compute, Storage, Database, Networking hardware        │
│  AWS Global Infrastructure (Regions, AZs, Edge)        │
│  Physical security of data centers                      │
└─────────────────────────────────────────────────────────┘
```

**The common mistake:** Teams assume "AWS handles security." AWS handles **security OF the cloud** (hardware, physical facilities, global network). Customers handle **security IN the cloud** (their data, their IAM configuration, their S3 bucket permissions, their EC2 security groups).

**Real example:** When a company's S3 bucket is publicly accessible and data is exposed, AWS is not responsible. The customer misconfigured their bucket. AWS provides the tools to prevent it (S3 Block Public Access) — but the customer must use them.

### Service Model Matters

| Service Model | Provider Handles | Customer Handles |
|---|---|---|
| IaaS (EC2, raw VMs) | Hardware, hypervisor | OS, application, networking |
| PaaS (RDS, Lambda, ECS Fargate) | OS, runtime | Application code, configuration |
| SaaS (Salesforce, Gmail) | Everything | Data, access control, configuration |

AppSec engineers deal with all three. When your app uses RDS (PaaS), you do not patch the database OS — AWS does. But you are still responsible for database user permissions, encryption at rest settings, and network access controls.

---

## 7.2 IAM — Identity and Access Management

IAM is the core security control in any cloud environment. Getting IAM right is critical — getting it wrong is how most cloud breaches happen.

### Key IAM Concepts

**Identity:** Who or what is making the request?
- Human users (developers, admins)
- Service accounts / IAM roles (applications, CI/CD pipelines, Lambda functions)

**Authentication:** Proving you are who you claim to be (password, MFA, certificate, OIDC token)

**Authorization:** What are you allowed to do? (IAM policies)

**Principal:** In AWS terminology, the entity that can make API calls (user, role, service)

### IAM Roles vs. IAM Users

**IAM Users** — long-lived identities with static access keys. Use for human console access only.

**IAM Roles** — temporary identities assumed by services. Use for all machine-to-machine access.

```
Application on EC2 needs to read from S3:

BAD:  Give EC2 instance an IAM User's access key stored as environment variable
      → Static key, long-lived, if server is compromised key is stolen

GOOD: Attach an IAM Role to the EC2 instance
      → Application calls AWS SDK → automatically gets temporary credentials
      → Credentials expire every hour
      → If server is compromised, keys expire within an hour
```

### The Principle of Least Privilege for IAM

Every role should have only the permissions it needs to do its job — nothing more.

**Overly permissive policy (BAD):**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "*",         // ALL AWS actions — including IAM admin, billing, delete
    "Resource": "*"        // On ALL resources
  }]
}
```

**Least-privilege policy (GOOD):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::my-app-data-bucket/*"
      // Only read/write to THIS specific bucket, not all S3
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789:secret:my-app/*"
      // Only this app's secrets, not all secrets
    }
  ]
}
```

### IAM Security Best Practices

1. **MFA for all human users** — especially the root account (lock it away, never use it daily)
2. **No long-lived access keys for services** — use IAM roles
3. **Rotate all access keys quarterly** (for cases where they must exist)
4. **Use IAM Access Analyzer** — automatically identifies policies that grant external access
5. **Use Service Control Policies (SCPs) in AWS Organizations** — organization-wide restrictions that even admin roles cannot override:
   ```json
   // Prevent creating resources outside approved regions
   {
     "Effect": "Deny",
     "Action": "*",
     "Resource": "*",
     "Condition": {
       "StringNotEquals": {
         "aws:RequestedRegion": ["us-east-1", "us-west-2"]
       }
     }
   }
   ```

---

## 7.3 Network Security

### VPC Architecture

A **VPC (Virtual Private Cloud)** is your private network in the cloud. Design it with security zones:

```
Internet
    │
    ▼
┌──────────────────────────────────────────┐
│ Public Subnet                            │
│ (Internet-reachable)                     │
│  - Load Balancer (ALB/NLB)               │
│  - NAT Gateway (for outbound from privat)│
└──────────────────────┬───────────────────┘
                       │ Private communication only
                       ▼
┌──────────────────────────────────────────┐
│ Private Subnet (Application Tier)        │
│ (No direct internet access)              │
│  - ECS tasks / EC2 instances             │
│  - Lambda functions                      │
└──────────────────────┬───────────────────┘
                       │ Private communication only
                       ▼
┌──────────────────────────────────────────┐
│ Private Subnet (Data Tier)               │
│ (Most restricted)                        │
│  - RDS databases                         │
│  - ElastiCache                           │
│  - OpenSearch                            │
└──────────────────────────────────────────┘
```

**Key rules:**
- Only the load balancer lives in the public subnet
- Application servers have no public IP — only accessible via load balancer
- Databases have no public IP — only accessible from the application subnet
- All communication is TLS encrypted, even between private subnets

### Security Groups

Security groups are instance-level firewalls. Apply least privilege:

```hcl
# ALB Security Group — accepts HTTPS from internet
resource "aws_security_group" "alb" {
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Internet
  }
  egress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]  # Only to app tier
  }
}

# App Security Group — only accepts from ALB, not internet
resource "aws_security_group" "app" {
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]  # Only from ALB
  }
}

# DB Security Group — only accepts from app tier
resource "aws_security_group" "db" {
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]  # Only from app tier
  }
}
```

### Web Application Firewall (WAF)

A WAF sits in front of your application and inspects HTTP traffic. It blocks:
- SQL injection attempts
- XSS payloads
- Known attack tools (scanning signatures)
- Rate-limit abusive IPs
- Log4Shell and similar one-line exploit payloads

**AWS WAF example rule:**
```json
{
  "Name": "BlockSQLInjection",
  "Priority": 1,
  "Action": {"Block": {}},
  "Statement": {
    "SqliMatchStatement": {
      "FieldToMatch": {"AllQueryArguments": {}},
      "TextTransformations": [{"Priority": 1, "Type": "URL_DECODE"}]
    }
  }
}
```

**Important:** WAF is defense in depth, not a replacement for secure code. A WAF can be bypassed. Fix the code; WAF just adds a layer.

---

## 7.4 Container Security in Depth

### The Container Security Threat Model

Containers provide process isolation, but they share the host OS kernel. If an attacker escapes a container, they may access the host and all other containers.

**Container attack paths:**
1. Vulnerable application → remote code execution in container
2. Container escape → host OS compromise
3. Over-privileged container → access to host resources (mounted volumes, host network)
4. Image with backdoor → malicious code running from day 1

### Container Hardening Checklist

**Dockerfile:**
- [ ] Use minimal base image (distroless, alpine, -slim variants)
- [ ] Run as non-root user
- [ ] Read-only filesystem (`--read-only` in docker run)
- [ ] No secrets in image (use runtime secrets injection)
- [ ] Multi-stage build (build tooling not in production image)

**Runtime:**
- [ ] Drop all capabilities, add only what is needed (`--cap-drop ALL --cap-add NET_BIND_SERVICE`)
- [ ] No privileged mode (`--privileged` is a security disaster — gives container root on host)
- [ ] No host network or host PID (`--network=host` breaks container isolation)
- [ ] Resource limits (CPU, memory) to prevent DoS
- [ ] Read-only root filesystem

```bash
# Hardened docker run example
docker run \
  --read-only \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  --security-opt no-new-privileges:true \
  --user 1000:1000 \
  --memory 512m \
  --cpus 0.5 \
  myapp:v1.2.3
```

---

## 7.5 Kubernetes Security

Kubernetes (K8s) is the dominant container orchestration platform in enterprises. It has many security configuration points.

### Kubernetes Security Layers

```
Cluster Security (network, nodes, etcd encryption)
    ↓
Authentication (who can talk to the API server?)
    ↓
Authorization (RBAC — what can they do?)
    ↓
Admission Control (policy enforcement before objects are created)
    ↓
Pod Security (what can the pod do at runtime?)
    ↓
Network Policies (which pods can talk to which pods?)
```

### RBAC (Role-Based Access Control)

Kubernetes RBAC controls who can do what to which Kubernetes resources.

```yaml
# Least-privilege RBAC for an application service account
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp
  namespace: production

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: myapp-role
  namespace: production
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list"]    # Read configmaps only
  - apiGroups: [""]
    resources: ["secrets"]
    resourceNames: ["myapp-secrets"]  # Only THIS specific secret
    verbs: ["get"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: myapp-binding
  namespace: production
subjects:
  - kind: ServiceAccount
    name: myapp
roleRef:
  kind: Role
  name: myapp-role
  apiGroup: rbac.authorization.k8s.io
```

### Pod Security Standards

```yaml
# Pod with security settings
apiVersion: v1
kind: Pod
spec:
  securityContext:
    runAsNonRoot: true           # Pod must run as non-root
    runAsUser: 1000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault       # Apply seccomp syscall filtering
  
  containers:
    - name: myapp
      image: myapp:v1.2.3
      securityContext:
        allowPrivilegeEscalation: false   # Cannot gain more privileges
        readOnlyRootFilesystem: true      # Filesystem is read-only
        capabilities:
          drop: ["ALL"]                   # Drop all Linux capabilities
      
      resources:
        limits:
          memory: "512Mi"
          cpu: "500m"
        requests:
          memory: "256Mi"
          cpu: "250m"
```

### Network Policies

By default, all pods in a Kubernetes cluster can communicate with each other. Network policies restrict this:

```yaml
# Only allow ingress to the myapp pod from the frontend namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-myapp
  namespace: backend
spec:
  podSelector:
    matchLabels:
      app: myapp
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: frontend
      ports:
        - protocol: TCP
          port: 8000
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: database
      ports:
        - protocol: TCP
          port: 5432
```

**Zero-trust Kubernetes networking:** Default deny all ingress and egress, then add explicit allow rules for only the communication paths that are needed.

### Kubernetes Security Scanning

**kube-bench:** Tests a Kubernetes cluster against CIS Kubernetes Benchmark
```bash
kube-bench run --targets master,node,etcd,policies
```

**Trivy for Kubernetes manifests:**
```bash
trivy k8s --report=all cluster
```

**Kubesec:** Scores Kubernetes deployment YAML for security:
```bash
kubesec scan deployment.yaml
```

---

## 7.6 Logging, Monitoring, and Detecting Attacks

### What to Log in Cloud Environments

**AWS CloudTrail:** Every API call made to AWS (who called what, from where, when). Essential for security investigations.

**VPC Flow Logs:** Network traffic logs at the network interface level. Shows source IP, destination IP, port, protocol, bytes transferred.

**Application logs:** Authentication events, authorization failures, sensitive data access.

**CloudWatch Container Insights / ECS logs:** Container stdout/stderr, task lifecycle events.

### What to Alert On

| Event | Alert Level | Why |
|---|---|---|
| Root account login | Critical | Root should never be used; any login is suspicious |
| MFA disabled for any user | High | Weakening authentication |
| IAM policy wildcard `*:*` added | Critical | Privilege escalation |
| S3 bucket ACL changed to public | Critical | Potential data exposure |
| Security group opens port 22/3389 to 0.0.0.0/0 | High | SSH/RDP exposed to internet |
| Unusual API calls from new region | High | Credential theft |
| GuardDuty finding: CryptoCurrency mining | High | EC2 compromised, being used for mining |
| Multiple failed login attempts | Medium | Brute force or credential stuffing |

### AWS Security Services

**GuardDuty:** Managed threat detection. Analyzes CloudTrail, VPC Flow Logs, DNS logs to detect:
- Cryptocurrency mining
- Unusual API calls (new region, new user agent)
- Port scanning from EC2 instances
- Known malicious IPs communicating with your resources
- Account compromise indicators

**AWS Security Hub:** Aggregates findings from GuardDuty, Inspector, Macie, IAM Access Analyzer, Firewall Manager into one place with compliance scoring against CIS AWS Benchmark.

**Amazon Inspector:** Continuously scans EC2 instances and ECR container images for CVEs.

**Amazon Macie:** Uses ML to discover and classify sensitive data (PII, credit card numbers, credentials) in S3 buckets.

**IAM Access Analyzer:** Identifies IAM policies that grant access to external principals — resources accessible outside your AWS account.

---

## 7.7 Cloud Security Configuration Review

As an AppSec engineer, you will be asked to conduct or participate in cloud security reviews. Here is a structured approach:

### AWS Security Review Checklist

**IAM:**
- [ ] Root account has MFA; no access keys for root
- [ ] All IAM users have MFA
- [ ] No active access keys older than 90 days
- [ ] No IAM policies with `*:*` except service control boundaries
- [ ] IAM Access Analyzer enabled; no external access findings

**Networking:**
- [ ] No security group rule allows 0.0.0.0/0 on SSH (22) or RDP (3389)
- [ ] No EC2 instances with public IPs in production (use ALB instead)
- [ ] VPC Flow Logs enabled
- [ ] No unrestricted outbound rules in production security groups

**Storage:**
- [ ] All S3 buckets have Block Public Access enabled (account-level setting)
- [ ] S3 bucket encryption enabled (SSE-S3 or SSE-KMS)
- [ ] S3 versioning enabled for important buckets
- [ ] No public S3 bucket ACLs or policies

**Encryption:**
- [ ] RDS encryption at rest enabled
- [ ] EBS volumes encrypted
- [ ] KMS CMK (Customer Managed Key) used for sensitive data (not AWS-managed keys)
- [ ] KMS key rotation enabled

**Logging and Monitoring:**
- [ ] CloudTrail enabled in all regions; log file validation enabled
- [ ] GuardDuty enabled in all regions
- [ ] AWS Config enabled with conformance packs
- [ ] Security Hub enabled; score > 80%

**Compute:**
- [ ] No hardcoded credentials in EC2 user data
- [ ] Systems Manager (SSM) used for remote access instead of SSH
- [ ] ECR images scanned; no critical/high CVEs in production images

---

## 7.8 Real-World Case Study: Capital One Breach (2019)

**What happened:** A former AWS employee exploited a misconfigured WAF to steal data from Capital One's AWS environment. 100 million US and Canadian customers' data was exposed.

**Attack chain:**
1. **SSRF via misconfigured WAF:** The attacker sent a request that caused the WAF to make an HTTP request on behalf of the server. The WAF ran on an EC2 instance with an attached IAM role.

2. **AWS metadata service abuse:** The attacker used the SSRF to call:
   ```
   http://169.254.169.254/latest/meta-data/iam/security-credentials/
   ```
   This returned the IAM role credentials for the WAF instance.

3. **Over-privileged IAM role:** The WAF instance's IAM role had excessive S3 permissions — it could list and download from any S3 bucket in the account (not just the ones it needed).

4. **Data exfiltration:** The attacker used the stolen credentials to list and download 100 million records from S3 buckets containing credit applications.

**What went wrong:**

| Control | Failure | Prevention |
|---|---|---|
| SSRF prevention | WAF could make requests to 169.254.169.254 | Block IMDS in security group (or use IMDSv2 which requires a session token) |
| IAM least privilege | WAF role could access ALL S3 buckets | Restrict role to only buckets WAF needed to read from |
| Detection | No alert on large-scale S3 data access | CloudWatch alarm on S3 GetObject volume anomaly; Macie PII detection |
| Network egress | No egress filtering | WAF should not be able to make outbound calls to the IMDS without specific routes |

**The fix:**
- **IMDSv2:** Requires a session token to use the instance metadata service. SSRF cannot get a session token because it is a single HTTP call — IMDSv2 requires a PUT then a GET. Prevents SSRF → metadata → credential theft.
- **IAM least privilege:** Each service gets a role that can only access what it needs.
- **VPC endpoint for S3:** Route S3 traffic through a VPC endpoint with bucket-level restrictions.
- **Macie:** Would have detected the S3 download pattern and the PII data.

---

## Chapter 7 Summary

| Topic | Key Takeaway |
|---|---|
| Shared responsibility | Cloud provider secures the infrastructure; you secure your configuration and data |
| IAM | Roles over users; least privilege; OIDC for CI/CD; MFA everywhere |
| Network | Public subnet = load balancer only; app and DB in private subnets; security groups by role |
| WAF | Defense in depth layer; does not replace secure code |
| Container security | Non-root, minimal image, read-only filesystem, no privileged mode |
| Kubernetes | RBAC, pod security contexts, network policies, admission controllers |
| Logging | CloudTrail + GuardDuty + Security Hub are minimum for AWS |
| Capital One | SSRF + over-privileged IAM = data breach; IMDSv2 + least privilege = prevention |

---

*Next: [Chapter 8 — Security Reviews, Audits & Governance](08-Reviews-Audits-Governance.md)*

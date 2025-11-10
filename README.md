# Kubernetes on Hetzner Cloud with Ansible

Automated Kubernetes cluster deployment on Hetzner Cloud infrastructure.

## Quick Start

```bash
# 1. Install dependencies
python3.11 -m pip install --user ansible
ansible-galaxy collection install hetzner.hcloud
python3.11 -m pip install --user hcloud

# 2. Configure
export HCLOUD_TOKEN="hcloud_xxxxxxxxxxxxx"
# Edit provision.yml: Update ssh_key_name to match your Hetzner SSH key

# 3. Deploy
cd ansible
ansible-playbook provision.yml                    # Create servers (~2 min)
ansible-playbook -i inventory.ini playbook.yml    # Configure K8s (~10 min)

# 4. Access
ssh root@<master-ip>  # IP from inventory.ini
kubectl get nodes
```

## What You Get

- 1× Master node (cx32: 4 vCPU, 8GB RAM) 
- 1× Worker node (cx22: 2 vCPU, 4GB RAM)
- Kubernetes v1.30 with Flannel CNI
- Ready to use in ~15 minutes
- Cost: ~€21/month (~$0.03/hour)

## Requirements

- Python 3.11+
- Hetzner Cloud account with API token
- SSH key uploaded to Hetzner Cloud

## Common Commands

```bash
# Check cluster status (via Ansible)
ansible master -i inventory.ini -m shell -a "kubectl get nodes"

# Destroy everything
ansible-playbook destroy.yml
```

## Configuration

Edit `provision.yml` to customize:

```yaml
server_type_master: cx32    # Master size
server_type_worker: cx22    # Worker size
worker_count: 1             # Number of workers
location: hel1              # Datacenter (hel1, fsn1, nbg1, ash)
```

## Structure

```
ansible/
├── provision.yml          # Creates Hetzner servers
├── playbook.yml           # Configures Kubernetes
├── destroy.yml            # Deletes everything
├── inventory.ini          # Auto-generated server IPs
└── roles/
    ├── common/            # System setup
    ├── containerd/        # Container runtime
    ├── kubernetes-master/ # Control plane
    └── kubernetes-worker/ # Worker nodes
```

## Troubleshooting

**Server limit reached**: New Hetzner accounts have 3-server limit. Reduce `worker_count: 1` or contact support.

**Python error**: Requires Python 3.9+. Use Python 3.11: `python3.11 -m pip install --user ansible`

**SSH fails**: Wait 1-2 min for servers to boot, then retry playbook.

## Learning Path

This repository contains a structured learning path for Kubernetes:

### Phase 1: Understanding Kubernetes
**File:** `01-understand-k8s.md`

Learn the fundamentals:
- What is Kubernetes and why use it
- Core concepts: Pods, Deployments, Services
- Architecture overview
- When to use Kubernetes

### Phase 2: Cluster Setup with Ansible
**Directory:** `ansible/`
**Guides:** `02-using-ansible.md`

Automated cluster deployment:
- Provision Hetzner Cloud servers via API
- Install and configure Kubernetes
- Set up networking with Flannel
- Ready-to-use cluster in 15 minutes

### Phase 3: Deploying Applications
**File:** `03-deploying-applications.md`
**Directory:** `workloads/`

Hands-on exercises deploying real apps:
- Pods and Deployments
- Services (ClusterIP, NodePort)
- Ingress controller and routing
- Real applications: Redis, PostgreSQL, WordPress, Grafana
- ConfigMaps, Secrets, and persistent storage

**Start here:** `03-deploying-applications.md`

## Repository Structure

```
k8s-learning-path/
├── README.md                      # This file
├── 01-understand-k8s.md           # Phase 1: Concepts
├── 02-using-ansible.md            # Phase 2: Setup guide
├── 03-deploying-applications.md   # Phase 3: Hands-on exercises
├── ansible/                       # Cluster automation
│   ├── provision.yml
│   ├── playbook.yml
│   ├── destroy.yml
│   └── roles/
└── workloads/                     # Application manifests
    ├── 01-pods/                   # Basic pods
    ├── 02-deployments/            # Deployments
    ├── 03-services/               # Services
    ├── 04-ingress/                # Ingress controller
    └── 05-real-apps/              # Production-like apps
```

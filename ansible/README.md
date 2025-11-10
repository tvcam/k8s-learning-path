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

## Learn More

See `01-understand-k8s.md` and `02-using-ansible.md` for detailed guides.

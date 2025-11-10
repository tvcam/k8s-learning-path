#!/usr/bin/env python3.11
"""Generate Ansible inventory from existing Hetzner servers."""

import os
import sys
from hcloud import Client

token = os.getenv('HCLOUD_TOKEN')
if not token:
    print('ERROR: HCLOUD_TOKEN not set')
    print('Run: export HCLOUD_TOKEN="your_token"')
    sys.exit(1)

client = Client(token=token)
servers = client.servers.get_all()

# Find k8s servers
master = None
workers = []

for server in servers:
    if server.name == 'k8s-master':
        master = server
    elif server.name.startswith('k8s-worker-'):
        workers.append(server)

if not master:
    print('ERROR: k8s-master not found')
    sys.exit(1)

# Generate inventory
inventory = "[master]\n"
inventory += f"master ansible_host={master.public_net.ipv4.ip} ansible_user=root\n\n"

inventory += "[workers]\n"
for i, worker in enumerate(sorted(workers, key=lambda w: w.name), 1):
    inventory += f"worker{i} ansible_host={worker.public_net.ipv4.ip} ansible_user=root\n"

inventory += "\n[kubernetes:children]\n"
inventory += "master\n"
inventory += "workers\n"

# Write to file
with open('inventory.ini', 'w') as f:
    f.write(inventory)

print(f'✅ Inventory generated with {len(workers)} worker(s)')
print(f'\nServers found:')
print(f'  • Master: {master.name} ({master.public_net.ipv4.ip})')
for worker in workers:
    print(f'  • Worker: {worker.name} ({worker.public_net.ipv4.ip})')
print(f'\nInventory saved to: inventory.ini')


Your Ansible playbook will not only configure Kubernetes, but also **create the Hetzner Cloud servers via API**, then set them up and join them automatically into a working cluster.

This will give you:

* Reproducible infrastructure (no manual Hetzner setup)
* One-command deployment for master + workers
* Ready-to-use kubeconfig file in minutes

---

## 🧱 PREREQUISITES

1. You need a **Hetzner Cloud API token**
   → Create from [console.hetzner.cloud → Access → API Tokens].
   → Copy it — it starts with `hcloud_...`.

2. Install dependencies **on your local machine**:

   ```bash
   sudo apt install -y python3-pip
   pip install ansible hetzner.hcloud
   ansible-galaxy collection install hetzner.hcloud
   ```

3. Save your token locally (for Ansible use):

   ```bash
   export HCLOUD_TOKEN="hcloud_xxxxxxxxxxxxxxxxxxxxx"
   ```

---

## 📂 Folder structure (updated)

```
ansible/
├── inventory.ini             # generated automatically
├── playbook.yml
├── provision.yml             # creates servers
├── roles/
│   ├── common/
│   ├── containerd/
│   ├── kubernetes-master/
│   └── kubernetes-worker/
```

You already have the `roles/` from earlier.

---

## ⚙️ 1️⃣ provision.yml — create servers on Hetzner

This playbook talks directly to the Hetzner Cloud API.

```yaml
---
- name: Provision Hetzner servers
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    hcloud_token: "{{ lookup('env', 'HCLOUD_TOKEN') }}"
    location: hel1
    image: ubuntu-22.04
    ssh_key_name: vibol-key        # must exist in your Hetzner Cloud account
    server_type_master: cx32       # 4 CPU, 8GB RAM
    server_type_worker: cx22       # 2 CPU, 4GB RAM
    master_count: 1
    worker_count: 2

  tasks:
    - name: Create master node
      hetzner.hcloud.hcloud_server:
        api_token: "{{ hcloud_token }}"
        name: "k8s-master"
        server_type: "{{ server_type_master }}"
        image: "{{ image }}"
        location: "{{ location }}"
        ssh_keys:
          - "{{ ssh_key_name }}"
        state: present
        wait: yes
      register: master

    - name: Create worker nodes
      hetzner.hcloud.hcloud_server:
        api_token: "{{ hcloud_token }}"
        name: "k8s-worker-{{ item }}"
        server_type: "{{ server_type_worker }}"
        image: "{{ image }}"
        location: "{{ location }}"
        ssh_keys:
          - "{{ ssh_key_name }}"
        state: present
        wait: yes
      loop: "{{ range(1, worker_count + 1) | list }}"
      register: workers

    - name: Generate inventory file
      copy:
        dest: inventory.ini
        content: |
          [master]
          master ansible_host={{ master.server.public_net.ipv4.ip }} ansible_user=root

          [workers]
          {% for w in workers.results %}
          worker{{ loop.index }} ansible_host={{ w.server.public_net.ipv4.ip }} ansible_user=root
          {% endfor %}

          [kubernetes:children]
          master
          workers

    - name: Show connection info
      debug:
        msg: |
          Cluster created ✅
          Master IP: {{ master.server.public_net.ipv4.ip }}
          Worker IPs:
          {% for w in workers.results %}
            - {{ w.server.public_net.ipv4.ip }}
          {% endfor %}
          Inventory saved to ./inventory.ini
```

---

## ⚙️ 2️⃣ playbook.yml — configure and join cluster

Use the same `playbook.yml` we built earlier.
It references roles `common`, `containerd`, `kubernetes-master`, and `kubernetes-worker`.

Together, they:

* Install containerd
* Install kubeadm/kubectl/kubelet
* Initialize control plane
* Apply Flannel
* Join workers automatically

---

## ⚙️ 3️⃣ Run it all

Now just run these two playbooks in sequence:

```bash
cd ansible
ansible-playbook provision.yml
ansible-playbook -i inventory.ini playbook.yml
```

After ~10–15 min:

```bash
ssh root@$(grep master inventory.ini | awk '{print $2}' | cut -d= -f2)
kubectl get nodes
```

✅ You’ll see:

```
NAME         STATUS   ROLES    AGE   VERSION
master       Ready    control-plane   5m   v1.30.x
worker1      Ready    <none>          3m   v1.30.x
worker2      Ready    <none>          3m   v1.30.x
```

---

## ⚡ Bonus: optional teardown

To destroy all servers later:

```yaml
- name: Delete all k8s servers
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    hcloud_token: "{{ lookup('env', 'HCLOUD_TOKEN') }}"
  tasks:
    - name: Remove all cluster servers
      hetzner.hcloud.hcloud_server:
        api_token: "{{ hcloud_token }}"
        name: "k8s-*"
        state: absent
```

Run with:

```bash
ansible-playbook destroy.yml
```

---

## 🧠 Summary

After this setup:

* You can deploy a **fresh Kubernetes cluster from scratch with one command**.
* Hetzner automatically provisions the servers via API.
* Ansible installs and joins them into a working cluster.
* You can rebuild or destroy it any time without touching the Hetzner console.

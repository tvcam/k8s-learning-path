Ah — got it 😎
You want **Step 10: Automate Kubernetes setup on Hetzner with Ansible** — a minimal but *production-ready* playbook that installs Kubernetes (via `kubeadm`), joins nodes, installs Flannel, and makes your cluster reproducible.

Let’s build this in a way that perfectly fits **your workflow**:
➡ Hetzner VPS instances (Ubuntu 22.04)
➡ Manual Hetzner provisioning (or use hcloud CLI later)
➡ Lightweight, secure, repeatable setup
➡ Works for 1 control plane + 2 workers

---

## 🧩 Folder structure

```
ansible/
├── inventory.ini
├── playbook.yml
├── roles/
│   ├── common/
│   │   └── tasks/main.yml
│   ├── containerd/
│   │   └── tasks/main.yml
│   ├── kubernetes-master/
│   │   └── tasks/main.yml
│   └── kubernetes-worker/
│       └── tasks/main.yml
```

---

## 🧠 inventory.ini

Define your nodes and SSH access:

```ini
[master]
master ansible_host=95.217.xxx.xxx ansible_user=root

[workers]
worker1 ansible_host=88.198.xxx.xxx ansible_user=root
worker2 ansible_host=65.109.xxx.xxx ansible_user=root

[kubernetes:children]
master
workers
```

*(You can replace IPs and users as needed. `root` works fine on fresh Hetzner Ubuntu images.)*

---

## ⚙️ playbook.yml

```yaml
- hosts: all
  become: true
  roles:
    - common
    - containerd

- hosts: master
  become: true
  roles:
    - kubernetes-master

- hosts: workers
  become: true
  roles:
    - kubernetes-worker
```

---

## 🧱 roles/common/tasks/main.yml

Base OS configuration (swap, sysctl, packages):

```yaml
---
- name: Disable swap
  command: swapoff -a
  args:
    warn: false

- name: Disable swap in fstab
  replace:
    path: /etc/fstab
    regexp: '(^[^#].*\bswap\b.*$)'
    replace: '# \1'

- name: Load kernel modules
  shell: |
    modprobe overlay
    modprobe br_netfilter

- name: Set sysctl params
  copy:
    dest: /etc/sysctl.d/k8s.conf
    content: |
      net.bridge.bridge-nf-call-iptables  = 1
      net.bridge.bridge-nf-call-ip6tables = 1
      net.ipv4.ip_forward                 = 1
  notify: reload sysctl

- name: Install base packages
  apt:
    name:
      - apt-transport-https
      - curl
      - ca-certificates
      - gnupg
    update_cache: yes

- name: reload sysctl
  command: sysctl --system
  listen: reload sysctl
```

---

## 🧰 roles/containerd/tasks/main.yml

Install and configure containerd:

```yaml
---
- name: Install containerd
  apt:
    name: containerd
    state: present

- name: Create containerd config
  shell: |
    mkdir -p /etc/containerd
    containerd config default > /etc/containerd/config.toml
  args:
    creates: /etc/containerd/config.toml

- name: Enable and restart containerd
  systemd:
    name: containerd
    enabled: yes
    state: restarted
```

---

## 🧠 roles/kubernetes-master/tasks/main.yml

Initialize the control plane and install Flannel:

```yaml
---
- name: Add Kubernetes APT repo
  shell: |
    curl -fsSLo /etc/apt/keyrings/kubernetes-archive-keyring.gpg https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key
    echo "deb [signed-by=/etc/apt/keyrings/kubernetes-archive-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /" > /etc/apt/sources.list.d/kubernetes.list
  args:
    creates: /etc/apt/sources.list.d/kubernetes.list

- name: Install kubeadm, kubelet, kubectl
  apt:
    name:
      - kubelet
      - kubeadm
      - kubectl
    state: present
    update_cache: yes

- name: Initialize the cluster
  command: kubeadm init --pod-network-cidr=10.244.0.0/16
  args:
    creates: /etc/kubernetes/admin.conf
  register: kubeinit

- name: Create kubeconfig for user
  shell: |
    mkdir -p $HOME/.kube
    cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
    chown $(id -u):$(id -g) $HOME/.kube/config
  environment:
    HOME: /root

- name: Save join command
  shell: kubeadm token create --print-join-command
  register: join_cmd

- name: Write join command to file
  local_action:
    module: copy
    content: "{{ join_cmd.stdout }}"
    dest: join-command.txt

- name: Install Flannel CNI
  shell: kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml
  environment:
    KUBECONFIG: /etc/kubernetes/admin.conf
```

---

## 🧩 roles/kubernetes-worker/tasks/main.yml

Join worker nodes to the cluster automatically:

```yaml
---
- name: Add Kubernetes APT repo
  shell: |
    curl -fsSLo /etc/apt/keyrings/kubernetes-archive-keyring.gpg https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key
    echo "deb [signed-by=/etc/apt/keyrings/kubernetes-archive-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /" > /etc/apt/sources.list.d/kubernetes.list
  args:
    creates: /etc/apt/sources.list.d/kubernetes.list

- name: Install kubeadm, kubelet, kubectl
  apt:
    name:
      - kubelet
      - kubeadm
      - kubectl
    state: present
    update_cache: yes

- name: Read join command from local file
  delegate_to: localhost
  run_once: true
  slurp:
    src: join-command.txt
  register: join_data

- name: Join cluster
  command: "{{ join_data.content | b64decode }}"
  args:
    creates: /etc/kubernetes/kubelet.conf
```

---

## 🚀 Running the playbook

```bash
cd ansible
ansible-playbook -i inventory.ini playbook.yml
```

### What happens

* All nodes are prepped with common settings
* Containerd is installed
* Master is initialized and Flannel applied
* Workers automatically join using the generated join token
* You end up with a ready-to-use cluster in 10–15 min 🔥

Check it:

```bash
kubectl get nodes
```

---

## 💡 Optional improvements later

| Feature                    | How                                                                  |
| -------------------------- | -------------------------------------------------------------------- |
| **Hetzner CSI driver**     | Add another role to install it (persistent volumes)                  |
| **Ingress setup**          | Add role to deploy NGINX ingress + cert-manager                      |
| **Firewall setup**         | Use `ufw` or Hetzner Cloud Firewall module                           |
| **Automated provisioning** | Use `hetzner.hcloud_server` Ansible module to create VPS dynamically |

---

## ✅ TL;DR

This playbook gives you:

* Reproducible Kubernetes setup across any fresh Hetzner VPS
* Declarative join process (auto token handling)
* Modularity (add ingress, CSI, monitoring later)
* Safe and minimal configuration (containerd, Flannel, kubeadm)

---

Would you like me to extend this playbook next to **automatically provision Hetzner servers via API (no manual VPS creation)** and then run the same setup end-to-end?

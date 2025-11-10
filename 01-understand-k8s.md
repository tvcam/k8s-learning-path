## 🧱 1. The Big Picture: Docker vs Kubernetes

You already know Docker runs containers — isolated environments for your apps.
Kubernetes (K8s) is basically the **operating system for containers** across multiple machines.

| Concept        | Docker                                | Kubernetes                                     |
| -------------- | ------------------------------------- | ---------------------------------------------- |
| **Purpose**    | Package and run a single container    | Manage and orchestrate many containers         |
| **Scope**      | One host                              | Many hosts (cluster)                           |
| **Networking** | Docker bridge network                 | Full cluster network (Pods, Services, Ingress) |
| **Scaling**    | Manual (`docker run` more containers) | Automated (ReplicaSets, HPA)                   |
| **Updates**    | Manual                                | Rolling updates, health checks, self-healing   |

👉 Think of Docker as **“single app runtime”**, and Kubernetes as **“multi-app operating system.”**

---

## ⚙️ 2. The Core Kubernetes Components (in your own mental model)

Let’s visualize how it works — imagine you have **3 Hetzner VPS nodes**.

```
+-------------------------------+
|   Control Plane (Master)      |
| - API Server (brain)          |
| - etcd (database)             |
| - Controller Manager          |
| - Scheduler                   |
+-------------------------------+
         |
         | talks to
         v
+-------------------------------+
|   Worker Node(s)              |
| - kubelet (node agent)        |
| - container runtime (Docker)  |
| - kube-proxy (network routing)|
| - pods (your apps)            |
+-------------------------------+
```

### 🧠 Control Plane = the brains

* **API Server:** Central entry point (all kubectl commands talk here).
* **etcd:** Stores all cluster state (deployed apps, configs, secrets).
* **Controller Manager:** Watches desired state vs actual state, and fixes mismatches.
* **Scheduler:** Decides *where* to run new Pods.

### 🏃 Worker Nodes = the muscles

* **kubelet:** Talks to API server and actually runs containers on that node.
* **container runtime:** Usually Docker or containerd.
* **kube-proxy:** Handles networking rules so services can talk to each other.

When you deploy something, you tell Kubernetes *desired state*, like:

```yaml
replicas: 3
```

It will make sure 3 Pods exist — if one dies, it recreates it.

---

## 🪄 3. How the magic happens (step-by-step under the hood)

Let’s say you run:

```bash
kubectl apply -f deployment.yaml
```

Here’s what happens:

1. **Your YAML → API Server**

   * The manifest goes to `kube-apiserver`.
   * Stored in `etcd`.

2. **Scheduler notices**

   * Scheduler finds nodes that have capacity → assigns Pods to nodes.

3. **kubelet pulls container**

   * The worker’s kubelet pulls the Docker image, starts it via container runtime.

4. **kube-proxy updates networking**

   * Exposes your app internally, applies routing.

5. **Controller Manager keeps watch**

   * Ensures Pods = desired replicas.
   * If a Pod crashes → it restarts automatically.

That’s the self-healing loop.

---

## 🧩 4. How to manually set up Kubernetes on Hetzner

Let’s do it your way — **manual setup**, not via cloud-managed service.

### 🧰 Step 1: Prepare your Hetzner environment

You’ll need:

* 1 control-plane node (2–4 vCPU, 4 GB RAM)
* 2 worker nodes (2 vCPU, 2 GB RAM)
* Ubuntu 22.04 LTS (recommended)

Make sure:

```bash
sudo apt update && sudo apt install -y apt-transport-https curl
```

---

### 🧰 Step 2: Install container runtime

Use containerd (Docker alternative that Kubernetes natively supports):

```bash
sudo apt install -y containerd
sudo systemctl enable containerd
sudo systemctl start containerd
```

Check:

```bash
containerd --version
```

---

### 🧰 Step 3: Install kubeadm, kubelet, kubectl

These are the 3 key tools.

```bash
sudo curl -fsSLo /etc/apt/keyrings/kubernetes-archive-keyring.gpg https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-archive-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /" | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt update
sudo apt install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```

---

### 🧰 Step 4: Initialize your control plane

Run this on your **master node**:

```bash
sudo kubeadm init --pod-network-cidr=10.244.0.0/16
```

When finished, it prints a `kubeadm join` command like:

```bash
kubeadm join <MASTER_IP>:6443 --token <TOKEN> --discovery-token-ca-cert-hash <HASH>
```

Save this — you’ll use it on worker nodes.

---

### 🧰 Step 5: Configure kubectl

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

Now `kubectl get nodes` should show your master node (NotReady yet).

---

### 🧰 Step 6: Install a CNI (network)

Use Flannel (simple, stable):

```bash
kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml
```

After a few seconds:

```bash
kubectl get nodes
```

→ All should show `Ready`.

---

### 🧰 Step 7: Join worker nodes

SSH into each worker node and paste the `kubeadm join ...` command.
Once joined, check:

```bash
kubectl get nodes
```

You’ll see master + workers in `Ready` state.

---

### 🧰 Step 8: Deploy something (e.g., your Rails app)

Create a simple Deployment + Service:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rails-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: rails-demo
  template:
    metadata:
      labels:
        app: rails-demo
    spec:
      containers:
      - name: rails
        image: vibol/rails-demo:latest
        ports:
        - containerPort: 3000
---
apiVersion: v1
kind: Service
metadata:
  name: rails-demo-service
spec:
  selector:
    app: rails-demo
  ports:
    - port: 80
      targetPort: 3000
  type: NodePort
```

Deploy:

```bash
kubectl apply -f rails-demo.yaml
kubectl get pods
```

Access your app at:

```
http://<any-node-ip>:<nodePort>
```

---

### 🧰 Step 9: Manage your cluster

Common tasks:

| Command                                       | Description                      |
| --------------------------------------------- | -------------------------------- |
| `kubectl get pods -A`                         | See all running containers       |
| `kubectl describe pod <pod>`                  | Details & logs                   |
| `kubectl logs <pod>`                          | View app logs                    |
| `kubectl delete pod <pod>`                    | Force restart                    |
| `kubectl rollout restart deployment <app>`    | Restart all pods in a deployment |
| `kubectl scale deployment <app> --replicas=5` | Scale your app                   |
| `kubectl top pods`                            | Resource usage                   |

---

### 🧰 Step 10: (Optional) Automate it later with Ansible

Once you’re comfortable with the manual steps, you can codify them in Ansible playbooks (I can help you generate a minimal one tailored to Hetzner’s layout).

---

## 🚀 Summary in plain terms

* **Docker** = runs one container at a time.
* **Kubernetes** = controls *many containers* over *many machines*.
* You talk to Kubernetes via `kubectl` → API Server → etcd → kubelet → containers.
* You declare what you *want* (YAML manifests), Kubernetes maintains that state.
* On Hetzner: you can build your own cluster easily with `kubeadm`, or later automate with Ansible and Hetzner Cloud API.

---

Would you like me to make a **step-by-step Hetzner setup guide** (with firewall, SSH, persistent volumes, and load balancer) that’s *production-ready but minimal* — something you could copy-paste and actually run in 1 hour?

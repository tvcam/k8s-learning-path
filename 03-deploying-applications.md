# Deploying Applications on Kubernetes

**A comprehensive, hands-on guide to deploying real applications on your Kubernetes cluster.**

## What You'll Learn

By the end of this guide, you'll understand:

- **Workload Management**: Pods, ReplicaSets, and Deployments
- **Networking**: Services, Endpoints, and DNS
- **Traffic Routing**: Ingress controllers and routing rules
- **Storage**: PersistentVolumes and PersistentVolumeClaims
- **Configuration**: ConfigMaps and Secrets
- **Resource Management**: Requests, limits, and quality of service
- **Application Patterns**: Stateless and stateful workloads

Each section includes theory, practical exercises, and real-world examples.

---

## Prerequisites

### Required

- ✅ Working Kubernetes cluster (see Phase 2: `02-using-ansible.md`)
- ✅ `kubectl` installed and configured
- ✅ SSH access to cluster nodes

### Verify Your Setup

```bash
# SSH to master node
ssh root@<master-ip>

# Check cluster health
kubectl get nodes
kubectl get componentstatuses
kubectl cluster-info

# Verify all nodes are Ready
# NAME         STATUS   ROLES           AGE   VERSION
# k8s-master   Ready    control-plane   1h    v1.30.x
# k8s-worker   Ready    <none>          1h    v1.30.x
```

---

## Exercise 1: Understanding Pods

### What Are Pods?

Pods are the **smallest deployable units** in Kubernetes. They represent a single instance of a running process in your cluster.

**Key Concepts:**
- A pod contains **one or more containers** (usually one)
- Containers in a pod **share the network namespace** (same IP address)
- Containers can communicate via **localhost**
- Pods are **ephemeral** - they don't self-heal when deleted
- Each pod gets a **unique IP address** in the cluster

**Pod Lifecycle:**
```
Pending → ContainerCreating → Running → Succeeded/Failed
```

### When to Use Pods Directly

❌ **Don't use bare pods in production** - they don't self-heal
✅ **Use for:** Quick testing, debugging, one-off jobs

**In production, use:** Deployments, StatefulSets, or DaemonSets

### Deploy Your First Pod

```bash
kubectl apply -f workloads/01-pods/nginx-pod.yaml
```

**What's in the manifest:**
```yaml
apiVersion: v1          # API version for Pods
kind: Pod               # Resource type
metadata:
  name: nginx           # Pod name (must be unique in namespace)
  labels:
    app: nginx          # Labels for selection and organization
spec:
  containers:
  - name: nginx         # Container name
    image: nginx:1.24   # Container image
    ports:
    - containerPort: 80 # Port exposed by container
```

### Inspect the Pod

```bash
# Quick status check
kubectl get pods

# Output:
# NAME    READY   STATUS    RESTARTS   AGE
# nginx   1/1     Running   0          30s

# Detailed information
kubectl describe pod nginx
# Shows: Events, Status, IP address, Node placement, Resource usage

# View real-time logs
kubectl logs nginx
kubectl logs -f nginx  # Follow logs (like tail -f)

# Execute commands inside the pod
kubectl exec -it nginx -- bash
# Inside container:
curl localhost
ls /usr/share/nginx/html/
exit
```

### Understanding Pod Networking

```bash
# Get pod IP address
kubectl get pod nginx -o wide

# From another pod, you can reach it by IP
kubectl run test --image=busybox --rm -it --restart=Never -- wget -qO- <pod-ip>
```

**Important:** Pod IPs are ephemeral. When a pod is deleted and recreated, it gets a new IP. That's why we need Services!

### Access the Application

**Method 1: Port Forwarding** (for development/testing)
```bash
kubectl port-forward pod/nginx 8080:80
# Visit http://localhost:8080
```

**How it works:**
```
Your Browser (localhost:8080) → kubectl → API Server → kubelet → Pod (port 80)
```

**Method 2: Direct Access** (from cluster)
```bash
# Only works from within the cluster or nodes
curl http://<pod-ip>
```

### Pod Lifecycle Demo

```bash
# Delete the pod
kubectl delete pod nginx

# Try to list it again
kubectl get pods
# It's gone and won't come back!
```

**Key Learning:** Pods are ephemeral. No automatic recreation. This is by design. For self-healing, use Deployments.

### Pod Multi-Container Pattern (Sidecar Example)

```yaml
# Example: Application + logging sidecar
apiVersion: v1
kind: Pod
metadata:
  name: app-with-sidecar
spec:
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: logs
      mountPath: /var/log
  - name: log-shipper
    image: fluent/fluentd
    volumeMounts:
    - name: logs
      mountPath: /var/log
  volumes:
  - name: logs
    emptyDir: {}
```

**Use cases:**
- Log shipping
- Service mesh proxies (Istio, Linkerd)
- Configuration synchronization
- Data processing pipelines

---

## Exercise 2: Deployments - Self-Healing Applications

### What Are Deployments?

Deployments provide **declarative updates** for Pods and ReplicaSets. They are the recommended way to deploy stateless applications.

**Deployment Hierarchy:**
```
Deployment
  ↓
ReplicaSet (manages pod replicas)
  ↓
Pods (actual running instances)
```

**What Deployments Provide:**

| Feature | Description |
|---------|-------------|
| **Self-Healing** | Automatically replaces failed pods |
| **Scaling** | Easy scale up/down of replicas |
| **Rolling Updates** | Zero-downtime deployments |
| **Rollback** | Revert to previous versions |
| **Version History** | Track deployment revisions |
| **Declarative** | Describe desired state, Kubernetes makes it happen |

### Create a Deployment

```bash
kubectl apply -f workloads/02-deployments/nginx-deployment.yaml
```

**Understanding the Manifest:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx              # Deployment label
spec:
  replicas: 3               # Desired number of pods
  selector:
    matchLabels:
      app: nginx            # Which pods this deployment manages
  template:                 # Pod template
    metadata:
      labels:
        app: nginx          # Label applied to pods
    spec:
      containers:
      - name: nginx
        image: nginx:1.24
        resources:          # Resource management
          requests:         # Guaranteed resources
            memory: "64Mi"
            cpu: "100m"
          limits:           # Maximum resources
            memory: "128Mi"
            cpu: "200m"
```

### Explore the Deployment

```bash
# View deployment status
kubectl get deployments
# NAME               READY   UP-TO-DATE   AVAILABLE   AGE
# nginx-deployment   3/3     3            3           1m

# View the ReplicaSet created by the deployment
kubectl get replicasets
# NAME                          DESIRED   CURRENT   READY   AGE
# nginx-deployment-5f8b9c5d4b   3         3         3       1m

# View the pods created by the ReplicaSet
kubectl get pods
# NAME                                READY   STATUS    RESTARTS   AGE
# nginx-deployment-5f8b9c5d4b-abcde   1/1     Running   0          1m
# nginx-deployment-5f8b9c5d4b-fghij   1/1     Running   0          1m
# nginx-deployment-5f8b9c5d4b-klmno   1/1     Running   0          1m

# See the relationship
kubectl get pods --show-labels
```

### Self-Healing in Action

```bash
# Delete a pod manually
kubectl delete pod <pod-name>

# Immediately list pods again
kubectl get pods
# A new pod is automatically created to maintain 3 replicas!

# The deployment ensures desired state = actual state
```

### Scaling Applications

**Horizontal scaling** means adding more pod replicas.

```bash
# Scale up to 5 replicas
kubectl scale deployment nginx-deployment --replicas=5

# Watch pods being created
kubectl get pods -w

# Check deployment status
kubectl get deployment nginx-deployment
# READY shows 5/5

# Scale back down
kubectl scale deployment nginx-deployment --replicas=2

# Watch pods terminating
kubectl get pods -w
```

**Scaling Strategy:**
- **Scale out**: Handle more traffic
- **Scale in**: Reduce resource usage
- **Auto-scaling**: Use HorizontalPodAutoscaler (advanced topic)

### Rolling Updates - Zero Downtime Deployments

Rolling updates allow you to update your application **without downtime**.

**Strategy:**
1. Create new pods with new version
2. Wait for them to be ready
3. Terminate old pods
4. Repeat until all pods updated

```bash
# Update the nginx image
kubectl set image deployment/nginx-deployment nginx=nginx:1.25

# Watch the rollout in real-time
kubectl rollout status deployment/nginx-deployment

# See the rollout happening
kubectl get pods
# You'll see old pods terminating and new ones starting
```

**What's happening:**
```
Old ReplicaSet: 3 pods → 2 pods → 1 pod → 0 pods
New ReplicaSet: 0 pods → 1 pod  → 2 pods → 3 pods
```

**Rollout Parameters (in deployment spec):**
```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Max new pods above desired count
      maxUnavailable: 0  # Max pods that can be unavailable
```

### Rollout History and Rollback

```bash
# View deployment history
kubectl rollout history deployment/nginx-deployment

# Output shows revisions:
# REVISION  CHANGE-CAUSE
# 1         <none>
# 2         <none>

# See details of a specific revision
kubectl rollout history deployment/nginx-deployment --revision=2

# Rollback to previous version
kubectl rollout undo deployment/nginx-deployment

# Rollback to specific revision
kubectl rollout undo deployment/nginx-deployment --to-revision=1

# Pause a rollout (useful during issues)
kubectl rollout pause deployment/nginx-deployment

# Resume a paused rollout
kubectl rollout resume deployment/nginx-deployment
```

### Update Strategies

**1. Recreate Strategy**
```yaml
strategy:
  type: Recreate  # Kill all old pods, then create new ones
```
- ⚠️ Causes downtime
- ✅ Useful when you can't run old and new versions together
- Use case: Database schema changes

**2. Rolling Update Strategy** (default)
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 25%
    maxUnavailable: 25%
```
- ✅ Zero downtime
- ✅ Gradual rollout
- Use case: Most applications

### Clean up

```bash
kubectl delete deployment nginx-deployment
```

**Key Learnings:**
- Deployments manage ReplicaSets, which manage Pods
- Self-healing ensures desired replicas are always running
- Rolling updates enable zero-downtime deployments
- Easy rollback if something goes wrong
- Declarative configuration - describe what you want, not how to do it

---

## Exercise 3: Services - Stable Networking

### The Problem Services Solve

Pods are ephemeral and have dynamic IP addresses. When a pod dies and is recreated, it gets a new IP. How do other pods reliably communicate with it?

**Solution:** Kubernetes Services provide:
- **Stable IP address** (ClusterIP)
- **DNS name** (`service-name.namespace.svc.cluster.local`)
- **Load balancing** across pod replicas
- **Service discovery** mechanism

### Service Types

| Type | Use Case | Access |
|------|----------|---------|
| **ClusterIP** | Internal services | Only within cluster |
| **NodePort** | External access | `<NodeIP>:<Port>` |
| **LoadBalancer** | Cloud load balancer | External IP (cloud only) |
| **ExternalName** | External service mapping | DNS CNAME |

### How Services Work

**Service Selection via Labels:**
```
Service (selector: app=nginx)
   ↓
Endpoints (list of pod IPs)
   ↓
Pod1 (label: app=nginx)
Pod2 (label: app=nginx)
Pod3 (label: app=nginx)
```

### Exercise 3.1: ClusterIP Service

ClusterIP is the **default service type**. It exposes the service on an **internal IP** within the cluster.

```bash
kubectl apply -f workloads/03-services/nginx-clusterip.yaml
```

**Understanding the Manifest:**
```yaml
---
# First, create the deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-clusterip
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx-clusterip  # Deployment selector
  template:
    metadata:
      labels:
        app: nginx-clusterip  # Pod labels
    spec:
      containers:
      - name: nginx
        image: nginx:1.24
---
# Then, create the service
apiVersion: v1
kind: Service
metadata:
  name: nginx-clusterip
spec:
  type: ClusterIP              # Default type
  selector:
    app: nginx-clusterip       # Matches pod labels above
  ports:
  - protocol: TCP
    port: 80                   # Service port
    targetPort: 80             # Container port
```

**How it works:**
```
Client → Service (ClusterIP:80) → Load Balancer → Pod1:80
                                                 → Pod2:80
```

### Test ClusterIP Service

```bash
# Get service information
kubectl get svc nginx-clusterip

# Output:
# NAME              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)
# nginx-clusterip   ClusterIP   10.96.123.45    <none>        80/TCP

# Check which pods the service routes to
kubectl get endpoints nginx-clusterip

# Output shows pod IPs:
# NAME              ENDPOINTS                     AGE
# nginx-clusterip   10.244.1.5:80,10.244.1.6:80   1m
```

**Test 1: Access via Service IP**
```bash
kubectl run test-pod --image=busybox --rm -it --restart=Never -- wget -qO- <CLUSTER-IP>
```

**Test 2: Access via DNS name**
```bash
kubectl run test-pod --image=busybox --rm -it --restart=Never -- wget -qO- nginx-clusterip

# Also works with full DNS name:
# nginx-clusterip.default.svc.cluster.local
```

**DNS Pattern:**
```
<service-name>.<namespace>.svc.<cluster-domain>
```
- In same namespace: `nginx-clusterip`
- Cross-namespace: `nginx-clusterip.default`
- Full FQDN: `nginx-clusterip.default.svc.cluster.local`

### Load Balancing Demo

```bash
# Get pod names
kubectl get pods -l app=nginx-clusterip -o wide

# Access service multiple times
kubectl run test-pod --image=busybox --rm -it --restart=Never -- sh
# Inside pod:
for i in {1..10}; do wget -qO- nginx-clusterip | grep hostname; done

# Requests are distributed across pods!
```

### Exercise 3.2: NodePort Service

NodePort exposes the service on a **static port on each node**. This allows external access without a load balancer.

```bash
kubectl apply -f workloads/03-services/nginx-nodeport.yaml
```

**Understanding NodePort:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-nodeport
spec:
  type: NodePort
  selector:
    app: nginx-nodeport
  ports:
  - protocol: TCP
    port: 80           # Service port (internal)
    targetPort: 80     # Container port
    nodePort: 30080    # Node port (30000-32767 range)
```

**How it works:**
```
External Client → NodeIP:30080 → Service → Pod1:80
                                         → Pod2:80
```

**Traffic Flow:**
1. Request arrives at any node on port 30080
2. iptables rules forward to ClusterIP
3. Service load balances to pods
4. Pods may be on different nodes (kube-proxy handles routing)

### Test NodePort Service

```bash
# Get service details
kubectl get svc nginx-nodeport

# Output:
# NAME             TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
# nginx-nodeport   NodePort   10.96.234.56   <none>        80:30080/TCP   1m

# Access from outside the cluster
curl http://<worker-node-ip>:30080

# Access from any node's IP works (even master)
curl http://<master-ip>:30080
```

**NodePort Use Cases:**
- Development/testing environments
- On-premise clusters without load balancer
- Simple external access
- **Not recommended for production** (use LoadBalancer or Ingress instead)

### Service Session Affinity

By default, services distribute requests randomly. Enable session affinity for sticky sessions:

```yaml
spec:
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800  # 3 hours
```

### Headless Services

For direct pod-to-pod communication without load balancing:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-headless
spec:
  clusterIP: None  # Makes it headless
  selector:
    app: nginx
```

**Use case:** StatefulSets, where you need to reach specific pods by name.

### Clean up

```bash
kubectl delete -f workloads/03-services/nginx-clusterip.yaml
kubectl delete -f workloads/03-services/nginx-nodeport.yaml
```

**Key Learnings:**
- Services provide stable endpoints for ephemeral pods
- ClusterIP for internal services
- NodePort for external access (development)
- Services use label selectors to find pods
- DNS makes service discovery easy
- Built-in load balancing across pod replicas

---

## Exercise 4: Ingress - HTTP Routing

### What is Ingress?

**The Problem:**
- NodePort exposes one service per port (limited port range)
- LoadBalancer creates one cloud LB per service (expensive)
- No HTTP-level routing (host-based, path-based)

**The Solution: Ingress**
- Single entry point for multiple services
- HTTP/HTTPS routing rules
- Host-based routing (`app1.com` → service1, `app2.com` → service2)
- Path-based routing (`/api` → api-service, `/web` → web-service)
- SSL/TLS termination
- Load balancing

### Ingress Architecture

```
Internet
   ↓
Ingress Controller (nginx pod)
   ↓ (reads Ingress resources)
Ingress Rules (routing config)
   ↓ (routes based on host/path)
Services (backend services)
   ↓
Pods (application containers)
```

**Two Components:**
1. **Ingress Controller**: The actual load balancer (nginx, traefik, HAProxy)
2. **Ingress Resource**: Routing rules (which requests go where)

### Step 1: Install NGINX Ingress Controller

```bash
kubectl apply -f workloads/04-ingress/ingress-controller.yaml
```

**What this installs:**
- Namespace: `ingress-nginx`
- Deployment: NGINX controller pods
- Service: NodePort service (30080 for HTTP, 30443 for HTTPS)
- RBAC: Permissions to watch Ingress resources
- IngressClass: Defines this as the nginx controller

Wait for it to be ready:
```bash
kubectl get pods -n ingress-nginx
# NAME                                        READY   STATUS    RESTARTS   AGE
# ingress-nginx-controller-xxxxxxxxxx-xxxxx   1/1     Running   0          1m

kubectl get svc -n ingress-nginx
# NAME                       TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)
# ingress-nginx-controller   NodePort   10.96.123.45   <none>        80:30080/TCP,443:30443/TCP
```

### Step 2: Deploy Applications

Deploy two different applications:

```bash
kubectl apply -f workloads/04-ingress/app1.yaml
kubectl apply -f workloads/04-ingress/app2.yaml
```

**What's deployed:**
- 2 Deployments (app1 and app2)
- 2 ConfigMaps (custom HTML for each app)
- 2 ClusterIP Services

```bash
# Verify deployments
kubectl get deployments
kubectl get pods
kubectl get svc
```

### Step 3: Create Ingress Rules

```bash
kubectl apply -f workloads/04-ingress/ingress-rules.yaml
```

**Understanding the Ingress Resource:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx  # Which controller to use
  rules:
  # Rule 1: Host-based routing
  - host: app1.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app1-service
            port:
              number: 80
  # Rule 2: Another host
  - host: app2.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app2-service
            port:
              number: 80
```

**Routing Logic:**
```
Request with "Host: app1.local" → app1-service → app1 pods
Request with "Host: app2.local" → app2-service → app2 pods
```

### Step 4: Configure Local DNS

Add to your `/etc/hosts` file:

```bash
# Get worker node IP from ansible/inventory.ini
<worker-ip> app1.local app2.local

# Example:
157.180.65.215 app1.local app2.local
```

### Step 5: Test the Ingress

```bash
# Test with curl
curl http://app1.local:30080
# Should show: "Welcome to Application 1"

curl http://app2.local:30080
# Should show: "Welcome to Application 2"

# Or visit in browser:
# http://app1.local:30080
# http://app2.local:30080
```

### Path-Based Routing Example

You can route based on URL paths:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: path-based-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: myapp.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8080
      - path: /web
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

**Routing:**
```
myapp.com/api/users  → api-service
myapp.com/web/home   → web-service
```

### Path Types

| Type | Matching | Example |
|------|----------|---------|
| `Prefix` | Matches path prefix | `/api` matches `/api/users` |
| `Exact` | Exact match only | `/api` doesn't match `/api/users` |
| `ImplementationSpecific` | Depends on controller | Varies |

### SSL/TLS Termination

Add HTTPS support:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
type: kubernetes.io/tls
data:
  tls.crt: <base64-encoded-cert>
  tls.key: <base64-encoded-key>
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tls-ingress
spec:
  tls:
  - hosts:
    - myapp.com
    secretName: tls-secret
  rules:
  - host: myapp.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-service
            port:
              number: 80
```

### Ingress Annotations

NGINX Ingress Controller supports many annotations for customization:

```yaml
metadata:
  annotations:
    # Rewrite rules
    nginx.ingress.kubernetes.io/rewrite-target: /$2
    
    # Rate limiting
    nginx.ingress.kubernetes.io/limit-rps: "10"
    
    # CORS
    nginx.ingress.kubernetes.io/enable-cors: "true"
    
    # Timeouts
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "60"
    
    # Custom redirects
    nginx.ingress.kubernetes.io/permanent-redirect: https://newsite.com
```

### View Ingress Resources

```bash
# List ingress resources
kubectl get ingress

# Output:
# NAME               CLASS   HOSTS                     ADDRESS   PORTS   AGE
# example-ingress    nginx   app1.local,app2.local               80      5m

# Detailed information
kubectl describe ingress example-ingress

# View controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

### Clean up

```bash
kubectl delete -f workloads/04-ingress/ingress-rules.yaml
kubectl delete -f workloads/04-ingress/app1.yaml
kubectl delete -f workloads/04-ingress/app2.yaml

# Optional: Remove controller
kubectl delete -f workloads/04-ingress/ingress-controller.yaml
```

**Key Learnings:**
- Ingress provides HTTP/HTTPS routing to services
- One Ingress Controller can handle multiple applications
- Host-based routing: Different domains to different services
- Path-based routing: Different URL paths to different services
- More efficient than NodePort for multiple services
- Supports SSL/TLS termination, rate limiting, and more

---

## Exercise 5: Real Applications

Deploy production-like applications demonstrating various Kubernetes patterns.

### 5.1 Redis - Stateless In-Memory Cache

**Use Case:** Session storage, caching, message queue, real-time analytics

**Characteristics:**
- Stateless (no persistent storage in this example)
- Single replica (for simplicity)
- ClusterIP service (internal only)

```bash
kubectl apply -f workloads/05-real-apps/redis.yaml
```

**Test Redis:**
```bash
# Connect to Redis
kubectl run redis-test --image=redis:7-alpine --rm -it --restart=Never -- redis-cli -h redis

# Inside redis-cli:
SET session:user123 "{'logged_in': true, 'username': 'alice'}"
GET session:user123
EXPIRE session:user123 3600
TTL session:user123

SET counter 100
INCR counter
GET counter

KEYS *
exit
```

**Redis Commands Overview:**
- `SET/GET`: Store/retrieve values
- `INCR/DECR`: Atomic counters
- `EXPIRE`: Set TTL
- `LPUSH/RPUSH`: List operations
- `HSET/HGET`: Hash operations
- `SADD/SMEMBERS`: Set operations

**Production Considerations:**
- Use Redis Cluster for high availability
- Enable persistence (RDB snapshots or AOF)
- Set resource limits
- Use passwords (requirepass in redis.conf)
- Monitor with Redis metrics

---

### 5.2 PostgreSQL - Stateful Database

**Use Case:** Relational database for persistent data storage

**Characteristics:**
- Stateful (uses PersistentVolumeClaim)
- Data survives pod restarts
- Single replica (for this example)

```bash
kubectl apply -f workloads/05-real-apps/postgres.yaml
```

**Understanding Persistent Storage:**
```yaml
# Step 1: Request storage
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes:
    - ReadWriteOnce  # Single node read-write
  resources:
    requests:
      storage: 1Gi

# Step 2: Use in pod
spec:
  volumes:
  - name: postgres-storage
    persistentVolumeClaim:
      claimName: postgres-pvc
  containers:
  - name: postgres
    volumeMounts:
    - name: postgres-storage
      mountPath: /var/lib/postgresql/data
```

**Storage Lifecycle:**
```
PVC Request → Kubernetes finds/creates PV → Binds PV to PVC → Pod uses PVC
```

**Test PostgreSQL:**
```bash
# Connect to database
kubectl exec -it deployment/postgres -- psql -U admin -d mydb

# Inside psql:
-- Create a table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert data
INSERT INTO users (name, email) VALUES 
    ('Alice Johnson', 'alice@example.com'),
    ('Bob Smith', 'bob@example.com'),
    ('Charlie Brown', 'charlie@example.com');

-- Query data
SELECT * FROM users;
SELECT name, email FROM users WHERE name LIKE 'A%';
SELECT COUNT(*) FROM users;

-- Update data
UPDATE users SET email = 'alice.j@example.com' WHERE name = 'Alice Johnson';

-- Create index
CREATE INDEX idx_users_email ON users(email);

-- View tables
\dt

-- Describe table
\d users

-- Quit
\q
```

**Test Persistence:**
```bash
# Delete the pod
kubectl delete pod -l app=postgres

# Wait for new pod
kubectl get pods -w

# Connect again
kubectl exec -it deployment/postgres -- psql -U admin -d mydb -c "SELECT * FROM users;"

# Data is still there! 🎉
```

**Production Considerations:**
- Use StatefulSet for replicas
- Set up replication (primary/replica)
- Configure backup strategy
- Use Secrets for passwords
- Set connection limits
- Monitor with PostgreSQL metrics
- Use connection pooling (PgBouncer)

---

### 5.3 WordPress - Multi-Tier Application

**Use Case:** Complete web application with frontend and database

**Components:**
- MySQL database (persistent storage)
- WordPress PHP application (persistent uploads)
- Secrets for credentials
- Services for internal communication
- Ingress for external access

```bash
# Deploy MySQL first
kubectl apply -f workloads/05-real-apps/wordpress/mysql.yaml

# Wait for MySQL to be ready
kubectl get pods -w
# Wait until STATUS is Running

# Deploy WordPress
kubectl apply -f workloads/05-real-apps/wordpress/wordpress.yaml
```

**Architecture:**
```
Internet
   ↓
Ingress (wordpress.local)
   ↓
WordPress Service (ClusterIP)
   ↓
WordPress Pod
   ↓ (connects via mysql:3306)
MySQL Service (ClusterIP)
   ↓
MySQL Pod
   ↓
PersistentVolume (database data)
```

**Understanding Secrets:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mysql-secret
type: Opaque
stringData:
  password: wordpress123  # Not encrypted at rest by default!

# Used in deployment:
env:
- name: MYSQL_PASSWORD
  valueFrom:
    secretKeyRef:
      name: mysql-secret
      key: password
```

**Configure DNS:**
```bash
# Add to /etc/hosts
<worker-ip> wordpress.local
```

**Access WordPress:**
```bash
# Get ingress controller service
kubectl get svc -n ingress-nginx

# Visit: http://wordpress.local:30080
```

**WordPress Setup:**
1. Select language
2. Set site title
3. Create admin username and password
4. Install WordPress
5. Start creating content!

**WordPress Admin:**
- URL: `http://wordpress.local:30080/wp-admin`
- Create posts, pages, themes
- Install plugins
- Configure settings

**Test Persistence:**
```bash
# Create a post in WordPress

# Delete WordPress pod
kubectl delete pod -l app=wordpress

# Visit site again - content is still there!
```

**Production Considerations:**
- Use managed MySQL (RDS, Cloud SQL)
- Horizontal pod autoscaling for WordPress
- Use object storage for uploads (S3)
- Enable caching (Redis, Memcached)
- SSL/TLS with cert-manager
- Regular database backups
- CDN for static assets
- Monitor performance

---

### 5.4 Grafana - Monitoring Dashboard

**Use Case:** Visualization and monitoring dashboard

```bash
kubectl apply -f workloads/05-real-apps/grafana.yaml
```

**Access Grafana:**
```bash
# Get NodePort
kubectl get svc grafana
# NAME      TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
# grafana   NodePort   10.96.123.45   <none>        3000:30300/TCP   1m

# Visit: http://<worker-ip>:30300
# Default credentials: admin / admin
```

**First Login:**
1. Login with admin/admin
2. You'll be prompted to change password
3. Set new password
4. Explore the interface

**Grafana Features:**
- Dashboards with panels
- Data sources (Prometheus, MySQL, etc.)
- Alerting rules
- User management
- Dashboard sharing

**Next Steps with Grafana:**
1. Add Prometheus as data source (Exercise 6)
2. Import Kubernetes dashboards
3. Create custom dashboards
4. Set up alerts

---

## Common Patterns and Best Practices

### 1. ConfigMaps - External Configuration

Decouple configuration from application code.

**Create ConfigMap:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  # Key-value pairs
  database_url: "postgres://db:5432/myapp"
  log_level: "info"
  feature_flags: |
    feature_a: true
    feature_b: false
  # Entire files
  nginx.conf: |
    server {
      listen 80;
      server_name _;
      location / {
        root /usr/share/nginx/html;
      }
    }
```

**Use as Environment Variables:**
```yaml
spec:
  containers:
  - name: app
    env:
    - name: DATABASE_URL
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database_url
    - name: LOG_LEVEL
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: log_level
```

**Mount as Files:**
```yaml
spec:
  containers:
  - name: nginx
    volumeMounts:
    - name: config
      mountPath: /etc/nginx/conf.d
  volumes:
  - name: config
    configMap:
      name: app-config
      items:
      - key: nginx.conf
        path: default.conf
```

**Create from Command Line:**
```bash
# From literal values
kubectl create configmap app-config \
  --from-literal=database_url=postgres://db:5432/myapp \
  --from-literal=log_level=info

# From file
kubectl create configmap nginx-config \
  --from-file=nginx.conf

# From directory
kubectl create configmap app-config --from-file=config/
```

---

### 2. Secrets - Sensitive Data

Never put passwords, tokens, or keys in plain text!

**Create Secret:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
stringData:  # Will be base64 encoded
  username: admin
  password: MySecretPassword123!
data:  # Already base64 encoded
  api_key: YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo=
```

**Use as Environment Variables:**
```yaml
spec:
  containers:
  - name: app
    env:
    - name: DB_USERNAME
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: username
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: password
```

**Mount as Files:**
```yaml
spec:
  containers:
  - name: app
    volumeMounts:
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secrets
    secret:
      secretName: db-credentials
```

**Create from Command Line:**
```bash
# From literal
kubectl create secret generic db-secret \
  --from-literal=username=admin \
  --from-literal=password=secret123

# From file
kubectl create secret generic ssh-key \
  --from-file=ssh-privatekey=~/.ssh/id_rsa

# TLS secret
kubectl create secret tls tls-secret \
  --cert=path/to/cert.crt \
  --key=path/to/key.key
```

**⚠️ Security Notes:**
- Secrets are base64 encoded, **NOT encrypted** by default
- Enable encryption at rest in production
- Use external secret management (Vault, Sealed Secrets)
- Limit RBAC access to secrets
- Rotate secrets regularly

---

### 3. Resource Management

Prevent resource starvation and ensure fair allocation.

**Resource Requests and Limits:**
```yaml
spec:
  containers:
  - name: app
    resources:
      requests:         # Guaranteed resources
        memory: "256Mi"  # Minimum memory
        cpu: "250m"      # 0.25 CPU cores
      limits:           # Maximum resources
        memory: "512Mi"  # Pod killed if exceeded (OOMKilled)
        cpu: "500m"      # Throttled if exceeded
```

**CPU Units:**
- `1` = 1 CPU core
- `1000m` = 1 CPU core
- `500m` = 0.5 CPU core (half a core)
- `100m` = 0.1 CPU core

**Memory Units:**
- `Mi` = Mebibytes (1024^2)
- `Gi` = Gibibytes (1024^3)
- `M` = Megabytes (1000^2)
- `G` = Gigabytes (1000^3)

**Quality of Service (QoS) Classes:**

| Class | Condition | Behavior |
|-------|-----------|----------|
| **Guaranteed** | requests = limits | Last to be evicted |
| **Burstable** | requests < limits | Evicted if needed |
| **BestEffort** | No requests/limits | First to be evicted |

**Best Practices:**
- Always set requests (for scheduling)
- Set limits to prevent resource hogging
- Monitor actual usage and adjust
- Use LimitRanges and ResourceQuotas for namespace-level controls

---

### 4. Health Checks

Kubernetes can automatically restart unhealthy containers.

**Liveness Probe** - Is the container healthy?
```yaml
spec:
  containers:
  - name: app
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 30  # Wait before first check
      periodSeconds: 10        # Check every 10s
      timeoutSeconds: 5        # Timeout after 5s
      failureThreshold: 3      # Restart after 3 failures
```

**Readiness Probe** - Is the container ready for traffic?
```yaml
spec:
  containers:
  - name: app
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
      successThreshold: 1
      failureThreshold: 3
```

**Startup Probe** - Has the container started?
```yaml
spec:
  containers:
  - name: slow-app
    startupProbe:
      httpGet:
        path: /startup
        port: 8080
      initialDelaySeconds: 0
      periodSeconds: 10
      failureThreshold: 30  # 30 * 10 = 300s max startup time
```

**Probe Types:**
- `httpGet`: HTTP GET request
- `tcpSocket`: TCP connection
- `exec`: Run command in container

**Example: TCP Probe**
```yaml
livenessProbe:
  tcpSocket:
    port: 3306
  initialDelaySeconds: 15
  periodSeconds: 20
```

**Example: Exec Probe**
```yaml
livenessProbe:
  exec:
    command:
    - cat
    - /tmp/healthy
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

### 5. Pod Lifecycle

**Init Containers** - Run before main containers
```yaml
spec:
  initContainers:
  - name: init-db
    image: busybox
    command: ['sh', '-c', 'until nc -z db 5432; do sleep 1; done']
  containers:
  - name: app
    image: myapp:1.0
```

**Use cases:**
- Wait for dependencies
- Database migrations
- Download configuration
- Pre-populate data

**Pod Termination Lifecycle:**
1. SIGTERM sent to containers
2. Grace period (default 30s)
3. SIGKILL if still running

**Graceful Shutdown:**
```yaml
spec:
  containers:
  - name: app
    lifecycle:
      preStop:
        exec:
          command: ["/bin/sh", "-c", "sleep 15"]
  terminationGracePeriodSeconds: 30
```

---

## Troubleshooting Guide

### Pod Issues

**Pod Stuck in Pending**
```bash
kubectl describe pod <pod-name>

# Common causes:
# - Insufficient resources (CPU/memory)
# - No nodes match nodeSelector/affinity
# - PVC not bound
# - Image pull secrets missing

# Check node resources
kubectl describe nodes
kubectl top nodes  # Requires metrics-server
```

**Pod in CrashLoopBackOff**
```bash
kubectl logs <pod-name>
kubectl logs <pod-name> --previous  # Previous crash logs

# Common causes:
# - Application error
# - Wrong command/entrypoint
# - Missing configuration
# - Failed liveness probe
```

**Pod in ImagePullBackOff**
```bash
kubectl describe pod <pod-name>

# Common causes:
# - Image doesn't exist
# - Wrong image name/tag
# - Private registry needs credentials
# - Network issues
```

**Pod in Evicted State**
```bash
kubectl get pods | grep Evicted

# Causes:
# - Node out of resources
# - Disk pressure
# - Memory pressure

# Clean up evicted pods
kubectl delete pods --field-selector=status.phase=Failed
```

---

### Service Issues

**Service Not Accessible**
```bash
# Check service
kubectl get svc <service-name>
kubectl describe svc <service-name>

# Check endpoints (should list pod IPs)
kubectl get endpoints <service-name>

# If no endpoints:
# 1. Check if pods are running
kubectl get pods -l <label-selector>

# 2. Check if pod labels match service selector
kubectl get pods --show-labels
kubectl describe svc <service-name> | grep Selector

# 3. Check pod port matches service targetPort
kubectl get pods -o wide
```

**DNS Not Working**
```bash
# Test DNS from pod
kubectl run test --image=busybox --rm -it --restart=Never -- nslookup kubernetes.default

# Check CoreDNS
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns
```

---

### Network Issues

**Pod-to-Pod Communication**
```bash
# Get pod IPs
kubectl get pods -o wide

# Test connectivity
kubectl exec <pod1> -- ping <pod2-ip>
kubectl exec <pod1> -- nc -zv <pod2-ip> <port>
```

**Network Policies Blocking Traffic**
```bash
# List network policies
kubectl get networkpolicies

# Describe policy
kubectl describe networkpolicy <policy-name>
```

---

### Storage Issues

**PVC Not Binding**
```bash
kubectl get pvc

# If Pending:
kubectl describe pvc <pvc-name>

# Check storage classes
kubectl get storageclass

# Check persistent volumes
kubectl get pv
```

**Data Not Persisting**
```bash
# Check if volume is mounted correctly
kubectl describe pod <pod-name>

# Check volume mount path
kubectl exec <pod-name> -- ls -la <mount-path>

# Check PVC is bound
kubectl get pvc
```

---

### General Debugging

**Get Events**
```bash
# All events in namespace
kubectl get events --sort-by='.lastTimestamp'

# Events for specific resource
kubectl get events --field-selector involvedObject.name=<pod-name>
```

**Check Resource Usage**
```bash
# Node resources
kubectl top nodes

# Pod resources
kubectl top pods

# Specific pod
kubectl top pod <pod-name>
```

**Debug with Temporary Pod**
```bash
# Busybox for basic testing
kubectl run debug --image=busybox --rm -it --restart=Never -- sh

# Curl for HTTP testing
kubectl run debug --image=curlimages/curl --rm -it --restart=Never -- sh

# Network tools
kubectl run debug --image=nicolaka/netshoot --rm -it --restart=Never -- sh
```

**Port Forward for Local Testing**
```bash
# Forward pod port
kubectl port-forward pod/<pod-name> 8080:80

# Forward service port
kubectl port-forward svc/<service-name> 8080:80

# Forward deployment port
kubectl port-forward deployment/<deployment-name> 8080:80
```

---

## Essential kubectl Commands Reference

### Get Resources
```bash
kubectl get pods                    # List pods
kubectl get pods -o wide           # More details
kubectl get pods --show-labels     # Show labels
kubectl get pods -l app=nginx      # Filter by label
kubectl get pods -A                # All namespaces
kubectl get all                    # All resources
```

### Describe (Detailed Info)
```bash
kubectl describe pod <name>
kubectl describe svc <name>
kubectl describe node <name>
```

### Logs
```bash
kubectl logs <pod>                 # Current logs
kubectl logs -f <pod>              # Follow logs
kubectl logs <pod> -c <container>  # Specific container
kubectl logs <pod> --previous      # Previous container logs
kubectl logs -l app=nginx          # Logs from label selector
```

### Execute Commands
```bash
kubectl exec <pod> -- ls           # Run command
kubectl exec -it <pod> -- bash     # Interactive shell
kubectl exec <pod> -c <container> -- sh  # Specific container
```

### Apply/Create/Delete
```bash
kubectl apply -f file.yaml         # Create/update
kubectl create -f file.yaml        # Create only
kubectl delete -f file.yaml        # Delete from file
kubectl delete pod <name>          # Delete by name
kubectl delete all --all           # Delete everything
```

### Edit Resources
```bash
kubectl edit pod <name>            # Edit in $EDITOR
kubectl edit deployment <name>
kubectl patch deployment <name> -p '{"spec":{"replicas":3}}'
```

### Scale
```bash
kubectl scale deployment <name> --replicas=5
kubectl autoscale deployment <name> --min=2 --max=10 --cpu-percent=80
```

### Rollout Management
```bash
kubectl rollout status deployment/<name>
kubectl rollout history deployment/<name>
kubectl rollout undo deployment/<name>
kubectl rollout restart deployment/<name>
```

### Port Forwarding
```bash
kubectl port-forward pod/<name> 8080:80
kubectl port-forward svc/<name> 8080:80
```

### Copy Files
```bash
kubectl cp <pod>:/path/to/file ./local-file
kubectl cp ./local-file <pod>:/path/to/file
```

### Labels and Annotations
```bash
kubectl label pod <name> env=prod
kubectl annotate pod <name> description="My pod"
```

### Namespace Management
```bash
kubectl create namespace dev
kubectl config set-context --current --namespace=dev
kubectl get pods -n kube-system
```

### Context and Config
```bash
kubectl config view
kubectl config get-contexts
kubectl config use-context <context-name>
```

---

## What's Next?

Congratulations! You've learned the fundamentals of deploying applications on Kubernetes. Here are recommended next steps:

### Phase 4: Storage Deep Dive
- PersistentVolumes and StorageClasses
- StatefulSets for stateful applications
- Dynamic provisioning
- Volume snapshots and cloning

### Phase 5: Configuration Management
- Helm package manager
- Kustomize for configuration overlays
- GitOps with ArgoCD or FluxCD
- Managing multiple environments

### Phase 6: Observability
- Prometheus for metrics
- Grafana dashboards
- ELK stack or Loki for logs
- Distributed tracing with Jaeger
- Alerting rules

### Phase 7: Advanced Topics
- Network Policies for security
- RBAC and security
- Horizontal Pod Autoscaler (HPA)
- Vertical Pod Autoscaler (VPA)
- Pod Disruption Budgets
- Admission controllers
- Service mesh (Istio, Linkerd)

### Phase 8: CI/CD Integration
- Jenkins/GitLab CI with Kubernetes
- GitHub Actions
- Tekton Pipelines
- Automated testing in Kubernetes
- Blue/green deployments
- Canary deployments

### Resources
- **Official Docs**: https://kubernetes.io/docs/
- **Kubernetes Blog**: https://kubernetes.io/blog/
- **CNCF Projects**: https://www.cncf.io/projects/
- **kubectl Cheat Sheet**: https://kubernetes.io/docs/reference/kubectl/cheatsheet/

---

## Clean Up

When you're done practicing, clean up resources:

```bash
# Delete all workloads
kubectl delete all --all

# Delete PVCs (separate command needed)
kubectl delete pvc --all

# Delete ingress resources
kubectl delete ingress --all

# Destroy the cluster (to save costs)
cd ansible
ansible-playbook destroy.yml
```

---

**Keep learning and experimenting! Kubernetes is vast, but you've built a solid foundation.** 🚀

The best way to learn is by doing - deploy your own applications, break things, fix them, and repeat!

# Ingress Examples

Ingress provides HTTP/HTTPS routing to services based on hostnames and paths.

## What is Ingress?

Ingress exposes HTTP and HTTPS routes from outside the cluster to services within the cluster. It provides:
- **Host-based routing** (app1.example.com → service1)
- **Path-based routing** (/api → api-service, /web → web-service)
- **SSL/TLS termination**
- **Load balancing**

## Installation

### Step 1: Install Ingress Controller

```bash
kubectl apply -f ingress-controller.yaml
```

This installs the NGINX Ingress Controller in the `ingress-nginx` namespace.

**Wait for it to be ready:**
```bash
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
```

### Step 2: Deploy Applications

```bash
kubectl apply -f app1.yaml
kubectl apply -f app2.yaml
```

### Step 3: Create Ingress Rules

```bash
kubectl apply -f ingress-rules.yaml
```

## Access Your Applications

### Get the Ingress Controller IP

```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller
```

Note the NodePort (30080 for HTTP).

### Configure DNS

Add to your `/etc/hosts` file on your local machine:

```
<worker-node-ip> app1.local app2.local
```

Replace `<worker-node-ip>` with the IP of your worker node from `ansible/inventory.ini`.

### Test

```bash
curl http://app1.local:30080
curl http://app2.local:30080
```

Or visit in browser:
- http://app1.local:30080
- http://app2.local:30080

## How It Works

1. **Ingress Controller** watches for Ingress resources
2. **Ingress Rules** define routing based on:
   - Host header (`app1.local`, `app2.local`)
   - Path (`/`, `/api`, etc.)
3. **Traffic flow:**
   ```
   Client → Ingress Controller → Service → Pods
   ```

## Path-Based Routing Example

You can route based on URL paths:

```yaml
rules:
- host: example.com
  http:
    paths:
    - path: /api
      backend:
        service:
          name: api-service
    - path: /web
      backend:
        service:
          name: web-service
```

## View Ingress Resources

```bash
# List ingress resources
kubectl get ingress

# Detailed info
kubectl describe ingress example-ingress

# View controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

## Clean up

```bash
kubectl delete -f ingress-rules.yaml
kubectl delete -f app1.yaml
kubectl delete -f app2.yaml

# Optional: Remove ingress controller
kubectl delete -f ingress-controller.yaml
```

## Key Concepts

- **Ingress Controller** implements the actual routing logic (nginx, traefik, etc.)
- **Ingress Resource** defines the routing rules
- **One controller** can handle multiple Ingress resources
- **Host-based routing** uses HTTP Host header
- **Path-based routing** uses URL path
- More efficient than NodePort for multiple services


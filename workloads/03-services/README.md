# Service Examples

Services provide stable networking for ephemeral pods.

## Service Types

### ClusterIP (Default)
- Internal-only access
- Pods within cluster can access via service name
- Use for databases, internal APIs

### NodePort
- External access via `<NodeIP>:<NodePort>`
- Exposes service on each node's IP at a static port
- Port range: 30000-32767

### LoadBalancer
- Creates external load balancer (cloud provider)
- Assigns external IP
- Not covered here (requires cloud provider support)

## nginx-clusterip.yaml

Deployment + ClusterIP service (internal only).

**Deploy:**
```bash
kubectl apply -f nginx-clusterip.yaml
```

**Test from within cluster:**
```bash
kubectl run test-pod --image=busybox --rm -it --restart=Never -- wget -qO- nginx-clusterip
```

**View service:**
```bash
kubectl get svc nginx-clusterip
kubectl describe svc nginx-clusterip
```

## nginx-nodeport.yaml

Deployment + NodePort service (external access).

**Deploy:**
```bash
kubectl apply -f nginx-nodeport.yaml
```

**Access externally:**
```bash
kubectl get svc nginx-nodeport
# Note the NodePort (30080 in this example)

# Access from outside cluster
curl http://<worker-node-ip>:30080
```

## Service Discovery

Services automatically get DNS names:
- `<service-name>` (within same namespace)
- `<service-name>.<namespace>.svc.cluster.local` (full FQDN)

**Test DNS:**
```bash
kubectl run test-pod --image=busybox --rm -it --restart=Never -- sh

# Inside pod:
wget -qO- nginx-clusterip
wget -qO- nginx-clusterip.default.svc.cluster.local
```

## Clean up

```bash
kubectl delete -f nginx-clusterip.yaml
kubectl delete -f nginx-nodeport.yaml
```

## Key Concepts

- Services provide **stable IPs** for dynamic pod IPs
- **Label selectors** determine which pods service routes to
- **ClusterIP** for internal, **NodePort** for external access
- Services perform **load balancing** across pod replicas
- **DNS names** enable service discovery


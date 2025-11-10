# Deployment Examples

Deployments manage ReplicaSets and provide declarative updates to Pods.

## nginx-deployment.yaml

Nginx deployment with 3 replicas and resource limits.

**Deploy:**
```bash
kubectl apply -f nginx-deployment.yaml
```

**Check status:**
```bash
kubectl get deployments
kubectl get replicasets
kubectl get pods
```

**Scale:**
```bash
# Scale up
kubectl scale deployment nginx-deployment --replicas=5

# Scale down
kubectl scale deployment nginx-deployment --replicas=2
```

**Update image:**
```bash
kubectl set image deployment/nginx-deployment nginx=nginx:1.25

# Watch rollout
kubectl rollout status deployment/nginx-deployment

# View history
kubectl rollout history deployment/nginx-deployment
```

**Rollback:**
```bash
kubectl rollout undo deployment/nginx-deployment
```

**Clean up:**
```bash
kubectl delete deployment nginx-deployment
```

## Key Concepts

- **Deployments** manage ReplicaSets
- **ReplicaSets** ensure desired number of pod replicas
- **Rolling updates** deploy new versions without downtime
- **Rollback** to previous versions if issues occur
- **Self-healing** - automatically replaces failed pods


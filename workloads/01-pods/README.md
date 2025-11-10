# Pod Examples

Basic pod manifests to understand Kubernetes pods.

## nginx-pod.yaml

Simple nginx web server pod.

**Deploy:**
```bash
kubectl apply -f nginx-pod.yaml
```

**Access:**
```bash
kubectl port-forward pod/nginx 8080:80
# Visit http://localhost:8080
```

**Clean up:**
```bash
kubectl delete pod nginx
```

## Key Concepts

- Pods are the smallest deployable units
- Can contain one or more containers
- Share network namespace (localhost communication)
- Ephemeral - if deleted, they don't come back automatically


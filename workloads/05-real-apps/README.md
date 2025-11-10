# Real Application Examples

Production-like applications demonstrating various Kubernetes patterns.

## Applications

### 1. Redis - Stateless Cache

Simple in-memory cache, no persistent storage.

**Deploy:**
```bash
kubectl apply -f redis.yaml
```

**Test:**
```bash
kubectl run redis-test --image=redis --rm -it --restart=Never -- redis-cli -h redis

# Inside redis-cli:
SET mykey "Hello Kubernetes"
GET mykey
KEYS *
```

**Use cases:**
- Session storage
- Caching
- Message queue
- Real-time analytics

---

### 2. PostgreSQL - Stateful Database

Relational database with persistent storage.

**Deploy:**
```bash
kubectl apply -f postgres.yaml
```

**Test:**
```bash
kubectl exec -it deployment/postgres -- psql -U admin -d mydb

# Inside psql:
CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(100), email VARCHAR(100));
INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');
INSERT INTO users (name, email) VALUES ('Bob', 'bob@example.com');
SELECT * FROM users;
\q
```

**Key features:**
- PersistentVolumeClaim for data persistence
- Data survives pod restarts
- ConfigMap/Secret for credentials (in production)

---

### 3. WordPress - Multi-Tier Application

Complete web application with database backend.

**Deploy:**
```bash
# Deploy MySQL first
kubectl apply -f wordpress/mysql.yaml

# Wait for MySQL to be ready
kubectl get pods -w

# Deploy WordPress
kubectl apply -f wordpress/wordpress.yaml
```

**Access:**
```bash
# Get ingress controller IP
kubectl get svc -n ingress-nginx ingress-nginx-controller

# Add to /etc/hosts:
# <worker-ip> wordpress.local

# Visit: http://wordpress.local:30080
```

**Components:**
- MySQL database with persistent storage
- WordPress frontend with persistent storage
- Secret for database credentials
- ClusterIP services for internal communication
- Ingress for external access

**Complete setup:**
1. Visit WordPress in browser
2. Select language
3. Create admin account
4. Start blogging!

---

### 4. Grafana - Dashboard Application

Monitoring and visualization dashboard.

**Deploy:**
```bash
kubectl apply -f grafana.yaml
```

**Access:**
```bash
# Get the NodePort
kubectl get svc grafana

# Visit: http://<worker-ip>:30300
# Default credentials: admin / admin
```

**First login:**
1. Login with admin/admin
2. Change password when prompted
3. Explore the dashboard

**What's next:**
- Add Prometheus as data source
- Create dashboards
- Monitor your cluster

---

## Patterns Demonstrated

### ConfigMaps
Environment-specific configuration:
```yaml
env:
- name: DATABASE_URL
  valueFrom:
    configMapKeyRef:
      name: app-config
      key: database_url
```

### Secrets
Sensitive data like passwords:
```yaml
env:
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: mysql-secret
      key: password
```

### Persistent Storage
Data that survives pod restarts:
```yaml
volumeMounts:
- name: data
  mountPath: /var/lib/mysql
volumes:
- name: data
  persistentVolumeClaim:
    claimName: mysql-pvc
```

### Resource Limits
Prevent resource starvation:
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Multi-Container Pods
(Not shown in these examples, but possible):
```yaml
containers:
- name: app
  image: myapp
- name: sidecar
  image: logging-agent
```

---

## Clean Up

Remove individual apps:
```bash
kubectl delete -f redis.yaml
kubectl delete -f postgres.yaml
kubectl delete -f grafana.yaml
kubectl delete -f wordpress/
```

Or delete everything in the namespace:
```bash
kubectl delete all --all
kubectl delete pvc --all
```

---

## Production Considerations

These examples are for learning. For production:

### Security
- Use proper Secrets management (Sealed Secrets, Vault)
- Don't hardcode passwords
- Enable RBAC
- Use NetworkPolicies
- Scan images for vulnerabilities

### High Availability
- Multiple replicas
- Pod disruption budgets
- Anti-affinity rules
- Multiple availability zones

### Backup & Recovery
- Regular backups of PersistentVolumes
- Database backups
- Disaster recovery plan
- Test restore procedures

### Monitoring
- Prometheus for metrics
- Grafana for visualization
- Logging (ELK stack, Loki)
- Alerting rules

### Performance
- Proper resource requests/limits
- Horizontal Pod Autoscaling
- Optimize container images
- Use caching effectively

### Storage
- Choose appropriate StorageClass
- Consider stateful workload requirements
- Plan for data growth
- Backup strategy

---

## Troubleshooting

### Pod stuck in Pending
```bash
kubectl describe pod <pod-name>
# Check: Events section for scheduling issues
```

### Database connection refused
```bash
# Check service endpoints
kubectl get endpoints mysql

# Test connectivity
kubectl run test --image=busybox --rm -it --restart=Never -- sh
nc -zv mysql 3306
```

### PVC not binding
```bash
kubectl get pvc
kubectl describe pvc <pvc-name>

# Check if StorageClass exists
kubectl get storageclass
```

### Application crashing
```bash
# Check logs
kubectl logs <pod-name>

# Check previous logs if crashed
kubectl logs <pod-name> --previous

# Check events
kubectl get events --sort-by='.lastTimestamp'
```

---

## Next Steps

- Try modifying these apps
- Add health checks (liveness/readiness probes)
- Implement proper secrets management
- Add monitoring with Prometheus
- Try deploying your own applications
- Learn about Helm for package management


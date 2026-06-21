# Disaster Recovery Plan (DRP)

## Objective
Ensure business continuity during infrastructure outages, deployment failures, or extreme market volatility.

## High Availability Configuration
- **Compute:** Risk Engine and Analytics API run with multiple replicas across 3 Availability Zones (AZs).
- **Auto-Scaling:** Horizontal Pod Autoscalers (HPA) automatically scale Risk Engine pods from 5 to 20 when CPU utilization exceeds 75%. EKS cluster autoscaler adds EC2 nodes as required.
- **Database:** PostgreSQL runs as a StatefulSet. In production, this maps to Amazon RDS Multi-AZ for seamless failover.

## Recovery Scenarios

### 1. Pod/Service Failure
- **Detection:** Liveness probes fail after 3 timeouts.
- **Recovery:** Kubernetes automatically restarts the failed pod. Traffic is routed to healthy pods by the Service.

### 2. Deployment Failure (Bad Code)
- **Detection:** Readiness probes fail or Jenkins pipeline tests fail.
- **Recovery:** Kubernetes halts the rolling update. Jenkins executes `kubectl rollout undo deployment/<name>` automatically.

### 3. AZ Outage
- **Detection:** Node becomes unreachable.
- **Recovery:** EKS provisions replacement nodes in healthy AZs. Kubernetes reschedules pods.

### 4. Database Failure
- **Detection:** API connection timeouts.
- **Recovery:** RDS automatically promotes the standby replica to master. DNS endpoints update seamlessly.

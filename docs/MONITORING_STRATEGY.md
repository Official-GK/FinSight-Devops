# Monitoring Strategy

## Overview
The FinSight platform uses a modern observability stack (Prometheus, Grafana, ELK) to monitor application health, infrastructure performance, and business metrics.

## Metrics Collection (Prometheus)
- **Infrastructure Metrics:** Scrapes Kubernetes nodes and pods for CPU and memory usage to feed the Horizontal Pod Autoscalers (HPA).
- **Application Metrics:** Scrapes `/metrics` endpoints from the FastAPI applications to monitor:
  - Request Rate (RPS)
  - Latency (Response Time)
  - Active Pods

## Visualization (Grafana)
Grafana dashboards are provisioned dynamically via `datasources.yaml`.
- **System Dashboard:** Shows CPU, memory, and network throughput across the cluster.
- **Business Dashboard:** Shows Risk Analysis throughput and average risk scores over time.

## Centralized Logging (ELK)
- **Filebeat** runs as a DaemonSet to capture logs from all Docker containers.
- **Logstash** filters logs based on the container name and adds tags (`api`, `risk_engine`).
- **Elasticsearch** indexes the logs daily.
- **Kibana** allows searching for specific transaction IDs and scaling events across all microservices.

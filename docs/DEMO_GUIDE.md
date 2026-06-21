# FinSight Demo Guide

## Purpose
This guide walks through how to demonstrate the key DevOps features of the platform for the case study evaluation.

## Scenario 1: Market Volatility Simulation (Auto-Scaling)
1. Open the Frontend Dashboard.
2. Click **Demo Mode**. This simulates a massive spike in transaction volume.
3. Show the Grafana CPU Dashboard or run `kubectl get hpa -w`.
4. **Expected Result:** The HPA will detect CPU utilization exceeding 75% and dynamically scale the `risk-engine` pods up to 20 to handle the bottleneck.

## Scenario 2: Infrastructure Outage (Pod Recovery)
1. In the terminal, find a risk engine pod: `kubectl get pods | grep risk-engine`.
2. Delete the pod manually: `kubectl delete pod <pod-name>`.
3. **Expected Result:** The frontend dashboard will not show any downtime or 502 errors. K8s will immediately provision a replacement pod.

## Scenario 3: Deployment Rollback
1. Trigger a Jenkins build but artificially fail the readiness probe (e.g., change the port in the K8s manifest).
2. **Expected Result:** The deployment will halt. The Jenkins pipeline will fail at the "Verify Deployment" stage and execute the rollback command, returning the system to version 1.0.

## Scenario 4: Observability
1. Show the **System Logs** on the dashboard.
2. Open Kibana and search for `tags: risk_engine` to demonstrate centralized logging.
3. Open Grafana and show the request latency and throughput dashboards.

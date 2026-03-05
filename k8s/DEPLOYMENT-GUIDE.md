# PrimePass Kubernetes Deployment Guide

This README provides instructions for deploying and managing the PrimePass application on Kubernetes (Minikube). All Kubernetes configuration files are located in the `k8s/` directory.

## 📋 Prerequisites

- [Minikube](https://minikube.sigs.k8s.io/docs/start/) installed and running
- [kubectl](https://kubernetes.io/docs/tasks/tools/) installed
- Docker installed
- The PrimePass project cloned locally

## 🚀 Quick Start

### 1. Start Minikube

    minikube start

### 2. Build and Load Images into Minikube

For each service, build the Docker image directly in Minikube's Docker environment.

**Backend:**

    # Point your shell to Minikube's Docker daemon
    eval $(minikube docker-env)

    # Build the backend image
    cd backend
    docker build -t backend:latest .
    cd ..

**Frontend:**

    # Still in minikube's Docker environment
    cd frontend
    docker build -t frontend:latest .
    cd ..

### 3. Deploy All Kubernetes Resources

Apply all YAML files in the correct order:

    cd k8s
    kubectl apply -f postgres-replication-secret.yaml
    kubectl apply -f postgres-primary-statefulset.yaml
    kubectl apply -f postgres-replica-statefulset.yaml
    kubectl apply -f postgres-primary-service.yaml
    kubectl apply -f postgres-replica-service.yaml
    # Then reapply backend, frontend, configmap, etc. if they were deleted
    kubectl apply -f ../backend-deployment.yaml
    kubectl apply -f ../backend-service.yaml
    kubectl apply -f ../frontend-deployment.yaml
    kubectl apply -f ../frontend-service.yaml

    cd ..

### 4. Verify Deployments

Check that all pods are running:

    kubectl get pods

You should see three pods: `backend`, `frontend`, and `postgres` all with `Running` status.

### 5. Access the Application

#### Option A: Port-Forwarding (Simple)

    # Terminal 1 - Frontend
    kubectl port-forward svc/frontend 8080:80

    # Terminal 2 - Backend (if needed for API testing)
    kubectl port-forward svc/backend 5000:5000

Then open `http://localhost:8080` in your browser.

#### Option B: Minikube Tunnel (Recommended)

Modify `frontend-service.yaml` to use `type: LoadBalancer`, then in a dedicated terminal:

    minikube tunnel

The app will be available at `http://localhost:80` (or `http://localhost:8080` if you changed the port).

## 🔄 Making Code Changes

### Rebuilding Images After Code Changes

Whenever you modify the backend or frontend code, rebuild and restart:

**Backend:**

    eval $(minikube docker-env)
    cd backend
    docker build -t backend:latest .
    cd ..
    kubectl rollout restart deployment backend

**Frontend:**

    eval $(minikube docker-env)
    cd frontend
    docker build -t frontend:latest .
    cd ..
    kubectl rollout restart deployment frontend

### Verify Changes Were Applied

    # Check if new pods are running
    kubectl get pods -w

    # View the new code in the pod
    kubectl exec <backend-pod-name> -- cat /app/server.py
    kubectl exec <frontend-pod-name> -- ls -la /usr/share/nginx/html

## 📊 Logs and Debugging

### View Logs

**Backend logs:**

    # Follow logs continuously
    kubectl logs -f deployment/backend

    # Get last 100 lines
    kubectl logs --tail=100 deployment/backend

    # Logs from a specific pod
    kubectl logs <backend-pod-name>

    # Previous instance logs (if pod restarted)
    kubectl logs <backend-pod-name> --previous

**Frontend logs:**

    kubectl logs -f deployment/frontend

**PostgreSQL logs:**

    kubectl logs -f deployment/postgres

### Common Debugging Commands

**Describe a pod** (shows events and details):

    kubectl describe pod <pod-name>

**Get all resources in the namespace:**

    kubectl get all

**Check service endpoints:**

    kubectl get endpoints

**Execute commands inside a pod:**

    # Backend
    kubectl exec -it <backend-pod> -- /bin/bash

    # Frontend
    kubectl exec -it <frontend-pod> -- /bin/sh

    # PostgreSQL
    kubectl exec -it <postgres-pod> -- psql -U appuser -d primepass_db

## 🛑 Restarting and Cleanup

### Restart Deployments

    # Restart individual deployments
    kubectl rollout restart deployment backend
    kubectl rollout restart deployment frontend
    kubectl rollout restart deployment postgres

    # Restart all at once
    kubectl rollout restart deployment/backend deployment/frontend deployment/postgres

### Check Rollout Status

    kubectl rollout status deployment/backend
    kubectl rollout status deployment/frontend
    kubectl rollout status deployment/postgres

### Scale Deployments

    # Scale to 3 replicas
    kubectl scale deployment backend --replicas=3

    # Scale down to 1
    kubectl scale deployment backend --replicas=1

### Delete Everything

    # Delete all resources
    kubectl delete -f k8s/

    # Or delete selectively
    kubectl delete deployment backend frontend postgres
    kubectl delete service backend frontend primepass-primary
    kubectl delete pvc postgres-volume-claim
    kubectl delete pv postgres-volume
    kubectl delete configmap postgres-config
    kubectl delete secret primepass-appuser

### Stop Minikube

    minikube stop

## 📝 Useful Commands Cheat Sheet

| Command | Description |
|---------|-------------|
| `kubectl get pods -w` | Watch pods in real-time |
| `kubectl logs -f deployment/backend` | Follow backend logs |
| `kubectl exec -it <pod> -- /bin/bash` | Shell into a pod |
| `kubectl port-forward svc/frontend 8080:80` | Access frontend locally |
| `eval $(minikube docker-env)` | Switch to minikube Docker env |
| `minikube tunnel` | Expose LoadBalancer services |
| `kubectl rollout restart deployment/backend` | Restart backend |
| `kubectl describe pod <pod>` | Debug pod issues |
| `kubectl delete -f k8s/` | Delete all resources |

## 🐛 Troubleshooting

### Pods stuck in `Pending` or `ContainerCreating`

    kubectl describe pod <pod-name>

Common issues:
- Insufficient resources (add nodes to minikube: `minikube node add`)
- PersistentVolume not bound (check PVC status)
- Image pull errors (ensure images are built in minikube's Docker)

### Backend can't connect to PostgreSQL

    # Check if PostgreSQL is running
    kubectl get pods -l app=postgres

    # Verify service exists
    kubectl get svc primepass-primary

    # Test connection from backend pod
    kubectl exec -it <backend-pod> -- ping primepass-primary

### Frontend shows no events

    # Check backend logs
    kubectl logs deployment/backend

    # Test API directly
    kubectl port-forward svc/backend 5000:5000
    # In another terminal
    curl http://localhost:5000/api/events

### Images not found

If you get `ErrImageNeverPull` or `ImagePullBackOff`:

    # Ensure you're in minikube's Docker environment
    eval $(minikube docker-env)

    # Rebuild images
    docker build -t backend:latest ./backend
    docker build -t frontend:latest ./frontend

    # Restart deployments
    kubectl rollout restart deployment/backend deployment/frontend
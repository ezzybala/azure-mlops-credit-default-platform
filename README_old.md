# Credit Default Prediction Platform on Azure

A production-style MLOps project demonstrating how to deploy, monitor, secure, and operate a machine learning inference service on Microsoft Azure.

This project implements an end-to-end credit default prediction solution using Azure Machine Learning, Azure Kubernetes Service (AKS), Helm, Managed Identity, Application Insights, and Azure Monitor. The goal is not only to serve predictions, but also to showcase the engineering practices required to run machine learning workloads in a cloud-native production environment.

---

## Project Goals

This project was built to demonstrate practical skills in:

- Machine Learning Operations (MLOps)
- Cloud-native application deployment
- Kubernetes administration
- Secure authentication and authorization
- CI/CD automation
- Observability and monitoring
- Production-grade ML service operation

The project is being developed incrementally, with new capabilities added and documented throughout its lifecycle.

---

## Solution Architecture

```text
                    +--------------------+
                    |   Client Request   |
                    +---------+----------+
                              |
                              v
                    +--------------------+
                    |   AKS Service      |
                    +---------+----------+
                              |
                              v
                    +--------------------+
                    |    FastAPI API     |
                    |  Model Inference   |
                    +---------+----------+
                              |
              +---------------+----------------+
              |                                |
              v                                v
    +------------------+          +--------------------------+
    | Azure ML Model   |          | Azure Application        |
    | Registry/Assets  |          | Insights                 |
    +------------------+          +------------+-------------+
                                               |
                                               v
                                  +--------------------------+
                                  | Azure Monitor            |
                                  | Log Analytics Workspace  |
                                  +--------------------------+
```

---

## Technology Stack

### Machine Learning

- Azure Machine Learning
- Scikit-learn
- MLflow

### Application Layer

- Python
- FastAPI
- Uvicorn

### Containerization & Orchestration

- Docker
- Kubernetes
- Azure Kubernetes Service (AKS)
- Helm

### Security

- Azure Managed Identity
- Azure Workload Identity
- Azure RBAC

### Observability

- Azure Application Insights
- Azure Monitor
- Log Analytics Workspace
- OpenTelemetry

### DevOps

- Azure DevOps Pipelines
- GitHub
- Azure Container Registry (ACR)

---

## Key Features

### Model Serving

- REST API for credit default prediction
- FastAPI-based inference service
- Containerized deployment

### Kubernetes Deployment

- AKS-hosted inference service
- Namespace isolation
- Replica-based scaling
- Kubernetes service discovery

### Secure Cloud Authentication

- Azure Workload Identity integration
- Kubernetes Service Account authentication
- Secretless access to Azure resources
- Role-Based Access Control (RBAC)

### Deployment Automation

- Helm chart packaging
- Environment-specific configuration
- CI/CD deployment pipeline

### Monitoring & Observability

- Request telemetry
- Distributed tracing
- Structured logging
- Container monitoring
- Health monitoring dashboards
- Performance analysis

---

## Repository Structure

```text
.
|-- README.md
|
|-- src/
|   |-- api/
|   |-- inference/
|   `-- model/
|
|-- helm/
|   `-- credit-default/
|
|-- kubernetes/
|   |-- service-account/
|   |-- workload-identity/
|   `-- manifests/
|
|-- pipelines/
|   `-- azure-devops/
|
|-- monitoring/
|   |-- workbooks/
|   |-- dashboards/
|   `-- alerts/
|
|-- docs/
|   |-- architecture.md
|   |-- deployment-guide.md
|   |-- monitoring.md
|   |-- progress-log.md
|   `-- screenshots/
|
|-- tests/
|
`-- requirements.txt
```

---

## Deployment Components

| Component | Purpose |
|---|---|
| Azure ML Workspace | ML asset management |
| Azure Container Registry | Container image storage |
| AKS | Application hosting |
| Helm | Kubernetes package management |
| Application Insights | Application telemetry |
| Azure Monitor | Platform monitoring |
| Log Analytics | Centralized log storage |
| Managed Identity | Secure Azure authentication |

---

## CI/CD Workflow

```text
Developer Push
       |
       v
GitHub Repository
       |
       v
Azure DevOps Pipeline
       |
       +--> Build Image
       |
       +--> Push to ACR
       |
       +--> Helm Upgrade
       |
       +--> Deploy to AKS
       |
       v
Production Environment
```

---

## Monitoring Strategy

### Phase 1 - Service Health ✅

Implemented:

- Application Insights integration
- OpenTelemetry instrumentation
- Request tracking
- Dependency tracking
- Container logs
- AKS health monitoring

Metrics monitored:

- Request count
- Request latency
- Failed requests
- Availability
- Container restarts
- Pod health

### Phase 2 - Operational Monitoring 🚧

Planned:

- Alert rules
- Dashboards
- Azure Monitor Workbooks
- Service-level indicators (SLIs)

### Phase 3 - Data Quality Monitoring 🚧

Planned:

- Data drift detection
- Input feature monitoring
- Dataset quality checks

### Phase 4 - Model Performance Monitoring 🚧

Planned:

- Prediction quality tracking
- Model accuracy monitoring
- Model retraining triggers

---

## Security Implementation

This project avoids long-lived credentials and uses Azure Workload Identity for secure authentication between Kubernetes workloads and Azure resources.

Security principles implemented:

- Least privilege access
- Managed identities
- RBAC authorization
- Workload Identity federation
- Secret minimization

This approach mirrors modern enterprise deployment practices and helps reduce credential management overhead.

---

## Lessons Learned

Building this project involved solving several real-world cloud engineering challenges:

- Configuring Azure Workload Identity on AKS
- Troubleshooting Managed Identity permissions
- Debugging Helm ownership conflicts
- Configuring OpenTelemetry instrumentation
- Integrating Application Insights with containerized applications
- Troubleshooting Kubernetes authentication flows
- Monitoring distributed services within Azure

These challenges provided practical experience beyond model development and closer to real production engineering environments.

---

## Future Enhancements

Planned improvements include:

- Prometheus integration
- Azure Managed Grafana dashboards
- Automated model retraining pipeline
- Data drift monitoring
- Blue-green deployment strategy
- Canary deployments
- Load testing and performance benchmarking
- Infrastructure as Code with Terraform
- GitOps deployment with FluxCD

---

## Screenshots

### AKS Deployment

> Add screenshots of healthy pods and services.

### Application Insights

> Add screenshots showing request telemetry and traces.

### Azure Monitor Workbook

> Add screenshots of operational dashboards.

### Azure DevOps Pipeline

> Add screenshots of successful deployments.

---

## Why This Project?

Many machine learning projects stop after model training.

This project focuses on the often-overlooked engineering work required to move models into production: deployment, security, automation, monitoring, and operational support.

The objective is to demonstrate the skills expected of an MLOps Engineer, Azure ML Engineer, Cloud Engineer, or Machine Learning Engineer working with production systems.

---

## Author

**Ezekiel Bala**

Passionate about building production-grade machine learning systems on Azure, with a focus on MLOps, cloud infrastructure, Kubernetes, observability, and platform engineering.

---

## License

MIT License
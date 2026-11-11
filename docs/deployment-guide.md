# Training and deployment guide

[Project overview](../README.md) | [Architecture](architecture.md) | [Monitoring guide](monitoring.md)

This guide explains how the existing pieces fit together and how to adapt the pattern to another Azure environment. It is a work in progress: Azure resources, permissions, model approval and some pipeline setup must be configured separately. Commands below use a Bash shell and start from the `azure-credit-default-mlops` project directory unless stated otherwise. Azure resources can incur charges.

## 1. Prerequisites

- An Azure subscription, resource group and Azure ML workspace, with appropriate permissions to create and use compute, data assets, environments, jobs and models.
- An Azure ML compute target and blob storage/container accessible to the workspace and training identity.
- Azure CLI signed in to the intended subscription. Training uses `AzureCliCredential`; serving uses `DefaultAzureCredential`.
- A Python environment for submitting training jobs. The project-level `requirements.txt` is currently empty; the submitter scripts import `azure-ai-ml`, `azure-identity`, `PyYAML` and `python-dotenv`. The Azure ML job environment is separately defined in `model_training/dependencies/conda.yaml`.
- Docker, Helm and `kubectl` for container build and AKS deployment; the Azure CLI Bicep tooling for infrastructure.
- For telemetry, an Application Insights resource and its connection string.

The job environment and serving Dockerfile currently use Python 3.8 and older ML dependencies. Check their compatibility and support status for your environment before reuse. Dataset licensing, consent and handling requirements are the responsibility of the operator.

## 2. Configure training

### Prepare data and Azure ML assets

1. Place the training CSV in a blob folder. The code expects the filename `default_of_credit_card_clients.csv`, a first metadata row followed by the column headers, an index in the first column, and the target column `default payment next month`. The feature names and order must be compatible with [`serving/schema.py`](../serving/schema.py) and [`serving/score.py`](../serving/score.py).
2. Register an Azure ML `uri_folder` data asset pointing at that folder. Ensure the job's identity can read the blob data. The repository has an optional datastore/data asset helper in [`model_training/src/datastore.py`](../model_training/src/datastore.py); review and adapt it before use.
3. Register an Azure ML environment with the dependencies in [`model_training/dependencies/conda.yaml`](../model_training/dependencies/conda.yaml). [`model_training/src/environment.py`](../model_training/src/environment.py) provides an environment registration example and also updates workspace image-build compute; review its permissions and side effects before running it.
4. Update [`model_training/config/config.yaml`](../model_training/config/config.yaml) with the datastore, data asset, environment, experiment and model names for your workspace. The configured split ratio and learning rate can also be adjusted there.

The helper runner currently runs only the pipeline: environment registration, datastore registration and component registration are commented out. Set up those prerequisites explicitly rather than assuming the runner creates them.

### Authenticate and submit

Sign in and select the subscription using Azure CLI. Populate an environment file selected by the runner, or export the following values in your shell:

| Variable | Meaning |
|---|---|
| `AZURE_SUBSCRIPTION_ID` | Subscription containing the Azure ML workspace |
| `AZURE_RESOURCE_GROUP` | Workspace resource group |
| `AZURE_WORKSPACE_NAME` | Azure ML workspace name |
| `AZURE_CPU_COMPUTE_NAME` | Existing Azure ML compute target |
| `AZURE_DATALAKE_ACCOUNT_NAME` | Storage account name, only when using the datastore helper |

The runner reads `model_training/environment_variables/<level>.env` for `level1`, `level2`, or `level3`. Avoid committing credentials or environment-specific secrets. From the project root:

```bash
az login
az account set --subscription "<subscription-id>"
python model_training/src/run_all_script.py --env level1
```

The runner starts the pipeline from `model_training/`, submits the job, and streams its logs. Review the job in Azure ML Studio: verify both components succeeded, inspect the printed classification report, and confirm the registered model version. The training split has no fixed random seed and the report is not an automated approval gate.

### Approve a model for serving

After independently reviewing the training results, set the registered model version's tag `status` to `approved` in Azure ML. The API filters by that tag and selects the highest numeric version; an untagged model will not load. Take care when approving multiple versions: selection uses the highest approved version, not a deployment-pinned version. The model must retain the MLflow artifact structure expected by `download_model.py`.

## 3. Run the inference service locally

The service needs Azure ML access on startup, even if a model artifact exists in the repository. Set the following in your shell:

| Variable | Meaning |
|---|---|
| `AML_SUBSCRIPTION_ID` | Subscription containing the Azure ML workspace |
| `AML_RESOURCE_GROUP` | Workspace resource group |
| `AML_WORKSPACE_NAME` | Azure ML workspace name |
| `MODEL_NAME` | Name of the registered model with an approved numeric version |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Connection string for the Application Insights resource |

Training and serving intentionally use different workspace variable names. Supply a valid Application Insights connection string for the current code: `app.py` calls Azure Monitor configuration even when the variable is missing. Do not copy real values into source files or command history. `DefaultAzureCredential` must be able to authenticate locally, for example through an Azure CLI login with the necessary workspace and artifact access.

With compatible Python and dependencies installed:

```bash
python -m pip install -r serving/requirements.txt
cd serving
uvicorn app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for the interactive API documentation, or check `http://127.0.0.1:8000/health/ready`. Use the example request in the [project README](../README.md#inference-service) to call `/predict`. A successful response contains a nested prediction, request ID and latency. If startup fails, check identity, workspace settings, model approval, artifact access and telemetry configuration in the service logs.

## 4. Prepare infrastructure and identity

1. Review [`infra/main.bicep`](../infra/main.bicep) and its parameters. It deploys ACR and AKS; [`infra/storage.bicep`](../infra/storage.bicep) is separate. Neither creates the Azure ML workspace, compute, Application Insights resource, or workload identity federation.
2. Validate and preview the infrastructure changes for your resource group and your own parameter values before deploying. The infrastructure Azure DevOps pipeline includes Bicep build, `what-if` and deployment stages. Review the supplied parameter file rather than deploying its environment-specific values unchanged.
3. Configure AKS OIDC issuer and workload identity, create or select a user-assigned managed identity, and create a federated identity credential matching the cluster issuer, namespace `credit-default`, and service account `credit-default-sa`. Grant the identity the minimum Azure ML and model-artifact access required by the service.
4. Ensure the cluster's actual image-pull identity can pull from ACR. Configure NGINX ingress if using the chart's ingress resource. The infrastructure pipeline includes an ingress-controller installation step.

Use your organization's network, TLS, ingress authentication and secret-management policies. The sample ingress does not configure TLS or API authentication. Do not expose it publicly without adding appropriate controls.

## 5. Build and deploy to AKS

Build and push the image using your own registry and tag:

```bash
az acr login --name "<acr-name>"
docker build -t "<acr-login-server>/credit-default-api:<tag>" -f serving/Dockerfile serving
docker push "<acr-login-server>/credit-default-api:<tag>"
```

Connect `kubectl` to the intended cluster:

```bash
az aks get-credentials --resource-group "<resource-group>" --name "<aks-name>"
```

Create a **private, untracked** Helm values file outside the repository, replacing all placeholders with your environment's values:

```yaml
image:
  repository: "<acr-login-server>/credit-default-api"
  tag: "<tag>"
managedIdentity:
  clientId: "<user-assigned-identity-client-id>"
aml:
  subscriptionId: "<subscription-id>"
  resourceGroup: "<workspace-resource-group>"
  workspaceName: "<workspace-name>"
  modelName: "<registered-model-name>"
applicationInsights:
  ConnectionString: "<application-insights-connection-string>"
```

The chart renders the connection string into a Kubernetes Secret. Protect the values file and Helm release data; a Kubernetes Secret is not a substitute for a complete secret-management solution. The chart defaults contain environment-specific values, so override all of them. Install the chart, pointing to your private values file:

```bash
helm upgrade --install credit-default ./helm/credit-default \
  --namespace credit-default --create-namespace \
  --values "<path-to-private-values.yaml>"
kubectl rollout status deployment/credit-default-api -n credit-default --timeout=300s
kubectl get pods,service,ingress -n credit-default
```

The default service is `ClusterIP`. For a local smoke test without exposing ingress:

```bash
kubectl port-forward -n credit-default service/credit-default-service 8000:80
```

In another terminal, open `http://127.0.0.1:8000/docs` or call `/health/ready` and `/predict`. Stop port forwarding when finished. Kubernetes probes are not configured in the Helm deployment; a successful rollout alone does not verify model readiness, so check the endpoint and logs explicitly.

## 6. Azure DevOps automation

The infrastructure and application pipeline definitions are in [`pipelines/azure-pipelines/`](../pipelines/azure-pipelines/). Configure the `infrastructure-dev` variable group and Azure service connection with the permissions required for the selected stages. The application pipeline expects `serviceConnection`, `acrName`, `resourceGroupName` and `aksClusterName`; the infrastructure pipeline also references the appropriate service connection, resource group and cluster.

**Current layout caveat:** the YAML definitions reference paths such as `serving/`, `infra/`, `helm/` and `kubernetes/` relative to the repository checkout root, while those directories now live under `azure-credit-default-mlops/`. Adjust task working directories, file paths and trigger paths for your checkout before running them. The application pipeline builds/pushes an image and deploys with Helm; it does not provision identity federation or approve the model. The training pipeline YAML is currently empty, and scheduled training in the Python pipeline is commented out.

## Troubleshooting

| Symptom | Checks |
|---|---|
| Training cannot find assets or compute | Verify CLI login, workspace variables, configured asset names, versions, compute and data permissions |
| API exits on startup | Inspect pod logs; verify telemetry configuration, Azure credentials, workspace variables, approved model tag and artifact access |
| Image pull fails | Verify image name/tag, registry connectivity and pull permission for the cluster's image-pull identity |
| `/health/ready` is unavailable or not ready | Check pod status and startup logs; ensure the model downloaded and loaded successfully |
| Ingress is unreachable | Check the ingress controller, ingress class, service endpoints, networking and any external access controls |

For diagnostic commands and telemetry investigation, see the [monitoring guide](monitoring.md). Redact tokens, connection strings and sensitive resource identifiers before sharing logs or screenshots.
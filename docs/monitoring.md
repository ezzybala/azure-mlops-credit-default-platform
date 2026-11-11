# Monitoring and observability

[Project overview](../README.md) | [Architecture](architecture.md) | [Deployment guide](deployment-guide.md)

This guide describes the signals currently emitted by the inference service and a practical workflow for investigating them. Dashboards, alerts, data drift and model quality monitoring are planned, not complete implementations.

## Current signals

| Signal | Current implementation | Where to investigate |
|---|---|---|
| HTTP requests | FastAPI OpenTelemetry instrumentation and Azure Monitor configuration | Application Insights requests, if export is configured and working |
| Health trace | A custom `health-check` span in `/health` | Application Insights traces/transaction view, if exported |
| Application events | JSON logs to stdout, including startup, model loading and prediction events | Container logs; Log Analytics only if container log collection is configured |
| Prediction latency | Application measures elapsed time and returns/logs `latency_ms` | Prediction response and application JSON logs |
| Model readiness | `/health/ready` checks whether a model is loaded | Endpoint response; Kubernetes probes are not currently wired to it |
| Training run | Azure ML job logs and MLflow sample/feature counts; classification report printed by the training component | Azure ML Studio job/experiment output |

The app's JSON logs are written to stdout; the repository does not establish that they are automatically exported to Application Insights. Azure Monitor container log collection and Log Analytics require separate configuration.

## Telemetry setup

1. Create or select an Application Insights resource and obtain its connection string through your approved secret-management process.
2. Set `APPLICATIONINSIGHTS_CONNECTION_STRING` for the service. In the Helm chart, the `applicationInsights.ConnectionString` value is rendered into a Kubernetes Secret and exposed to the container.
3. Ensure the workload can reach the telemetry endpoint and that any required Azure Monitor or container insights integrations are configured.
4. Start the service, generate requests and verify they appear in the intended resource. Allow time for ingestion and check the time range and filters.

The current application calls `configure_azure_monitor` twice, including once unconditionally. Treat a valid connection string as a startup prerequisite until this is corrected; do not assume the missing-variable branch disables telemetry cleanly. Avoid putting connection strings in committed values files, shared screenshots or terminal history.

## Check the service

The application exposes:

| Endpoint | Meaning |
|---|---|
| `GET /health` | Basic healthy response with a custom tracing span |
| `GET /health/live` | Liveness response |
| `GET /health/ready` | Returns success when the in-process model is loaded, otherwise `503` |
| `POST /predict` | Returns a prediction, request ID and application-measured latency |

The readiness response's `model_version` is currently a hard-coded API value, not the actual registered model version. Also, startup performs model download before serving requests: a startup failure may make the endpoint unreachable rather than returning `503`.

The chart has no configured Kubernetes readiness/liveness probes or resource requests and limits. Add and test them as a future operational improvement; endpoints alone do not activate Kubernetes health checks.

## Investigate a deployment

Replace the namespace or deployment name if your release differs:

```bash
kubectl get pods,service,ingress -n credit-default
kubectl rollout status deployment/credit-default-api -n credit-default
kubectl describe deployment credit-default-api -n credit-default
kubectl logs -n credit-default deployment/credit-default-api --all-containers=true --tail=100
```

If a container restarts, select its pod and inspect the previous container's logs:

```bash
kubectl logs -n credit-default <pod-name> --previous
```

Use `kubectl port-forward -n credit-default service/credit-default-service 8000:80` in a separate terminal to inspect `/health/ready` or the `/docs` UI locally. Stop the port forward after the investigation.

### Follow a prediction

For a successful `/predict` request:

1. Record the `X-Request-ID` response header or `request_id` in the response.
2. Search the container logs for the same `request_id` to locate the `prediction_request` and `prediction_completed` events. These include the measured latency; the completion event also includes the prediction.
3. Use the time window and endpoint to investigate the corresponding request in Application Insights. The application-generated request ID is not explicitly added to the OpenTelemetry request telemetry, so do not assume it equals the Application Insights operation ID.

Validation errors and prediction failures are logged with an event name and request ID, but the API does not include that ID in error response headers. Framework-level request validation may occur before the prediction handler and its application logs.

## Application Insights investigation

In the Application Insights resource, use **Logs**, **Failures**, and the transaction/request views to investigate request volume, response time and failed operations. The following example uses the Application Insights `requests` table; table names and columns may differ when querying from a Log Analytics workspace.

```kusto
requests
| where timestamp > ago(1h)
| summarize requests = count(), failures = countif(success == false),
            p95_duration_ms = percentile(duration, 95)
    by bin(timestamp, 5m), name
| order by timestamp desc
```

Use the results as an investigation starting point, not a predefined service-level objective. If no results appear, first verify resource selection, time range, telemetry configuration, network access and ingestion. Do not assume stdout logs or dependency telemetry are present without confirming the relevant instrumentation and collection configuration.

## Operational monitoring roadmap

The following are proposed, not currently defined as alert rules or dashboards in this repository:

- **Availability:** probe the service externally and alert on sustained failed requests or unavailable endpoints.
- **Latency and errors:** track request count, error rate and latency percentiles with thresholds based on a measured baseline.
- **AKS health:** monitor pod restarts, unschedulable pods, CPU/memory saturation and image-pull failures.
- **Data quality and drift:** validate input features and compare aggregate input distributions against a suitable reference, respecting privacy requirements.
- **Model performance:** collect outcomes when available, evaluate quality and fairness over time, and establish review/retraining triggers.

Avoid logging raw customer features or other sensitive information. The current service logs prediction results, so decide whether retaining them is appropriate for your use case and configure retention and access controls.

## Screenshots

Suggested additions: Application Insights request and trace views, AKS pod health, and a future workbook or dashboard. Save redacted images in `docs/screenshots/` and link them here when available.
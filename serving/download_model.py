from pathlib import Path
import os
from xml.parsers.expat import model

from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential

print("========== AZURE ENVIRONMENT ==========")

print("AZURE_CLIENT_ID:",
      os.getenv("AZURE_CLIENT_ID"))

print("AZURE_TENANT_ID:",
      os.getenv("AZURE_TENANT_ID"))

print("AZURE_FEDERATED_TOKEN_FILE:",
      os.getenv("AZURE_FEDERATED_TOKEN_FILE"))

print("=======================================")

def test_authentication():
    credential = DefaultAzureCredential()

    token = credential.get_token(
        "https://management.azure.com/.default"
    )

    print("Authentication successful")


def get_ml_client() -> MLClient:
    return MLClient(

    
        credential=DefaultAzureCredential(),
        subscription_id=os.environ["AML_SUBSCRIPTION_ID"],
        resource_group_name=os.environ["AML_RESOURCE_GROUP"],
        workspace_name=os.environ["AML_WORKSPACE_NAME"]

    )


def get_latest_approved_model(model_name: str):
    ml_client = get_ml_client()

    models = list(
        ml_client.models.list(name=model_name)
    )
    for model in models:
        print("Model Name:", model.name)
        print("Model Version:", model.version)
        print("Model Path:", model.path)


    approved_models = [
        m for m in models
        if m.tags and m.tags.get("status") == "approved"
    ]

    if not approved_models:
        raise RuntimeError(
            f"No approved versions found for model '{model_name}'"
        )

    return sorted(
        approved_models,
        key=lambda x: int(x.version),
        reverse=True
    )[0]


def download_model(
    model_name: str,
    download_dir: str = "./model"
) -> Path:

    test_authentication()

    ml_client = get_ml_client()

    model = get_latest_approved_model(model_name)

    ml_client.models.download(
        name=model.name,
        version=model.version,
        download_path=download_dir
    )

    model_path = (
        Path(download_dir)
        / model.name
        / model.name
    )

    return model_path
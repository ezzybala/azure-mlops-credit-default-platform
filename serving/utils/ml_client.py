from azure.identity import AzureCliCredential
from azure.ai.ml import MLClient
import os
import yaml

def load_config(config_path="config/config.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def get_ml_client():
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    workspace_name = os.getenv("AZURE_WORKSPACE_NAME")
    
    if not subscription_id or not resource_group or not workspace_name:
        raise ValueError("One or more environment variables are not set.")
    
    return MLClient(
        AzureCliCredential(),
        subscription_id=subscription_id,
        resource_group_name=resource_group,
        workspace_name=workspace_name
    )

from azure.ai.ml.entities import Environment
import os
from utils.ml_client import get_ml_client, load_config


def update_workspace_image_build_compute(ml_client, compute_name):
    workspace_name = os.getenv("AZURE_WORKSPACE_NAME")
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    
    # Retrieve the existing workspace object
    workspace = ml_client.workspaces.get(name=workspace_name, resource_group_name=resource_group)
    
    # Update the workspace's image build compute
    workspace.image_build_compute = compute_name
    
    # Apply the update to the existing workspace
    poller = ml_client.workspaces.begin_update(workspace)
    
    # Wait for the operation to complete
    workspace_result = poller.result()
    print(f"Workspace {workspace_name} updated to use compute {compute_name} for image building.")


def register_environment(ml_client, env_name, conda_file_path, docker_image, description):
    # Define the environment
    pipeline_job_env = Environment(
        name=env_name,
        description=description,
        conda_file=conda_file_path,
        image=docker_image
    )

    # Register the environment
    registered_env = ml_client.environments.create_or_update(pipeline_job_env)
    print(f"Environment registered: {registered_env.name}, Version: {registered_env.version}")

if __name__ == "__main__":
    ml_client = get_ml_client()

    # Update workspace to use the specified compute cluster for image building
    compute_name = os.getenv("AZURE_CPU_COMPUTE_NAME")  # Retrieve compute cluster name from environment variable
    if not compute_name:
        raise ValueError("Compute cluster environment variable is not set.")
    
    update_workspace_image_build_compute(ml_client, compute_name)

    config = load_config()["environment"]
    register_environment(
        ml_client,
        env_name=config["env_name"],
        conda_file_path=config["conda_file_path"],
        docker_image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest",
        description=config["description"]
    )




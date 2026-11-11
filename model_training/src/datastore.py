from azure.ai.ml.entities import AzureBlobDatastore, Data
from azure.ai.ml.constants import AssetTypes
import os
from utils.ml_client import get_ml_client, load_config


def create_or_get_datastore(ml_client, datastore_name, container_name):
    account_name = os.getenv("AZURE_DATALAKE_ACCOUNT_NAME")
    
    if not account_name:
        raise ValueError("Storage account name environment variable is not set.")
    
    try:
        datastore = ml_client.datastores.get(datastore_name)
        print(f"Datastore already exists: {datastore.name}")
    except Exception as e:
        print(f"Datastore not found. Creating a new one. Error: {e}")
        datastore = AzureBlobDatastore(
            name=datastore_name,
            account_name=account_name,
            container_name=container_name,
            description="Datastore points to complaints directory",
        )
        datastore = ml_client.create_or_update(datastore)
        print(f"Datastore registered: {datastore.name}")
    
    return datastore.name

def create_folder_data_asset(ml_client, datastore_name, data_asset_path, asset_name):
    main_data_asset = Data(
        name=asset_name,
        path=f"azureml://datastores/{datastore_name}/paths/{data_asset_path}",
        type=AssetTypes.URI_FOLDER,
        description="Data asset for pipeline"
    )

    registered_data_asset = ml_client.data.create_or_update(main_data_asset)
    print(f"Data asset registered: {registered_data_asset.name}")

if __name__ == "__main__":
    config = load_config()["datastore"]
    ml_client = get_ml_client()
    datastore_name = create_or_get_datastore(
        ml_client, config["datastore_name"], config["container_name"]
    )
    create_folder_data_asset(
        ml_client, datastore_name, config["data_asset_path"], config["data_asset_name"]
    )


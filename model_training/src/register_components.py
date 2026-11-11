import argparse
from pathlib import Path
from azure.ai.ml import Input, Output, command
from utils.ml_client import get_ml_client, load_config


BASE_DIR = Path(__file__).resolve().parents[1]


def get_latest_version(entities):
    entities = list(entities)
    if not entities:
        raise ValueError("No matching Azure ML environments were found.")
    if not all(str(entity.version).isdigit() for entity in entities):
        raise ValueError("Environment versions are not numeric; select an explicit version instead.")
    return max(entities, key=lambda entity: int(entity.version))

def create_shared_components(environment_reference, component_version, source_root):
    definitions = (
        (
            "data_preprocessing",
            "Data Preprocessing Component",
            "Load raw tables and write merged transactions for preprocessing.",
        ),
        # (
        #     "model_training",
        #     "Model Training Component",
        #     "Read preprocessed data and train the model.",
        # ),
    )
    components = []
    for name, display_name, description in definitions:
        source_directory = Path(source_root) / name
        script_name = f"{name}.py"
        if not (source_directory / script_name).is_file():
            raise FileNotFoundError(f"Component script not found: {source_directory / script_name}")

        step = command(
            name=name,
            display_name=display_name,
            description=description,
            inputs={
                "data": Input(type="uri_folder"),
                # "mode": Input(
                #     type="string",
                #     default="forecasting",
                #     enum=["forecasting", "historical"],
                # ),
            },
            outputs={"output_path": Output(type="uri_folder")},
            code=str(source_directory),
            command=(
                f"python {script_name} "
                "--input ${{inputs.data}} "
                "--output ${{outputs.output_path}} "
                #"--mode ${{inputs.mode}}"
            ),
            environment=environment_reference,
        )
        component = step.component
        component.version = component_version
        components.append(component)
    return components


def register_shared_components(ml_client, components):
    registered_components = {}
    for component in components:
        registered = ml_client.components.create_or_update(component)
        registered_components[registered.name] = registered
        print(f"Registered: {registered.name}:{registered.version}")
    return registered_components


def main(component_version="1"):
    ml_client = get_ml_client()

    config = load_config(str(BASE_DIR.parent / "config" / "config.yaml"))["environment"]
    env_name = config["env_name"]
    environments = ml_client.environments.list(name=env_name)
    latest_env = get_latest_version(environments)
    environment_reference = f"azureml:{latest_env.name}:{latest_env.version}"

    components = create_shared_components(
        environment_reference,
        component_version,
        BASE_DIR / "components",
    )
    return register_shared_components(ml_client, components)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Register shared Azure ML components.")
    parser.add_argument("--version", default="1", help="Component version to register.")
    args = parser.parse_args()
    main(component_version=args.version)
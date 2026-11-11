import os
from pathlib import Path
from azure.ai.ml import Input, Output, command, dsl
from azure.ai.ml.entities import PipelineJobSettings, CronTrigger, JobSchedule
from utils.ml_client import get_ml_client, load_config


def get_latest_version(entities):
    entities = list(entities)
    if not entities:
        raise ValueError("No matching Azure ML assets were found.")
    return max(entities, key=lambda entity: entity.version)


def main():
    compute_target = os.getenv("AZURE_CPU_COMPUTE_NAME")
    if not compute_target:
        raise ValueError(f"AZURE_CPU_COMPUTE_NAME environment variable not set")

    # Initialize ML client
    ml_client = get_ml_client()

    full_config = load_config()
    datastore_config = full_config["datastore"]
    environment_config = full_config["environment"]
    pipeline_config = full_config["pipeline"]

    environment = get_latest_version(ml_client.environments.list(name=environment_config["env_name"]))
    data_asset = get_latest_version(ml_client.data.list(name=datastore_config["data_asset_name"]))
    print(data_asset.path)
    storage_path = f"azureml://datastores/{datastore_config['datastore_name']}/paths/{pipeline_config['project_folder']}/"

    ########Step1#############
    cwd = os.getcwd()
    src_dir = os.path.join(cwd, "components", "data_prep")
    src_dir = os.path.abspath(src_dir)

    data_preprocessing_step = command(
        name="data_preprocessing",
        display_name="Data Preprocessing Component",
        description="read raw file as input and run the data preprocessing script",
        inputs={
            "data": Input(type="uri_folder"),
            "test_train_ratio": Input(type="number"),
        },
        outputs=dict(
            train_data=Output(type="uri_folder", mode="rw_mount"),
            test_data=Output(type="uri_folder", mode="rw_mount"),
        ),
        # The source folder of the component
        code=src_dir,
        command=(
            "python data_prep.py "
            "--data ${{inputs.data}} "
            "--test_train_ratio ${{inputs.test_train_ratio}} "
            "--train_data ${{outputs.train_data}} "
            "--test_data ${{outputs.test_data}} "
        ),
        environment=f"{environment.name}:{environment.version}",
    )
    ########Step1 Ends#############

    ########Step2 Starts#############
    cwd = os.getcwd()
    src_dir = os.path.join(cwd, "components", "train")
    src_dir = os.path.abspath(src_dir)

    model_training_step = command(
        name="model_training",
        display_name="Model Training Component",
        description="read preprocessed data as input and run the model training script",
        inputs={
            "train_data": Input(type="uri_folder"),
            "test_data": Input(type="uri_folder"),
            "learning_rate": Input(type="number"),
            "registered_model_name": Input(type="string"),

        },
        outputs=dict(
            model=Output(type="uri_folder", mode="rw_mount"),
        ),
        # The source folder of the component
        code=src_dir,
        command=(
            "python train.py "
            "--train_data ${{inputs.train_data}} "
            "--test_data ${{inputs.test_data}} "
            "--model ${{outputs.model}} "
            "--learning_rate ${{inputs.learning_rate}} "
            "--registered_model_name ${{inputs.registered_model_name}} "
        ),
        environment=f"{environment.name}:{environment.version}",
    )
    ########Step2 Ends#############

    #Pipeline
    @dsl.pipeline(
        compute= compute_target,
        description=pipeline_config["description"],
    )
    def credit_main_pipeline(
        data_input,
        test_train_ratio,

        
    ):
        
        step1 = data_preprocessing_step(
            data=data_input,
            test_train_ratio=test_train_ratio,
        )
        step2 = model_training_step(
            train_data=step1.outputs.train_data,
            test_data=step1.outputs.test_data,
            learning_rate=pipeline_config["learning_rate"],
            registered_model_name=pipeline_config["registered_model_name"]
        )

        return 

    pipeline = credit_main_pipeline(
    data_input=Input(type="uri_folder", path=data_asset.path),
    test_train_ratio=pipeline_config["test_train_ratio"],
    )
    pipeline.settings = PipelineJobSettings(force_rerun=False)

    pipeline_job = ml_client.jobs.create_or_update(
        pipeline,
        experiment_name=pipeline_config["experiment_name"],
    )
    
    # # Step 4: Create the monthly schedule (use original unsubmitted pipeline_job)
    # cron_trigger = CronTrigger(
    #     expression=pipeline_config["cron_expression"],
    #     time_zone="UTC"
    # )

    # job_schedule = JobSchedule(
    #     name=pipeline_config["schedule_name"],
    #     trigger=cron_trigger,
    #     create_job=pipeline  # Safe to reuse, since it's not altered by submission
    # )

    # # Register the schedule
    # created_schedule = ml_client.schedules.begin_create_or_update(job_schedule).result()
    # print(f"Schedule created: {created_schedule.name}")

    ml_client.jobs.stream(pipeline_job.name)


if __name__ == "__main__":
    main()
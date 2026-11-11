from download_model import download_model
# from score import load_model

global model

model_path = download_model(
    "credit_defaults_model"
)

# model = load_model(model_path)
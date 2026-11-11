from contextlib import asynccontextmanager
import time
import uuid
import os

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from fastapi import FastAPI, HTTPException, Response
from schema import PredictionRequest
from score import is_model_ready
from score import load_model, predict
from logger import get_logger
from download_model import download_model

connection_string = os.getenv(
    "APPLICATIONINSIGHTS_CONNECTION_STRING"
)

if connection_string:
    configure_azure_monitor(
        connection_string=connection_string
    )
    print("Application Insights configured")
else:
    print("Application Insights not configured")

configure_azure_monitor(
    connection_string=os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
)

tracer = trace.get_tracer(__name__)


model_name = os.environ["MODEL_NAME"]

logger = get_logger()
@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info(
        "API startup",
        extra={
            "event": "application_startup"
        }
    )

    model_path = download_model(
        model_name
    )

    load_model(model_path)

    yield

    logger.info(
        "API shutdown",
        extra={
            "event": "application_shutdown"
        }
    )


app = FastAPI(
    title="Credit Default Prediction API",
    version="1.0.0",
    lifespan=lifespan
)

FastAPIInstrumentor.instrument_app(app)



@app.get("/")
def root():
    logger.info("Root endpoint called")
    return {
        "message": "Credit Default Prediction API"
    }

@app.get("/health")
def health():

    with tracer.start_as_current_span(
        "health-check"
    ):
        return {"status": "healthy"}

@app.get("/health/live")
def liveness():
    return {
        "status": "live",
        "service": "credit-default-api"
    }

@app.get("/health/ready")
def readiness():

    if not is_model_ready():
        raise HTTPException(
            status_code=503,
            detail="Model not loaded"
        )

    return {
        "status": "ready",
        "service": "credit-default-api",
        "model_loaded": True,
        "model_version": "1.0.0"
    }

# @app.post("/predict")
# def score_request(request: PredictionRequest):
#     try:
#         logger.info(f"Prediction request received: {request}")
#         payload = request.model_dump()
#         return predict(payload)

#     except ValueError as e:
#         logger.error(f"ValueError occurred: {e}")
#         raise HTTPException(
#             status_code=400,
#             detail=str(e)
#         )

#     except Exception as e:
#         logger.error(f"Unexpected error occurred: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=str(e)
#         )

@app.post("/predict")
def score_request(
    request: PredictionRequest,
    response: Response
):

    request_id = str(uuid.uuid4())

    start_time = time.perf_counter()

    try:

        logger.info(
            "Prediction request received",
            extra={
                "event": "prediction_request",
                "request_id": request_id
            }
        )

        payload = request.model_dump()

        prediction = predict(payload)

        latency_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2
        )

        logger.info(
            "Prediction completed",
            extra={
                "event": "prediction_completed",
                "request_id": request_id,
                "prediction": prediction,
                "latency_ms": latency_ms
            }
        )

        response.headers["X-Request-ID"] = request_id

        return {
            "request_id": request_id,
            "prediction": prediction,
            "latency_ms": latency_ms
        }

    except ValueError as e:

        latency_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2
        )

        logger.error(
            "Validation error",
            extra={
                "event": "validation_error",
                "request_id": request_id,
                "latency_ms": latency_ms,
                "error": str(e)
            }
        )

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        latency_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2
        )

        logger.exception(
            "Prediction failed",
            extra={
                "event": "prediction_failed",
                "request_id": request_id,
                "latency_ms": latency_ms,
                "error": str(e)
            }
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )




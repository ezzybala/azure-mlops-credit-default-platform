import json
import logging
import sys
from datetime import datetime


class JsonFormatter(logging.Formatter):

    def format(self, record):

        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage()
        }

        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id

        if hasattr(record, "event"):
            log_record["event"] = record.event

        if hasattr(record, "latency_ms"):
            log_record["latency_ms"] = record.latency_ms

        if hasattr(record, "prediction"):
            log_record["prediction"] = record.prediction

        if hasattr(record, "error"):
            log_record["error"] = record.error

        return json.dumps(log_record)


def get_logger():

    logger = logging.getLogger("credit-api")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    logger.addHandler(handler)

    return logger
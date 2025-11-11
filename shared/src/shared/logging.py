import json
import os
import sys
import traceback
from logging import DEBUG, INFO, Formatter, LogRecord, StreamHandler, getLogger

from dotenv import load_dotenv

try:
    from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
except ImportError:  # pragma: no cover - optional dependency
    AzureMonitorLogExporter = None  # type: ignore[assignment]
    LoggerProvider = None  # type: ignore[assignment]
    LoggingHandler = None  # type: ignore[assignment]
    BatchLogRecordProcessor = None  # type: ignore[assignment]
    set_logger_provider = None  # type: ignore[assignment]

load_dotenv()


class JSONFormatter(Formatter):
    def format(self, record: LogRecord) -> str:
        try:
            log_message: str | dict = record.msg
            log_exception = record.exc_info

            if log_exception:
                log_exception = self.formatException(log_exception).splitlines()

            if isinstance(log_message, dict):
                if log_exception:
                    log_message["exception"] = log_exception
                return json.dumps(
                    log_message,
                    ensure_ascii=False,
                    default=lambda obj: str(type(obj).__name__)
                )
            elif isinstance(log_message, str):
                if log_exception:
                    log_exception_string = "\n".join(log_exception)
                    log_message = f"{log_message}\n{log_exception_string}"
                return log_message
            else:
                return record.msg
        except Exception as e:
            print(f"{e}\n{traceback.format_exc()}")
            return record.msg


def get_logger(name: str = "APP", level: int = DEBUG):
    logger = getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        stream_handler = StreamHandler(stream=sys.stdout)
        stream_handler.setFormatter(JSONFormatter())
        stream_handler.setLevel(level)
        logger.addHandler(stream_handler)

        # Azure Monitor LoggingHandler
        if (
            os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
            and AzureMonitorLogExporter
            and LoggerProvider
            and LoggingHandler
            and BatchLogRecordProcessor
            and set_logger_provider
        ):
            logger_provider = LoggerProvider()
            set_logger_provider(logger_provider)
            exporter = AzureMonitorLogExporter(
                connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"]
            )
            logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
            azure_handler = LoggingHandler(level=level, logger_provider=logger_provider)
            azure_handler.setFormatter(JSONFormatter())
            logger.addHandler(azure_handler)

    root_logger = getLogger()
    root_logger.handlers.clear()

    for noisy_logger in ["werkzeug", "httpx"]:
        getLogger(noisy_logger).disabled = True

    return logger


logger = get_logger("APP")

if __name__ == "__main__":
    logger.debug({"message": "This is a debug log."})
    logger.info({"message": "This is an info log."})
    logger.error({"message": "This is an error log.", "error_code": 500})

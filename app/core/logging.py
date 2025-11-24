import logging
import sys
from typing import Any
from datetime import datetime


class JSONFormatter(logging.Formatter):
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        import json
        
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields (request context, etc.)
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "details"):
            log_data["details"] = record.details
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logging(level: str = "INFO", json_logs: bool = False) -> None:
   
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter
    if json_logs:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
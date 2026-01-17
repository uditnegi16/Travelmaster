import os
import logging
import traceback
import pandas as pd
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)

EXCEPTIONS_DIR = "exceptions"
os.makedirs(EXCEPTIONS_DIR, exist_ok=True)

def dump_exception(
    exc: Exception,
    context: Dict[str, Any] = None,
    data_sample: pd.DataFrame = None,
    filename_prefix: str = "error",
):
    """Dump full exception + context to timestamped CSV in exceptions/."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

    error_data = {
        "timestamp": [timestamp],
        "error_type": [type(exc).__name__],
        "error_msg": [str(exc)],
        "traceback": [traceback.format_exc()],
    }
    if context:
        for k, v in context.items():
            error_data[k] = [str(v)]

    error_df = pd.DataFrame(error_data)

    csv_path = os.path.join(EXCEPTIONS_DIR, f"{filename_prefix}_{timestamp}.csv")
    error_df.to_csv(csv_path, index=False)

    logger.error(f"Dumped exception to {csv_path}")
    return csv_path

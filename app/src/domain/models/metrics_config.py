from typing import Callable

from pydantic import BaseModel

from app.src.domain.constants import ModelMetrics


class MetricsConfig(BaseModel):
    metric_getter: Callable
    metric_name: ModelMetrics
    reverse: bool
from typing import List

from pydantic import BaseModel

from .pydantic_ontology import MetricIn


class MetricsBatch(BaseModel):
    items: List[MetricIn]

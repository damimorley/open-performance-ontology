from pydantic import BaseModel
from typing import List
from .pydantic_ontology import MetricIn


class MetricsBatch(BaseModel):
    items: List[MetricIn]

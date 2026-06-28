"""Serialize System Review Graph objects."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from system_review_graph.models import SystemReviewGraph


def to_dict(graph: SystemReviewGraph) -> dict[str, Any]:
    """Convert a graph object into a JSON-ready dictionary."""

    return asdict(graph)

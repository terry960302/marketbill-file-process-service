import json
from dataclasses import dataclass, field, asdict


@dataclass
class GatewayResponse:
    statusCode: int
    message: str = field(default_factory=str)
    body: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.body is None:
            self.body = {}

    def to_dict(self):
        return asdict(self)

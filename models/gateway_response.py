import json
from dataclasses import dataclass, field, asdict


@dataclass
class GatewayResponse:
    statusCode: int
    body: str = field(default_factory=str)

    def to_dict(self):
        return asdict(self)


@dataclass
class ErrorBody:
    message: str = field(default_factory=str)

    def to_str(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ReceiptOutput:
    file_name: str = field(default_factory=str)
    file_path: str = field(default_factory=str)
    file_format: str = field(default_factory=str)
    metadata: str = field(default_factory=str)

    def to_str(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    def to_dict(self) -> dict:
        return asdict(self)

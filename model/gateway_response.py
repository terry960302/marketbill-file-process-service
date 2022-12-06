from dataclasses import dataclass


@dataclass
class GatewayResponse:
    statusCode: int
    message: str
    body: dict = {}

    def __post_init__(self):
        if self.body is None:
            self.body = {}

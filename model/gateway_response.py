from dataclasses import dataclass, field


@dataclass
class GatewayResponse:
    statusCode: int
    message: str
    body: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.body is None:
            self.body = {}

from dataclasses import dataclass, field, asdict


@dataclass
class ReceiptProcessOutput:
    file_name: str
    file_format: str
    file_path: str
    metadata: str = field(default_factory=str)

    def to_dict(self):
        return asdict(self)

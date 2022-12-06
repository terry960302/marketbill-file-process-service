from dataclasses import dataclass
from typing import List, Optional


@dataclass
class User:
    name: str


@dataclass
class FlowerType:
    name: str


@dataclass
class Flower:
    name: str
    flowerType: FlowerType

    def __post_init__(self):
        self.flowerType = FlowerType(**self.flowerType)


@dataclass
class OrderItem:
    flower: Flower
    price: Optional[int]
    quantity: int
    grade: str

    def __post_init__(self):
        self.flower = Flower(**self.flower)


@dataclass
class ReceiptProcessInput:
    orderNo: str
    retailer: User
    wholesaler: User
    orderItems: List[OrderItem]

    def __post_init__(self):
        self.retailer = User(**self.retailer)
        self.wholesaler = User(**self.wholesaler)
        self.orderItems = list(map(lambda item: OrderItem(**item), self.orderItems))

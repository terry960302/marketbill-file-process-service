from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Retailer:
    name: str

@dataclass
class Wholesaler:
    businessNo: str
    companyName: str
    employerName: str
    sealStampImgUrl: str
    address: str
    companyPhoneNo: str
    businessMainCategory: str
    businessSubCategory: str
    bankAccount: str


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
    retailer: Retailer
    wholesaler: Wholesaler
    orderItems: List[OrderItem]

    def __post_init__(self):
        self.retailer = User(**self.retailer)
        self.wholesaler = User(**self.wholesaler)
        self.orderItems = list(map(lambda item: OrderItem(**item), self.orderItems))

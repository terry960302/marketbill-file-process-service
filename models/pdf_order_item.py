from dataclasses import dataclass


@dataclass
class PdfOrderItem:
    name: str
    quantity: str
    unit_price: str
    tot_price: str

    def __init__(self, name: str, quantity: int, unit_price: int):
        self.name = name
        self.quantity = self.format_currency(quantity)
        self.unit_price = self.format_currency(unit_price)
        self.tot_price = self.format_currency(quantity * unit_price)

    @staticmethod
    def format_currency(num):
        if num is None:
            return "-"
        return '{:,.0f}'.format(num)

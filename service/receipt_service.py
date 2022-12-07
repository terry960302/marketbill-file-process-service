#!/usr/bin/env python
# coding: utf-8
from datetime import datetime
from pytz import timezone
import boto3
from config import ACCESS_KEY_ID, ACCESS_SECRET_KEY, BUCKET_NAME
import os
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from gspread.cell import Cell
import pandas as pd
import json
import requests
from math import ceil
from model import receipt_process_input as dto
from typing import List
from dataclasses import asdict
from gspread import Client, Spreadsheet, Worksheet
import time


class ReceiptService:
    SCOPE = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    JSON_KEY_PATH = "../credential/eloquent-branch-369106-1e961c642259.json"
    GOOGLE_SPREAD_SHEET_ACCOUNT = 'floway.wholesale@gmail.com'
    STORAGE_PATH = '../tmp_storage/'
    EXPORT_FILE_FORMAT = ".pdf"
    REMOTE_STORAGE = "s3"

    def __init__(self):
        self.__google_client: Client = None
        return

    def process_receipt_data(self, data: dto.ReceiptProcessInput, file_name: str):
        # 인증 설정하기
        credential = ServiceAccountCredentials.from_json_keyfile_name(ReceiptService.JSON_KEY_PATH,
                                                                      ReceiptService.SCOPE)
        gc: Client = gspread.authorize(credential)
        self.__google_client = gc

        order_items: List[dto.OrderItem] = self.filter_not_null(data.orderItems)

        new_title: str = f"receipt_{data.wholesaler.name}_" + str(data.orderNo)

        doc: Spreadsheet = self.create_formatted_spreadsheet(file_name, new_title)

        print('기본 세팅 완료')

        self.update_all_contents_to_sheet(doc, data.orderNo, data.retailer.name, order_items)

        print('스프레드시트 내 데이터 입력 완료')

        self.export_pdf(new_title, credential, doc)

        self.upload_receipt_to_s3(new_title)
        return

    @staticmethod
    def get_today():
        today = datetime.now(timezone('Asia/Seoul'))
        today = datetime.strftime(today, '%Y-%m-%d')
        return today

    """
   양식을 복사해서, 새로운 스프레드시트를 만드는 함수
    """

    def create_formatted_spreadsheet(self, file_name: str, new_title: str) -> Spreadsheet:
        doc: Spreadsheet = self.__google_client.open(file_name)

        # 권한을 새로줘야해요 ~~ floway.wholesale 계정 내에. 
        # service 계정에 생성된 파일이고, 이를 공유해야 하는 개념

        new_spreadsheet = self.__google_client.copy(doc.id, title=new_title)
        new_spreadsheet.share(ReceiptService.GOOGLE_SPREAD_SHEET_ACCOUNT, perm_type='user', role='writer')

        doc = self.__google_client.open(new_title)
        return doc

    def create_sheet_cells(self, d: dto.OrderItem, num: int, cells):
        flower_name = d.flower.name
        flower_type = d.flower.flowerType.name

        grade = d.grade
        qty = d.quantity
        prc = int(d.price)
        tot_prc = int(prc * qty)

        item = "(" + flower_type + ")" + flower_name + "-" + grade

        # define input cell
        cell_item = Cell(num, 1, item)
        cell_qty = Cell(num, 5, qty)
        cell_prc = Cell(num, 7, prc)
        cell_tot_prc = Cell(num, 11, tot_prc)

        cell = [cell_item, cell_qty, cell_prc, cell_tot_prc]

        cells = cells + cell

        return cells

    """
    sheet를 input으로 받아서 복제 후 데이터를 넣을 부분만 내용 날림
    """

    def generate_new_sheet(self, idx: int, sheet, name: str):
        new_sheet = sheet.duplicate(insert_sheet_index=idx, new_sheet_name=name)
        new_sheet = new_sheet.batch_clear(['A11:K23'])
        return new_sheet

    def update_basic_info_to_sheet(self, sheet: Worksheet, order_no: str, retailer: str,
                                   order_list: List[dto.OrderItem]):
        # 기본 정보 및 판매 합계 입력
        order_id = Cell(2, 2, order_no)
        retail_name = Cell(2, 7, retailer)
        issue_date = Cell(8, 1, ReceiptService.get_today())

        # 합계 입력
        # dict_list = list(map(lambda item: asdict(item), order_list))
        # df = pd.DataFrame(dict_list)

        # df['tot_price'] = df['quantity'] * df['price']
        # tot_price = int(df['tot_price'].sum())

        calc_prices = list(map(lambda item: item.price * item.quantity, order_list))
        tot_price = sum(calc_prices)

        top_tot_price = Cell(8, 4, tot_price)
        bottom_tot_price = Cell(24, 11, tot_price)

        sheet.update_cells([order_id, retail_name, issue_date, top_tot_price, bottom_tot_price])
        return

    def filter_not_null(self, order_list: List[dto.OrderItem]) -> List[dto.OrderItem]:
        def is_not_null(item: dto.OrderItem):
            return item.price is not None

        return list(filter(is_not_null, order_list))

    def export_pdf(self, new_title, credential, doc):

        url = 'https://docs.google.com/spreadsheets/export?format=pdf&size=statement&gridlines=false&scale=3&horizontal_alignment=CENTER&vertical_alignment=CENTER&id=' + doc.id
        headers = {'Authorization': 'Bearer ' + credential.create_delegated("").get_access_token().access_token}
        res = requests.get(url, headers=headers)

        with open(ReceiptService.STORAGE_PATH + new_title + ReceiptService.EXPORT_FILE_FORMAT, 'wb') as f:
            f.write(res.content)

        return print('finish exporting pdf')

    def upload_receipt_to_s3(self, new_title):  # f = 파일명

        local_file_name = f'{ReceiptService.STORAGE_PATH}{new_title}{ReceiptService.EXPORT_FILE_FORMAT}'
        object_name = f'file-process-service-storage/{new_title}.pdf'

        s3_client = boto3.client(
            ReceiptService.REMOTE_STORAGE,
            aws_access_key_id=ACCESS_KEY_ID,
            aws_secret_access_key=ACCESS_SECRET_KEY
        )

        response = s3_client.upload_file(
            local_file_name,
            BUCKET_NAME,
            object_name)

        if os.path.isfile(local_file_name):
            os.remove(local_file_name)

        print('finish upload pdf to s3')

    def update_all_contents_to_sheet(self, doc: Spreadsheet, order_no: str, retailer: str,
                                     order_items: List[dto.OrderItem]):
        max_row = 13
        receipt_num = ceil(len(order_items) / max_row)  # max_row 개수보다 많으면 영수증을 분리함.

        default_sheet_name = "Sheet1"
        sheet: Worksheet = doc.worksheet(default_sheet_name)

        for n in range(receipt_num):
            # 첫 영수증에는 기본 정보 입력(+ 주문항목 입력)
            if n == 0:

                # 기본 정보 입력
                self.update_basic_info_to_sheet(sheet, order_no, retailer, order_items)

                cells = []

                end = (n + 1) * max_row

                for i, d in enumerate(order_items[:end]):
                    num = i + 11
                    cells = self.create_sheet_cells(d, num, cells)  # 주문 항목 입력

                sheet.update_cells(cells)

            # 그 다음 장(paper)부터는 기본 정보가 안 들어감
            elif n > 0:

                name = f'Sheet{str(n + 1)}'
                self.generate_new_sheet(n, sheet, name)  # 장(paper)이 다르므로 다른 sheet 으로 분리

                new_sheet: Worksheet = doc.worksheet(name)

                cells = []

                start = n * max_row
                end = (n + 1) * max_row

                for i, d in enumerate(order_items[start:end]):
                    num = i + 11
                    cells = self.create_sheet_cells(d, num, cells)

                new_sheet.update_cells(cells)


# # test
# if __name__ == "__main__":
#     print("init")
#     start_time = time.time()
#     json_object = {
#         "orderNo": "20221205M1230918",
#         "retailer": {
#             "name": "꽃소매"
#         },
#         "wholesaler": {
#             "name": "꽃도매"
#         },
#         "orderItems": [
#             {
#                 "flower": {
#                     "name": "테데오옐로우",
#                     "flowerType": {
#                         "name": "국화"
#                     }
#                 },
#                 "quantity": 17,
#                 "grade": "상",
#                 "price": 10000
#             },
#             {
#                 "flower": {
#                     "name": "테데오옐로우2",
#                     "flowerType": {
#                         "name": "국화"
#                     }
#                 },
#                 "quantity": 123,
#                 "grade": "상",
#                 "price": 39450
#             },
#             {
#                 "flower": {
#                     "name": "신명",
#                     "flowerType": {
#                         "name": "국화"
#                     }
#                 },
#                 "quantity": 23,
#                 "grade": "상",
#                 "price": None
#             },
#             {
#                 "flower": {
#                     "name": "상그릴라",
#                     "flowerType": {
#                         "name": "국화"
#                     }
#                 },
#                 "quantity": 84,
#                 "grade": "상",
#                 "price": None
#             }
#         ]
#     }
#
#     receipt_form_name = 'receipt_001'
#
#     json_input = dto.ReceiptProcessInput(**json_object)
#     receipt_service = ReceiptService()
#     receipt_service.process_receipt_data(json_input, receipt_form_name)
#     print("--- %s seconds ---" % (time.time() - start_time))

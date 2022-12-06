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


def get_today():
    today = datetime.now(timezone('Asia/Seoul'))
    today = datetime.strftime(today, '%Y-%m-%d')
    return today


"""
   요게 json 객체를 받아서, parsing해서 데이터 내려주는 친구
"""
def parse_json_input(data):
    order_no = data['orderNo']
    retailer = data['retailer']['name']
    wholesaler = data['wholesaler']['name']
    order_items = data['orderItems']
    return order_no, retailer, wholesaler, order_items


"""
   양식을 복사해서, 새로운 스프레드시트를 만드는 함수
"""
def create_formatted_spreadsheet(file_name, new_title):
    doc = gc.open(file_name)

    # 권한을 새로줘야해요 ~~ floway.wholesale 계정 내에. 
    # service 계정에 생성된 파일이고, 이를 공유해야 하는 개념

    google_spread_sheet_account = 'floway.wholesale@gmail.com'

    new_spreadsheet = gc.copy(doc.id, title=new_title)
    new_spreadsheet.share(google_spread_sheet_account, perm_type='user', role='writer')

    doc = gc.open(new_title)

    return doc


def create_sheet_cells(d, num, cells):
    flower_name = d['flower']['name']
    flower_type = d['flower']['flowerType']['name']

    grade = d['grade']
    qty = d['quantity']
    prc = int(d['price'])
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


def generate_new_sheet(idx, sheet, name):
    new_sheet = sheet.duplicate(insert_sheet_index=idx, new_sheet_name=name)
    new_sheet = new_sheet.batch_clear(['A11:K23'])
    return new_sheet


def update_basic_info_to_sheet(sheet, order_no, retailer, order_list):
    # 기본 정보 및 판매 합계 입력
    order_id = Cell(2, 2, order_no)
    retail_name = Cell(2, 7, retailer)
    issue_date = Cell(8, 1, get_today())

    # 합계 입력
    df = pd.DataFrame(order_list)
    df['tot_price'] = df['quantity'] * df['price']

    tot_price = int(df['tot_price'].sum())

    top_tot_price = Cell(8, 4, tot_price)
    bottom_tot_price = Cell(24, 11, tot_price)

    sheet.update_cells([order_id, retail_name, issue_date, top_tot_price, bottom_tot_price])
    return


def eliminate_null_data(order_list):
    df = pd.DataFrame(order_list)
    df = df[~df['price'].isnull()]
    order_list = json.loads(df.to_json(orient='records',
                                       force_ascii=False))

    return order_list


def export_pdf(new_title, credential, doc):
    # I added below script
    url = 'https://docs.google.com/spreadsheets/export?format=pdf&size=statement&gridlines=false&scale=3&horizontal_alignment=CENTER&vertical_alignment=CENTER&id=' + doc.id
    headers = {'Authorization': 'Bearer ' + credential.create_delegated("").get_access_token().access_token}
    res = requests.get(url, headers=headers)

    with open('./tmp_storage/' + new_title + ".pdf", 'wb') as f:
        f.write(res.content)

    return print('finish exporting pdf')


def upload_receipt_to_s3(new_title):  # f = 파일명
    remote_storage = "s3"
    file_name = f'tmp_storage/{new_title}.pdf'
    object_name = f'file-process-service-storage/{new_title}.pdf'

    s3_client = boto3.client(
        remote_storage,
        aws_access_key_id=ACCESS_KEY_ID,
        aws_secret_access_key=ACCESS_SECRET_KEY
    )

    response = s3_client.upload_file(
        file_name,
        BUCKET_NAME,
        object_name)

    if os.path.isfile(file_name):
        os.remove(file_name)

    return print('finish upload pdf to s3')


def update_all_contents_to_sheet(doc, order_no, retailer, order_items):
    max_row = 13
    receipt_num = ceil(len(order_items) / max_row) # max_row 개수보다 많으면 영수증을 분리함.

    default_sheet_name = "Sheet1"
    sheet = doc.worksheet(default_sheet_name)

    for n in range(receipt_num):
        # 첫 영수증에는 기본 정보 입력(+ 주문항목 입력)
        if n == 0:

            # 기본 정보 입력
            update_basic_info_to_sheet(sheet, order_no, retailer, order_items)

            cells = []

            end = (n + 1) * max_row

            for i, d in enumerate(order_items[:end]):
                num = i + 11
                cells = create_sheet_cells(d, num, cells)  # 주문 항목 입력

            sheet.update_cells(cells)

        # 그 다음 장(paper)부터는 기본 정보가 안 들어감
        elif n > 0:

            name = f'Sheet{str(n + 1)}'
            generate_new_sheet(n, sheet, name)  # 장(paper)이 다르므로 다른 sheet 으로 분리

            new_sheet = doc.worksheet(name)

            cells = []

            start = n * max_row
            end = (n + 1) * max_row

            for i, d in enumerate(order_items[start:end]):
                num = i + 11
                cells = create_sheet_cells(d, num, cells)

            new_sheet.update_cells(cells)


def process_receipt_data(data, file_name):
    # 인증 설정하기
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    json_key_path = "../credential/eloquent-branch-369106-1e961c642259.json"  # JSON Key File Path

    credential = ServiceAccountCredentials.from_json_keyfile_name(json_key_path, scope)

    global gc

    gc = gspread.authorize(credential)

    order_no, retailer, wholesaler, order_items = parse_json_input(data)

    order_items = eliminate_null_data(order_items)

    new_title = f"receipt_{wholesaler}_" + str(order_no)

    doc = create_formatted_spreadsheet(file_name, new_title)

    print('기본 세팅 완료')

    update_all_contents_to_sheet(doc, order_no, retailer, order_items)

    print('스프레드시트 내 데이터 입력 완료')

    export_pdf(new_title, credential, doc)

    upload_receipt_to_s3(new_title)


# test
if __name__ == "__main__":
    json_object = {
        "orderNo": "c3a5444d-b02d-42bf-ba2c-5d1d027dbe63",
        "retailer": {
            "name": "CCJBDFFVVW"
        },
        "wholesaler": {
            "name": "KQXYQVLXJA"
        },
        "orderItems": [
            {
                "flower": {
                    "name": "테데오옐로우",
                    "flowerType": {
                        "name": "국화"
                    }
                },
                "quantity": 17,
                "grade": "상",
                "price": 10000
            },
            {
                "flower": {
                    "name": "신명",
                    "flowerType": {
                        "name": "국화"
                    }
                },
                "quantity": 23,
                "grade": "상",
                "price": None
            },
            {
                "flower": {
                    "name": "상그릴라",
                    "flowerType": {
                        "name": "국화"
                    }
                },
                "quantity": 84,
                "grade": "상",
                "price": None
            }
        ]
    }

    receipt_form_name = 'receipt_001'

    process_receipt_data(json_object, receipt_form_name)

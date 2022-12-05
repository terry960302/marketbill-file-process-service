#!/usr/bin/env python
# coding: utf-8


def getToday():
    
    from datetime import datetime
    from pytz import timezone

    today = datetime.now(timezone('Asia/Seoul'))
    today = datetime.strftime(today, '%Y-%m-%d')
    
    return today


def data_parsing(json_object):
    """
    
    요게 json 객체를 받아서, parsing해서 데이터 내려주는 친구
    
    """
    
    data = json_object
    
    order_no = data['orderNo']
    retailer = data['retailer']['name']
    wholesaler = data['wholesaler']['name']
    
    order_items = data['orderItems']
    
    return order_no, retailer, wholesaler, order_items



def new_receipt_file(file_name, new_title):
    
    """
    양식을 복사해서, 새로운 스프레드시트를 만드는 함수
    
    """
    
    doc = gc.open(file_name)
    
    # 권한을 새로줘야해요 ~~ floway.wholesale 계정 내에. 
    # service 계정에 생성된 파일이고, 이를 공유해야 하는 개념

    new_spreadsheet = gc.copy(doc.id, title=new_title)
    new_spreadsheet.share('floway.wholesale@gmail.com', perm_type='user', role='writer')
    
    doc = gc.open(new_title)

    return doc


def generate_input_data(d, num, cells):
    
    from gspread.cell import Cell
    
    flower_name = d['flower']['name']
    flower_type = d['flower']['flowerType']['name']
    
    grade = d['grade']
    qty = d['quantity']
    prc = int(d['price'])
    tot_prc = int(prc*qty)
    
    item = "("+flower_type+")" + flower_name + "-" + grade

    # define input cell
    cell_item = Cell(num, 1, item)
    cell_qty = Cell(num, 5,  qty)
    cell_prc = Cell(num, 7, prc)
    cell_tot_prc = Cell(num, 11, tot_prc)
    
    cell = [cell_item, cell_qty, cell_prc, cell_tot_prc]
    
    cells = cells+cell
    
    return cells


# In[30]:


def generate_new_sheet(idx, sheet, name):
    
    new_sheet = sheet.duplicate(insert_sheet_index=idx, new_sheet_name=name)
    new_sheet = new_sheet.batch_clear(['A11:K23'])


# In[31]:


def input_basic_info(sheet, order_no, retailer, order_list):
    
    from gspread.cell import Cell
    import pandas as pd
    
    # 기본 정보 및 판매 합계 입력
    order_id = Cell(2, 2, order_no)
    retail_name = Cell(2, 7, retailer)
    issue_date = Cell(8, 1, getToday())
    
    
    # 합계 입력
    df = pd.DataFrame(order_list)
    df['tot_price'] = df['quantity']*df['price']

    tot_price = int(df['tot_price'].sum())
    
    top_tot_price = Cell(8, 4, tot_price)
    bottom_tot_price = Cell(24, 11, tot_price)
    
    sheet.update_cells([order_id, retail_name, issue_date, top_tot_price, bottom_tot_price])


def eliminate_null_data(order_list):
    
    import pandas as pd
    import json

    df = pd.DataFrame(order_list)
    df = df[~df['price'].isnull()]
    order_list = json.loads(df.to_json(orient='records', 
                                       force_ascii=False))
    
    return order_list


def export_pdf(new_title, credential, doc):
    
    import requests
    # I added below script

    url = 'https://docs.google.com/spreadsheets/export?format=pdf&size=statement&gridlines=false&scale=3&horizontal_alignment=CENTER&vertical_alignment=CENTER&id=' + doc.id
    headers = {'Authorization': 'Bearer ' + credential.create_delegated("").get_access_token().access_token}
    res = requests.get(url, headers=headers)

    with open('./tmp_storage/' + new_title + ".pdf", 'wb') as f:
        f.write(res.content) 
        
    return print('finish exporting pdf')


def upload_receipt_to_s3(new_title): # f = 파일명
    
    import boto3
    from config import ACCESS_KEY_ID, ACCESS_SECRET_KEY, BUCKET_NAME
    
    import os
    
    s3_client = boto3.client(
                's3',
                aws_access_key_id=ACCESS_KEY_ID,
                aws_secret_access_key=ACCESS_SECRET_KEY
    )
    
    response = s3_client.upload_file(
        f'tmp_storage/{new_title}.pdf', 
        BUCKET_NAME, 
        f'file-process-service-storage/{new_title}.pdf')
    
    
    tmp_file = f'tmp_storage/{new_title}.pdf'
    if os.path.isfile(tmp_file):
        os.remove(tmp_file)
    
    return print('finish upload pdf to s3')


def create_receipt_file_contents(order_no, retailer, order_items, sheet):
    
    from math import ceil
    
    receipt_num = ceil(len(order_items) / 13)

    for n in range(receipt_num):

        if n == 0 :

            # 기본 정보 입력
            input_basic_info(sheet, order_no, retailer, order_items)

            cells = []

            end = (n+1)*13

            for i, d in enumerate(order_items[:end]):

                num = i+11
                cells = generate_input_data(d, num, cells)

            sheet.update_cells(cells)

        elif n > 0 :

            name = f'Sheet{str(n+1)}'
            generate_new_sheet(n, sheet, name)

            new_sheet = doc.worksheet(name)

            cells = []

            start = n*13
            end = (n+1)*13

            for i, d in enumerate(order_items[start:end]):

                num = i+11
                cells = generate_input_data(d, num, cells)

            new_sheet.update_cells(cells)        


def execute_file_process(json_object, receipt_form_name):

    from oauth2client.service_account import ServiceAccountCredentials
    import gspread
    from gspread.cell import Cell

    # 인증 설정하기
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    json_key_path = "./credential/eloquent-branch-369106-1e961c642259.json"# JSON Key File Path

    credential = ServiceAccountCredentials.from_json_keyfile_name(json_key_path, scope)
    
    global gc
    
    gc = gspread.authorize(credential)


    order_no, retailer, wholesaler, order_items = data_parsing(json_object)
    order_items = eliminate_null_data(order_items)
    
    
    file_name = receipt_form_name
    new_title = f"receipt_{wholesaler}_"+str(order_no)

    doc = new_receipt_file(file_name, new_title)
    sheet1 = doc.worksheet("Sheet1")

    print('기본 세팅 완료')

    create_receipt_file_contents(order_no, retailer, order_items, sheet1)

    print('스프레드시트 내 데이터 입력 완료')

    export_pdf(new_title, credential, doc)

    upload_receipt_to_s3(new_title)


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
    
    execute_file_process(json_object, receipt_form_name)

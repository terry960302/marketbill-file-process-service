#!/usr/bin/env python
# coding: utf-8
import random
from datetime import datetime
from pytz import timezone
import boto3
from botocore.client import BaseClient
from config import ACCESS_KEY_ID, ACCESS_SECRET_KEY, BUCKET_NAME
import os
from math import ceil
from models.receipt_process_input import ReceiptProcessInput, OrderItem, Flower, FlowerType
from models.receipt_process_output import ReceiptProcessOutput
from models.pdf_order_item import PdfOrderItem
from typing import List
import time
from pathlib import Path
from PyPDF2 import PdfFileReader
from utils.pdf_generator import PdfGenerator
from reportlab.platypus import PageBreak
import logging
import inspect
from constants import strings

# 로그
logger = logging.getLogger("receipt_service")
logging.basicConfig(format=strings.LOGGER_FORMAT)
logger.setLevel(logging.INFO)


class ReceiptService:
    SCOPE = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    ROOT_DIR = Path(__file__).parent.parent

    TMP_STORAGE_PATH = f'{ROOT_DIR if ROOT_DIR != "/" else ""}/tmp_storage'
    PDF_FORMAT = ".pdf"
    REMOTE_STORAGE_TYPE = "s3"
    REMOTE_STORAGE_DIR = "file-process-service-storage"
    REMOTE_STORAGE_URI_PREFIX = "https://marketbill-storage.s3.ap-northeast-2.amazonaws.com/"
    REMOTE_CDN_URI_PREFIX = "https://d23zpri05ibxyp.cloudfront.net"

    def __init__(self, data: ReceiptProcessInput):
        self.remote_storage_dir = ReceiptService.REMOTE_STORAGE_DIR
        self.remote_storage_type = ReceiptService.REMOTE_STORAGE_TYPE
        self.tmp_storage_path = ReceiptService.TMP_STORAGE_PATH
        self.pdf_format = ReceiptService.PDF_FORMAT
        # s3에 저장될 파일명
        file_name: str = f"receipt_{data.wholesaler.companyName}_{data.orderNo}"
        self.file_name = file_name
        # pdf 파일 저장 경로
        self.pdf_file_path: str = f'{self.tmp_storage_path}/{file_name}{self.pdf_format}'

        self.order_no = data.orderNo
        self.retailer = data.retailer
        self.wholesaler = data.wholesaler
        self.order_items: List[OrderItem] = self._filter_empty_price(data.orderItems)
        return

    @staticmethod
    def _get_today():
        today = datetime.now(timezone('Asia/Seoul'))
        today = datetime.strftime(today, '%Y-%m-%d')
        return today

    @staticmethod
    def _filter_empty_price(order_list: List[OrderItem]) -> List[OrderItem]:
        def is_non_empty_price(item: OrderItem):
            is_not_null_price = item.price is not None
            return is_not_null_price and item.price > 0

        return list(filter(is_non_empty_price, order_list))

    @staticmethod
    def _get_profile() -> str:
        profile = os.environ.get("PROFILE")
        if profile is None:
            profile = "local"
        else:
            profile = str(profile)
        return profile

    @staticmethod
    def reformat_address(address: str, company_phone_no: str) -> str:
        try:
            max_letters_per_line = 45
            if len(address) <= max_letters_per_line:
                address = f'{address}\n'
            else:
                address = address[:max_letters_per_line] \
                          + "\n" \
                          + address[max_letters_per_line:]
            logger.info('completed.')
            return f'{address} ☎ {company_phone_no}'
        except Exception as e:
            logger.error(e)
            raise

    @staticmethod
    def reformat_company_name(company_name: str) -> str:
        try:
            max_letters_per_line = 15
            if len(company_name) > max_letters_per_line:
                company_name = company_name[:max_letters_per_line] \
                               + "\n" \
                               + company_name[max_letters_per_line:]
            logger.info('completed.')
            return company_name
        except Exception as e:
            logger.error(e)
            raise

    def process_receipt_pdf(self):
        try:
            pdf_buffer = self.create_pdf_from_data()
            logger.info("1. pdf 파일 생성 완료")
            metadata = self.upload_receipt_to_s3(pdf_buffer)
            logger.info("2. s3 업로드 완료")
            output = self.create_output(metadata)
            logger.info('completed.')
            return output
        except Exception as e:
            logger.error(e)
            raise

    def create_pdf_from_data(self):
        try:
            pdf_generator = PdfGenerator(file_name=self.file_name)

            calc_prices = list(map(lambda item: item.price * item.quantity, self.order_items))
            tot_price = sum(calc_prices)
            items = list(
                map(lambda item: PdfOrderItem(name=f'({item.flower.flowerType.name}){item.flower.name}-{item.grade}',
                                              unit_price=item.price, quantity=item.quantity), self.order_items))

            form_elements = pdf_generator.create_form_elements(order_no=self.order_no,
                                                               receipt_owner=self.retailer.name,
                                                               business_no=self.wholesaler.businessNo,
                                                               company_name=ReceiptService.reformat_company_name(
                                                                   self.wholesaler.companyName),
                                                               employer_name=self.wholesaler.employerName,
                                                               address=ReceiptService.reformat_address(
                                                                   self.wholesaler.address,
                                                                   self.wholesaler.companyPhoneNo),
                                                               business_category=self.wholesaler.businessMainCategory,
                                                               business_sub_category=self.wholesaler.businessSubCategory,
                                                               stamp_img_url=self.wholesaler.sealStampImgUrl,
                                                               tot_price=tot_price,
                                                               etc="", prev_balance=None, deposit=None,
                                                               balance=None, bank_account=self.wholesaler.bankAccount)
            max_row = 13
            items_section_idx = 4
            page_num = ceil(len(items) / max_row)
            elements = []

            for i in range(page_num):
                if i != 0:
                    elements.append(PageBreak())
                elements.extend(form_elements)
                partial_items = items[i * max_row: (i + 1) * max_row]
                items_section = pdf_generator.create_items_section(items=partial_items)
                elements.insert(items_section_idx + (i * 8), items_section)
            pdf_generator.doc.build(elements)
            logger.info('completed.')
            return pdf_generator.buffer
        except Exception as e:
            logger.error(e)
            raise

    # common
    def upload_receipt_to_s3(self, buffer) -> str:
        try:
            profile = self._get_profile()
            object_name = f'{self.remote_storage_dir}/{profile}/{self.file_name}{self.pdf_format}'

            pdf = PdfFileReader(buffer)
            pdf_info = pdf.getDocumentInfo()
            pdf_metadata = str(pdf_info)

            s3_client: BaseClient = boto3.client(
                self.remote_storage_type,
                aws_access_key_id=ACCESS_KEY_ID,
                aws_secret_access_key=ACCESS_SECRET_KEY
            )

            # 파일을 다시 읽을 수 있도록 처음부터 읽게 설정
            buffer.seek(0)
            # 자동으로 Buffer가 close되므로 buffer.close() 가 필요없음
            s3_client.upload_fileobj(
                buffer,
                BUCKET_NAME,
                object_name)
            logger.info('completed.')
            return pdf_metadata
        except Exception as e:
            logger.error(e)
            raise

    # common
    def create_output(self, pdf_metadata: str) -> ReceiptProcessOutput:
        # [Warning] remote_dir 경로를 제외하고 요청을 보내야 CDN 을 통해 파일을 읽을 수 있습니다.(CDN 의 origin 소스 경로 설정으로 인해.)
        try:
            profile = self._get_profile()
            cached_file_path = f'{ReceiptService.REMOTE_CDN_URI_PREFIX}/{profile}/{self.file_name}{self.pdf_format}'
            logger.info('completed.')
            return ReceiptProcessOutput(
                file_name=self.file_name,
                file_format=self.pdf_format,
                file_path=cached_file_path,
                metadata=pdf_metadata
            )
        except Exception as e:
            logger.error(e)
            raise

# def _create_json_mock(num: int = 100) -> dict:
#     cur_time = datetime.now().strftime("%Y.%m.%d-%h:%m:%s")
#     today = datetime.now(timezone('Asia/Seoul'))
#     today = datetime.strftime(today, '%Y%m%d')
#     basic_info = {
#         "orderNo": f'{today}M1230918',
#         "retailer": {
#             "name": "꽃소매"
#         },
#         "wholesaler": {
#             "businessNo": "98733987123",
#             "companyName": "(주)꿀벌원예" + cur_time,
#             "employerName": "배갑순",
#             # "sealStampImgUrl": "https://user-images.githubusercontent.com/37768791/207530270-d38c7770-642e-433a-b93f-db14bcca74e1.png",
#             "sealStampImgUrl": "https://tokyo.hanko.club/ko/wp-content/uploads/sites/15/2002/12/92b3958e876345074354b392f452a10d.jpg",
#             "address": "서울특별시 서초구 강남대로 27, 146호 (양재동, 화훼유통공사생화매장)asldljasjdlkjalsd",
#             # "address": "ㅁㄴ아ㅣㅓㅁ니ㅏ어ㅣ먼이ㅓㅁㄴㅇ",
#             "companyPhoneNo": "2978123-1238",
#             "businessMainCategory": "도매 및 소매업",
#             "businessSubCategory": "화초 및 산식물 도소매업",
#             "bankAccount": "농협 : 351-5249-3199-43 (주)꿀벌원예",
#         },
#     }
#
#     items = []
#     for i in range(0, num):
#         item = {
#             "flower": {
#                 "name": "테데오옐로우",
#                 "flowerType": {
#                     "name": "국화"
#                 }
#             },
#             "quantity": 17,
#             "grade": "상",
#             "price": 10000
#         }
#         item["flower"]["name"] = f'랜덤꽃{i}'
#         # item["price"] = random.randrange(1000, 10000)
#         if i == 0:
#             item["price"] = None
#         else:
#             item["price"] = random.randrange(1000, 10000)
#         item["quantity"] = random.randrange(10, 100)
#         items.append(item)
#
#
#     basic_info["orderItems"] = items
#     return basic_info
#
#
# if __name__ == "__main__":
#     mock_data = _create_json_mock(13)
#
#     start_time = time.time()
#     input = ReceiptProcessInput(**mock_data)
#     service = ReceiptService(input)
#     output = service.process_receipt_pdf()
#     print(output)
#     print("총 소요시간 --- %s seconds ---" % (time.time() - start_time))

import os

from reportlab.platypus import SimpleDocTemplate, Image, PageBreak
from reportlab.platypus.tables import Table
from reportlab.platypus.tables import colors
from reportlab.lib.pagesizes import letter, inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from pathlib import Path
from typing import Union, List
import urllib3
import io
from models.pdf_order_item import PdfOrderItem
from datetime import datetime
from pytz import timezone
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class PdfGenerator:
    NANUM_GOTHIC_400 = "nanum_gothic"
    NANUM_GOTHIC_600 = "nanum_gothic_600"
    NANUM_GOTHIC_700 = "nanum_gothic_700"
    PDF_FORMAT = "pdf"
    ROOT_DIR = Path(__file__).parent.parent
    FONT_DIR = f'{ROOT_DIR if ROOT_DIR != "/" else ""}/fonts'
    TMP_STORAGE_DIR = f'{ROOT_DIR if ROOT_DIR != "/" else ""}/tmp_storage'

    def __init__(self, file_name: str, directory: Union[None, str] = None):
        self.font_dir = PdfGenerator.FONT_DIR
        self.tmp_storage_dir = PdfGenerator.TMP_STORAGE_DIR
        self.pdf_format = PdfGenerator.PDF_FORMAT
        self.pdf_path = f'{self.tmp_storage_dir if directory is None else directory}/{file_name}.{self.pdf_format}'
        self.cm = 2.54
        self.font_400 = PdfGenerator.NANUM_GOTHIC_400
        self.font_600 = PdfGenerator.NANUM_GOTHIC_600
        self.font_700 = PdfGenerator.NANUM_GOTHIC_700
        # Setup fonts
        pdfmetrics.registerFont(TTFont("nanum_gothic", f'{self.font_dir}/NanumGothic-Regular.ttf'))
        pdfmetrics.registerFont(TTFont("nanum_gothic_600", f'{self.font_dir}/NanumGothic-Bold.ttf'))
        pdfmetrics.registerFont(
            TTFont("nanum_gothic_700", f'{self.font_dir}/NanumGothic-ExtraBold.ttf'))
        # width : 7 inch(total)
        # : PDF 생성할 시 전체 너비입니다. 컬럼의 폭을 계산할 때 참고하는 목적이 있습니다. 여기선 7인치로 설정하여 작업했습니다.
        buffer = io.BytesIO()
        self.buffer = buffer
        self.doc = SimpleDocTemplate(buffer, pagesize=letter, title=file_name, author="Team Marketbill",
                                     creator="Taewan Kim", subject="마켓빌 영수증",
                                     producer="Powered by reportlab PDF library.")
        return

    @staticmethod
    def _get_today():
        today = datetime.now(timezone('Asia/Seoul'))
        today = datetime.strftime(today, '%Y-%m-%d')
        return today

    @staticmethod
    def format_currency(num: int) -> str:
        if num is None:
            return "-"
        return '{:,.0f}'.format(num)

    @staticmethod
    def download_url_image(url: str) -> io.BytesIO:
        try:
            http = urllib3.PoolManager()
            response = http.request('GET', url, preload_content=False)
            buffered_response = io.BufferedReader(response, 2048)
            img_bytes = buffered_response.read()
            return io.BytesIO(img_bytes)
        except Exception as e:
            msg = f'## Failed to download stamp image from URL ({url}). : {e}'
            logger.error(msg)
            raise

    def create_header(self, title: str) -> Table:
        data = [[title, '', '', '', '']]
        style = [
            ('SPAN', (0, 0), (-1, 0),),
            ('ALIGN', (0, 0), (-1, 0), "CENTER"),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.black),
            ('LINEBEFORE', (0, 0), (-1, 0), 2, colors.black),
            ('LINEAFTER', (0, 0), (-1, 0), 2, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), self.font_700),
        ]
        table: Table = Table(data, colWidths=[1.4 * inch] * 5, rowHeights=[0.5 * inch] * 1, style=style)
        return table

    def create_sub_header(self, order_no: str, name: str) -> Table:
        col_widths = [0.5 * inch, 2 * inch, 1.5 * inch, 2 * inch, 1 * inch]
        row_heights = [0.5 * inch] * 1
        data = [["No.", order_no, '', name, '귀하']]
        style = [
            ('ALIGN', (1, 0), (-1, 0), "CENTER"),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('LINEBEFORE', (0, 0), (0, 0), 2, colors.black),
            ('LINEAFTER', (-1, 0), (-1, 0), 2, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), self.font_400),
        ]

        table: Table = Table(data, colWidths=col_widths,
                             rowHeights=row_heights, style=style)
        return table

    # 공급자 섹션
    def create_supply_section(self, business_no: str, company_name: str, name: str, address: str,
                              business_category: str, business_sub_category: str, stamp_img_url: str) -> Table:
        # 가로로 최대 6칸 필요
        col_widths = [0.75 * inch, 1 * inch, 2 * inch, 0.25 * inch, 1.5 * inch, 1.5 * inch]
        height = 0.4 * inch
        row_heights = [height] * 4

        try:
            image_buffer = PdfGenerator.download_url_image(stamp_img_url)
            origin_img = ImageReader(image_buffer)
            origin_width, origin_height = origin_img.getSize()
            stamp_img = Image(image_buffer)
            stamp_img.drawHeight = height
            stamp_img.drawWidth = (height / origin_height) * origin_width
            stamp_item = stamp_img if stamp_img is not None else "(인)"

            data = [["공\n급\n자", "사업자\n등록번호", business_no, "", '', ""],
                    ["", "상호", company_name, "성\n명", name, stamp_item],
                    ["", "사업장\n소재지", address, '', '', ""],
                    ["", "업태", business_category, "종\n목", business_sub_category]]
            style = [
                ("SPAN", (0, 0), (0, -1)),  # 공급자 수직 셀병합
                ("SPAN", (2, 0), (-1, 0)),  # 사업자등록번호 row 셀병합
                ("SPAN", (2, 2), (-1, 2)),  # 사업장 소재지 row 셀병합
                ("SPAN", (-2, -1), (-1, -1)),  # 종목 셀병합
                ('ALIGN', (0, 0), (-1, -1), "CENTER"),  # 전체 텍스트 중앙정렬
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # 공급자 텍스트 수직 중앙배치
                ('FONTSIZE', (0, 0), (-1, -1), 10),  # 전체 영역 10포인트
                ('LINEBELOW', (0, 0), (-1, -1), 1, colors.black),
                ('LINEBEFORE', (0, 0), (0, -1), 2, colors.black),
                ('LINEBEFORE', (1, 0), (0, -1), 1, colors.black),
                ('LINEAFTER', (-1, 0), (-1, -1), 2, colors.black),
                ('LINEAFTER', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 0), (-1, -1), self.font_400),  # 전체 폰트 적용
                ('FONTNAME', (2, 0), (2, 0), self.font_600),  # 사업자 등록 번호에만 적용
                ('FONTSIZE', (2, 0), (2, 0), 12),  # 사업자 등록 번호에만 적용
            ]

            table: Table = Table(data, colWidths=col_widths,
                                 rowHeights=row_heights,
                                 style=style)
            logger.info('## [create_supply_section] completed.')
            return table
        except Exception as e:
            msg = f'## Failed to create_supply_section : {e}'
            logger.error(msg)
            raise

            # 작성년월일, 공급대가 총액 섹션

    def create_upper_tot_price_section(self, created_at: str, tot_price: int, etc: str) -> Table:
        # 가로로 최대 4칸만 필요
        col_widths = [2 * inch, 0.4 * inch, 2.6 * inch, 2 * inch]
        row_heights = [0.3 * inch] * 3
        tot_price = PdfGenerator.format_currency(tot_price)
        data = [["작성년월일", "공급대가 총액", "", "비고"],
                [created_at, "￦", tot_price, etc],
                ["위 금액을 영수(청구)함", "", "", ""]]

        style = [
            ("SPAN", (1, 0), (2, 0)),  # 공급대가 총액 셀병합
            ("SPAN", (0, -1), (-1, -1)),  # 위 금액을 영수(청구)함 row 셀병합
            ('ALIGN', (0, 0), (-1, -1), "CENTER"),  # 전체 텍스트 중앙정렬
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # 공급자 텍스트 수직 중앙배치
            ('FONTSIZE', (0, 0), (-1, -1), 10),  # 전체 영역 12포인트
            ('LINEBELOW', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBEFORE', (0, 0), (0, -1), 2, colors.black),
            ('LINEBEFORE', (1, 0), (0, -1), 1, colors.black),
            ('LINEAFTER', (-1, 0), (-1, -1), 2, colors.black),
            ('LINEAFTER', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), self.font_400),
        ]

        table: Table = Table(data, colWidths=col_widths, rowHeights=row_heights, style=style)
        logger.info('## [create_upper_tot_price_section] completed.')
        return table

    # items 는 총 13개까지만 들어갈 수 있음(더 넣어야하면 pdf page break 필요)
    def create_items_section(self, items=List[PdfOrderItem]) -> Table:
        total_row = 14  # 헤더 포함
        max_row = total_row - 1  # 헤더 제외

        # 최대 4 column 이 필요
        col_widths = [2.5 * inch, 1 * inch, 1.5 * inch, 2 * inch]
        row_heights = [0.3 * inch] * total_row

        empty_row: List[str] = ["", "", "", ""]  # 아이템 항목 정보가 들어갈 빈 row 13개 필요(5배수 row 마다 아래 굵은 border 필요)
        header = [["품목", "수량", "단가", "공급대가(금액)"]]
        for i in range(0, max_row):
            if i < len(items):
                item: PdfOrderItem = items[i]
                item_row = [item.name, item.quantity, item.unit_price, item.tot_price]
                header.append(item_row)
            else:
                header.append(empty_row)
        data = header

        style = [
            ('ALIGN', (0, 0), (-1, -1), "CENTER"),  # 전체 텍스트 중앙정렬
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # 공급자 텍스트 수직 중앙배치
            ('FONTSIZE', (0, 0), (-1, -1), 10),  # 전체 영역 12포인트
            ('LINEBELOW', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, 5), (-1, 5), 2, colors.black),
            ('LINEBELOW', (0, 10), (-1, 10), 2, colors.black),
            ('LINEBEFORE', (0, 0), (0, -1), 2, colors.black),
            ('LINEBEFORE', (1, 0), (0, -1), 1, colors.black),
            ('LINEAFTER', (-1, 0), (-1, -1), 2, colors.black),
            ('LINEAFTER', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), self.font_400),
        ]

        table: Table = Table(data, colWidths=col_widths, rowHeights=row_heights, style=style)
        logger.info('## [create_items_section] completed.')
        return table

    # prev_balance : 전잔액
    # balance : 잔액
    # deposit : 입금
    def create_footer(self, prev_balance: Union[int, None], tot_price: Union[int, None], deposit: Union[int, None],
                      balance: Union[int, None]) -> Table:
        prev_balance = PdfGenerator.format_currency(prev_balance)
        tot_price = PdfGenerator.format_currency(tot_price)
        deposit = PdfGenerator.format_currency(deposit)
        balance = PdfGenerator.format_currency(balance)

        # 최대 4 column 이 필요
        col_widths = [1.5 * inch, 2 * inch, 1.5 * inch, 2 * inch]
        row_heights = [0.3 * inch] * 2

        data = [["전잔액", prev_balance, "합계", tot_price],
                ["입금", deposit, "잔액", balance], ]

        style = [
            ('ALIGN', (0, 0), (-1, -1), "CENTER"),  # 전체 텍스트 중앙정렬
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # 공급자 텍스트 수직 중앙배치
            ('FONTSIZE', (0, 0), (-1, -1), 10),  # 전체 영역 10포인트
            ('LINEBELOW', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, -1), (-1, -1), 2, colors.black),
            ('LINEBEFORE', (0, 0), (0, -1), 2, colors.black),
            ('LINEBEFORE', (1, 0), (0, -1), 1, colors.black),
            ('LINEAFTER', (-1, 0), (-1, -1), 2, colors.black),
            ('LINEAFTER', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), self.font_400),
        ]

        table: Table = Table(data, colWidths=col_widths, rowHeights=row_heights, style=style)
        logger.info('## [create_footer] completed.')
        return table

    def create_extra_footer(self, bank_account: str):
        # 최대 4 column 이 필요
        col_widths = [7 * inch]
        row_heights = [0.4 * inch] * 1

        data = [[bank_account]]

        style = [
            ('ALIGN', (0, 0), (-1, -1), "CENTER"),  # 전체 텍스트 중앙정렬
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # 전체 텍스트 수직 중앙배치
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('FONTNAME', (0, 0), (-1, -1), self.font_600),
        ]

        table: Table = Table(data, colWidths=col_widths, rowHeights=row_heights, style=style)
        logger.info('## [create_extra_footer] completed.')
        return table

    # 반환된 elements 배열의 4번째 index 에 items_sections 을 생성 후 넣어주면 됨
    def create_form_elements(self, order_no: str, receipt_owner: str, business_no: str, company_name: str,
                             employer_name: str, address: str, business_category: str, business_sub_category,
                             stamp_img_url: str, tot_price: int, etc: str,
                             prev_balance: Union[None, int],
                             deposit: Union[None, int],
                             balance: Union[None, int], bank_account: str):
        title = "영수증"
        created_at = PdfGenerator._get_today()

        header = self.create_header(title=title)
        sub_header = self.create_sub_header(order_no=order_no, name=receipt_owner)
        supply_section = self.create_supply_section(business_no=business_no,
                                                    company_name=company_name,
                                                    name=employer_name,
                                                    address=address,
                                                    business_category=business_category,
                                                    business_sub_category=business_sub_category,
                                                    stamp_img_url=stamp_img_url)
        upper_tot_price_section = self.create_upper_tot_price_section(created_at=created_at, tot_price=tot_price,
                                                                      etc=etc)
        footer = self.create_footer(prev_balance=prev_balance, deposit=deposit, tot_price=tot_price, balance=balance)
        extra_footer = self.create_extra_footer(bank_account=bank_account)

        # 4 index에 items_section element가 들어가면 됩니다.
        return [header, sub_header, supply_section, upper_tot_price_section, footer, extra_footer]

# def _create_json_mock(num: int = 100) -> dict:
#     today = datetime.now(timezone('Asia/Seoul'))
#     today = datetime.strftime(today, '%Y%m%d')
#     basic_info = {
#         "orderNo": f'{today}M1230918',
#         "retailer": {
#             "name": "꽃소매"
#         },
#         "wholesaler": {
#             "name": "꽃도매"
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
#         item["price"] = random.randrange(1000, 10000)
#         item["quantity"] = random.randrange(10, 100)
#         items.append(item)
#
#     basic_info["orderItems"] = items
#     return basic_info
#
#
# if __name__ == "__main__":
#     start_time = time.time()
#
#     ROOT_DIR = Path(__file__).parent.parent
#     TMP_STORAGE = f'{ROOT_DIR if ROOT_DIR != "/" else ""}/tmp_storage'
#     pdf_generator = PdfGenerator(f'{TMP_STORAGE}/reportlab_sample_receipt.pdf')
#     json_object = _create_json_mock(30)
#     json_input = ReceiptProcessInput(**json_object)
#
#     calc_prices = list(map(lambda item: item.price * item.quantity, json_input.orderItems))
#     tot_price = sum(calc_prices)
#     items = list(map(lambda item: PdfOrderItem(name=f'({item.flower.flowerType.name}){item.flower.name}-{item.grade}',
#                                                unit_price=item.price, quantity=item.quantity), json_input.orderItems))
#
#     form_elements = pdf_generator.create_form_elements(order_no=json_input.orderNo,
#                                                        receipt_owner=json_input.retailer.name,
#                                                        business_no="244-88-01311", company_name="주식회사 꿀벌원예",
#                                                        person_name="배갑순",
#                                                        address="서울특별시 서초구 강남대로 27, 146호\n(양재동, 화훼유통공사생화매장) ☎ 579-3199",
#                                                        business_category="도매 및 소매업",
#                                                        business_sub_category="화초 및 산식물 도소매업",
#                                                        stamp_img_url="https://user-images.githubusercontent.com/37768791/207530270-d38c7770-642e-433a-b93f-db14bcca74e1.png",
#                                                        tot_price=tot_price,
#                                                        etc="", prev_balance=None, deposit=None,
#                                                        balance=None, bank_account="농협 : 351-5249-3199-43 (주)꿀벌원예")
#     max_row = 13
#     items_section_idx = 4
#     page_num = ceil(len(items) / max_row)
#     elements = []
#
#     for i in range(page_num):
#         if i != 0:
#             elements.append(PageBreak())
#         elements.extend(form_elements)
#         partial_items = items[i * max_row: (i + 1) * max_row]
#         items_section = pdf_generator.create_items_section(items=partial_items)
#         elements.insert(items_section_idx + (i * 8), items_section)
#     pdf_generator.doc.build(elements)
#     print("총 소요시간 --- %s seconds ---" % (time.time() - start_time))

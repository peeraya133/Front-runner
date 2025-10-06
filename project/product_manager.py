# product_manager.py
import struct
import os

PRODUCT_FILE = "products.dat"
PRODUCT_STRUCT = struct.Struct('<i30si')  # pro_id, pro_name, promotion_id

def init_product_file():
    if not os.path.exists(PRODUCT_FILE):
        with open(PRODUCT_FILE, 'wb') as f:
            pass  # สร้างไฟล์เปล่า

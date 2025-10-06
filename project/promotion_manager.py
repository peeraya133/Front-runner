# promotion_manager.py
import struct
import os

PROMOTION_FILE = "promotions.dat"
PROMOTION_STRUCT = struct.Struct('<i30s')  # promotion_id, promotion_name

def init_promotion_file():
    if not os.path.exists(PROMOTION_FILE):
        with open(PROMOTION_FILE, 'wb') as f:
            pass

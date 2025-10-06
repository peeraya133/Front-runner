# price_manager.py
import struct
import os

PRICE_FILE = "prices.dat"
PRICE_STRUCT = struct.Struct('<i10sfiB')  # pro_id, size, price, stock, status

def init_price_file():
    if not os.path.exists(PRICE_FILE):
        with open(PRICE_FILE, 'wb') as f:
            pass

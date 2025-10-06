import struct
import os
from datetime import datetime

# --- Constants & Structs ---

PRODUCT_FILE = "products.dat"
PRICE_FILE = "prices.dat"
PROMOTION_FILE = "promotions.dat"
LOG_FILE = "log.txt"
REPORT_FILE = "report.txt"

# Struct format:
# Product: pro_id(10 bytes string), pro_name(30 bytes string), promotion_id(int)
PRODUCT_STRUCT = struct.Struct('<10s30si')

# Price: pro_id(10 bytes string), pro_size(10 bytes string), pro_price(float), pro_stock(int), sale_status(unsigned char)
PRICE_STRUCT = struct.Struct('<10s10sfiB')

# Promotion: promotion_id(int), promotion_name(30 bytes string)
PROMOTION_STRUCT = struct.Struct('<i30s')

# --- Helper Functions ---

def log_event(actor, action, status="OK", detail=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {actor} - {action}: {detail} -> {status}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)

def pad_string(s, length):
    b = s.encode('utf-8')[:length]
    return b.ljust(length, b'\x00')

def read_all_records(filename, record_size):
    if not os.path.exists(filename):
        return []
    with open(filename, 'rb') as f:
        data = f.read()
    return [data[i:i+record_size] for i in range(0, len(data), record_size)]

def write_all_records(filename, record_size, records):
    with open(filename, 'wb') as f:
        for rec in records:
            f.write(rec)

# --- CRUD for Products ---

def add_product():
    try:
        pro_id = input("Enter product ID: ").strip()
        pro_name = input("Enter product name (max 30 chars): ")[:30]
        promotion_id = int(input("Enter promotion ID (int): "))

        # Check if pro_id already exists
        products = read_all_records(PRODUCT_FILE, PRODUCT_STRUCT.size)
        for rec in products:
            pid_bytes, _, _ = PRODUCT_STRUCT.unpack(rec)
            pid = pid_bytes.decode('utf-8').rstrip('\x00')
            if pid == pro_id:
                print(f"Product ID {pro_id} already exists.")
                return

        packed = PRODUCT_STRUCT.pack(pad_string(pro_id, 10), pad_string(pro_name, 30), promotion_id)
        with open(PRODUCT_FILE, 'ab') as f:
            f.write(packed)

        log_event("USER", f"Add Product ID {pro_id}")
        print("Product added.")
    except Exception as e:
        print("Error adding product:", e)

def update_product():
    try:
        pro_id = input("Enter product ID to update: ").strip()
        products = read_all_records(PRODUCT_FILE, PRODUCT_STRUCT.size)
        updated = False
        new_products = []

        for rec in products:
            pid_bytes, pname_b, promo_id = PRODUCT_STRUCT.unpack(rec)
            pid = pid_bytes.decode('utf-8').rstrip('\x00')
            if pid == pro_id:
                print(f"Current name: {pname_b.decode('utf-8').rstrip(chr(0))}, promotion ID: {promo_id}")
                new_name = input("Enter new product name (leave blank to keep): ")
                new_promo = input("Enter new promotion ID (leave blank to keep): ")
                if new_name.strip() == '':
                    new_name = pname_b.decode('utf-8').rstrip(chr(0))
                if new_promo.strip() == '':
                    new_promo = promo_id
                else:
                    new_promo = int(new_promo)
                new_rec = PRODUCT_STRUCT.pack(pad_string(pro_id,10), pad_string(new_name,30), new_promo)
                new_products.append(new_rec)
                updated = True
            else:
                new_products.append(rec)

        if updated:
            write_all_records(PRODUCT_FILE, PRODUCT_STRUCT.size, new_products)
            log_event("USER", f"Update Product ID {pro_id}")
            print("Product updated.")
        else:
            print("Product ID not found.")
    except Exception as e:
        print("Error updating product:", e)

def delete_product():
    try:
        pro_id = input("Enter product ID to delete: ").strip()
        products = read_all_records(PRODUCT_FILE, PRODUCT_STRUCT.size)
        new_products = []
        deleted = False

        for rec in products:
            pid_bytes, _, _ = PRODUCT_STRUCT.unpack(rec)
            pid = pid_bytes.decode('utf-8').rstrip('\x00')
            if pid == pro_id:
                deleted = True
                continue
            new_products.append(rec)

        if deleted:
            write_all_records(PRODUCT_FILE, PRODUCT_STRUCT.size, new_products)
            log_event("USER", f"Delete Product ID {pro_id}")
            print("Product deleted.")
            delete_price_by_product(pro_id)
        else:
            print("Product ID not found.")
    except Exception as e:
        print("Error deleting product:", e)

def view_products():
    products = read_all_records(PRODUCT_FILE, PRODUCT_STRUCT.size)
    promotions = read_all_records(PROMOTION_FILE, PROMOTION_STRUCT.size)
    
    promo_dict = {}
    for rec in promotions:
        pid, pname_b = PROMOTION_STRUCT.unpack(rec)
        pname = pname_b.decode('utf-8').rstrip('\x00')
        promo_dict[pid] = pname
    
    if not products:
        print("No products found.")
        return
    
    print(f"\n{'ID':<10} {'Name':<30} {'PromotionName':<30}")
    print("-" * 70)
    for rec in products:
        pid_bytes, pname_b, promo_id = PRODUCT_STRUCT.unpack(rec)
        pid = pid_bytes.decode('utf-8').rstrip('\x00')
        pname = pname_b.decode('utf-8').rstrip('\x00')
        promo_name = promo_dict.get(promo_id, "No Promotion")
        print(f"{pid:<10} {pname:<30} {promo_name:<30}")

# --- CRUD for Prices ---

def add_price():
    try:
        pro_id = input("Enter product ID: ").strip()
        pro_size = input("Enter size (max 10 chars): ")[:10]
        pro_price = float(input("Enter price (float): "))
        pro_stock = int(input("Enter stock (int): "))
        sale_status = int(input("Enter sale status (0=not sell,1=sell): "))
        if sale_status not in (0,1):
            print("Sale status must be 0 or 1")
            return

        products = read_all_records(PRODUCT_FILE, PRODUCT_STRUCT.size)
        if not any(PRODUCT_STRUCT.unpack(p)[0].decode('utf-8').rstrip('\x00') == pro_id for p in products):
            print("Product ID does not exist. Please add product first.")
            return

        prices = read_all_records(PRICE_FILE, PRICE_STRUCT.size)
        for p in prices:
            pid, size_b, _, _, _ = PRICE_STRUCT.unpack(p)
            pid_str = pid.decode('utf-8').rstrip('\x00')
            size = size_b.decode('utf-8').rstrip('\x00')
            if pid_str == pro_id and size == pro_size:
                print("Price record for this product and size already exists.")
                return

        packed = PRICE_STRUCT.pack(pad_string(pro_id, 10), pad_string(pro_size,10), pro_price, pro_stock, sale_status)
        with open(PRICE_FILE, 'ab') as f:
            f.write(packed)

        log_event("USER", f"Add Price for Product ID {pro_id}, size {pro_size}")
        print("Price added.")
    except Exception as e:
        print("Error adding price:", e)

def update_price():
    try:
        pro_id = input("Enter product ID to update : ").strip()
        pro_size = input("Enter size to update: ")[:10]
        prices = read_all_records(PRICE_FILE, PRICE_STRUCT.size)
        updated = False
        new_prices = []

        for rec in prices:
            pid, size_b, price, stock, status = PRICE_STRUCT.unpack(rec)
            pid_str = pid.decode('utf-8').rstrip('\x00')
            size = size_b.decode('utf-8').rstrip('\x00')
            if pid_str == pro_id and size == pro_size:
                print(f"Current price: {price}, stock: {stock}, status: {status}")
                new_price = input("Enter new price (leave blank to keep): ")
                new_stock = input("Enter new stock (leave blank to keep): ")
                new_status = input("Enter new sale status (0/1, blank to keep): ")

                if new_price.strip() == '':
                    new_price = price
                else:
                    new_price = float(new_price)

                if new_stock.strip() == '':
                    new_stock = stock
                else:
                    new_stock = int(new_stock)

                if new_status.strip() == '':
                    new_status = status
                else:
                    new_status = int(new_status)
                    if new_status not in (0,1):
                        print("Sale status must be 0 or 1")
                        return

                new_rec = PRICE_STRUCT.pack(pad_string(pro_id,10), pad_string(pro_size,10), new_price, new_stock, new_status)
                new_prices.append(new_rec)
                updated = True
            else:
                new_prices.append(rec)

        if updated:
            write_all_records(PRICE_FILE, PRICE_STRUCT.size, new_prices)
            log_event("USER", f"Update Price Product ID {pro_id} Size {pro_size}")
            print("Price updated.")
        else:
            print("Price record not found.")
    except Exception as e:
        print("Error updating price:", e)

def delete_price():
    try:
        pro_id = input("Enter product ID to delete price: ").strip()
        pro_size = input("Enter size to delete: ")[:10]
        prices = read_all_records(PRICE_FILE, PRICE_STRUCT.size)
        new_prices = []
        deleted = False

        for rec in prices:
            pid, size_b, _, _, _ = PRICE_STRUCT.unpack(rec)
            pid_str = pid.decode('utf-8').rstrip('\x00')
            size = size_b.decode('utf-8').rstrip('\x00')
            if pid_str == pro_id and size == pro_size:
                deleted = True
                continue
            new_prices.append(rec)

        if deleted:
            write_all_records(PRICE_FILE, PRICE_STRUCT.size, new_prices)
            log_event("USER", f"Delete Price Product ID {pro_id} Size {pro_size}")
            print("Price deleted.")
        else:
            print("Price record not found.")
    except Exception as e:
        print("Error deleting price:", e)

def delete_price_by_product(pro_id):
    prices = read_all_records(PRICE_FILE, PRICE_STRUCT.size)
    new_prices = []
    for p in prices:
        pid_bytes = PRICE_STRUCT.unpack(p)[0]
        pid = pid_bytes.decode('utf-8').rstrip('\x00')
        if pid != pro_id:
            new_prices.append(p)
    write_all_records(PRICE_FILE, PRICE_STRUCT.size, new_prices)
    log_event("SYSTEM", f"Delete all prices of deleted product ID {pro_id}")

def view_prices():
    prices = read_all_records(PRICE_FILE, PRICE_STRUCT.size)
    if not prices:
        print("No price records found.")
        return
    print(f"\n{'ProductID':<10} {'Size':<10} {'Price':<10} {'Stock':<7} {'Status':<6}")
    print("-"*50)
    for rec in prices:
        pid, size_b, price, stock, status = PRICE_STRUCT.unpack(rec)
        pid_str = pid.decode('utf-8').rstrip('\x00')
        size = size_b.decode('utf-8').rstrip('\x00')
        status_str = "Sell" if status == 1 else "Not Sell"
        print(f"{pid_str:<10} {size:<10} {price:<10.2f} {stock:<7} {status_str:<6}")

# --- CRUD for Promotions ---

def add_promotion():
    try:
        promotion_id = int(input("Enter promotion ID (int): "))
        promotion_name = input("Enter promotion name (max 30 chars): ")[:30]
        promotions = read_all_records(PROMOTION_FILE, PROMOTION_STRUCT.size)
        for rec in promotions:
            pid, _ = PROMOTION_STRUCT.unpack(rec)
            if pid == promotion_id:
                print("Promotion ID already exists.")
                return
        packed = PROMOTION_STRUCT.pack(promotion_id, pad_string(promotion_name, 30))
        with open(PROMOTION_FILE, 'ab') as f:
            f.write(packed)
        log_event("USER", f"Add Promotion ID {promotion_id}")
        print("Promotion added.")
    except Exception as e:
        print("Error adding promotion:", e)

def update_promotion():
    try:
        promotion_id = int(input("Enter promotion ID to update: "))
        promotions = read_all_records(PROMOTION_FILE, PROMOTION_STRUCT.size)
        updated = False
        new_promos = []
        for rec in promotions:
            pid, pname_b = PROMOTION_STRUCT.unpack(rec)
            pname = pname_b.decode('utf-8').rstrip('\x00')
            if pid == promotion_id:
                print(f"Current name: {pname}")
                new_name = input("Enter new promotion name (leave blank to keep): ")
                if new_name.strip() == '':
                    new_name = pname
                new_rec = PROMOTION_STRUCT.pack(promotion_id, pad_string(new_name,30))
                new_promos.append(new_rec)
                updated = True
            else:
                new_promos.append(rec)
        if updated:
            write_all_records(PROMOTION_FILE, PROMOTION_STRUCT.size, new_promos)
            log_event("USER", f"Update Promotion ID {promotion_id}")
            print("Promotion updated.")
        else:
            print("Promotion ID not found.")
    except Exception as e:
        print("Error updating promotion:", e)

def delete_promotion():
    try:
        promotion_id = int(input("Enter promotion ID to delete: "))
        promotions = read_all_records(PROMOTION_FILE, PROMOTION_STRUCT.size)
        new_promos = []
        deleted = False
        for rec in promotions:
            pid, _ = PROMOTION_STRUCT.unpack(rec)
            if pid == promotion_id:
                deleted = True
                continue
            new_promos.append(rec)
        if deleted:
            write_all_records(PROMOTION_FILE, PROMOTION_STRUCT.size, new_promos)
            log_event("USER", f"Delete Promotion ID {promotion_id}")
            print("Promotion deleted.")
        else:
            print("Promotion ID not found.")
    except Exception as e:
        print("Error deleting promotion:", e)

def view_promotions():
    promotions = read_all_records(PROMOTION_FILE, PROMOTION_STRUCT.size)
    if not promotions:
        print("No promotions found.")
        return
    print(f"\n{'PromotionID':<12} {'Name':<30}")
    print("-" * 45)
    for rec in promotions:
        pid, pname_b = PROMOTION_STRUCT.unpack(rec)
        pname = pname_b.decode('utf-8').rstrip('\x00')
        print(f"{pid:<12} {pname:<30}")

# --- Report Generation ---

def generate_report():
    from textwrap import shorten

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    products = read_all_records(PRODUCT_FILE, PRODUCT_STRUCT.size)
    prices = read_all_records(PRICE_FILE, PRICE_STRUCT.size)
    promotions = read_all_records(PROMOTION_FILE, PROMOTION_STRUCT.size)

    # promotion_id -> promotion_name
    promo_dict = {}
    for rec in promotions:
        pid, pname_b = PROMOTION_STRUCT.unpack(rec)
        pname = pname_b.decode('utf-8').rstrip('\x00')
        promo_dict[pid] = pname

    # product_id -> (product_name, promotion_name)
    product_info = {}
    for rec in products:
        pid_bytes, pname_b, promo_id = PRODUCT_STRUCT.unpack(rec)
        pid = pid_bytes.decode('utf-8').rstrip('\x00')
        pname = pname_b.decode('utf-8').rstrip('\x00')
        promo_name = promo_dict.get(promo_id, "No Promotion")
        product_info[pid] = (pname, promo_name)

    # Header for combined table
    header = (
        "+------------+---------------------------+-------------+-------------------+---------+-------+------------+\n"
        "| Product ID | Product Name              | Size        | Promotion Name    | Price   | Stock | Status     |\n"
        "+------------+---------------------------+-------------+-------------------+---------+-------+------------+\n"
    )

    rows = ""
    for rec in prices:
        pid_bytes, size_b, price, stock, status = PRICE_STRUCT.unpack(rec)
        pid = pid_bytes.decode('utf-8').rstrip('\x00')
        size = size_b.decode('utf-8').rstrip('\x00')
        pname, promo_name = product_info.get(pid, ("Unknown", "No Promotion"))
        pname_short = shorten(pname, width=25, placeholder="...")
        promo_short = shorten(promo_name, width=20, placeholder="...")
        status_text = "Ready" if status == 1 else "Not Ready"
        rows += f"| {pid:<10} | {pname_short:<25} | {size:<11} | {promo_short:<17} | {price:<7.2f} | {stock:<5} | {status_text:<10} |\n"

    footer = "+------------+---------------------------+-------------+-------------------+---------+-------+------------+\n"

    # Print to Terminal
    print("\n=== Combined Product & Price Report ===")
    print(header + rows + footer)

    # Write to file
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("Burger Shop Report\n")
        f.write(f"Generated: {now}\n\n")
        f.write(f"Total Products: {len(products)}\n")
        f.write(f"Total Price Records: {len(prices)}\n\n")
        f.write(header + rows + footer)
        f.write("\nLast 10 Log Events:\n")

        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as logf:
                logs = logf.readlines()
                for line in logs[-10:]:
                    f.write(line)
        else:
            f.write("No log file found.\n")

    log_event("SYSTEM", "Generate Report")
    print(f"\n✅ Report written to {REPORT_FILE}")


def manage_products_menu():
    while True:
        print("\n--- Manage Products ---")
        print("1) Add Product")
        print("2) Update Product")
        print("3) Delete Product")
        print("4) View Products")
        print("0) Back to Main Menu")
        choice = input("Choose option: ")
        if choice == '1':
            add_product()
        elif choice == '2':
            update_product()
        elif choice == '3':
            delete_product()
        elif choice == '4':
            view_products()
        elif choice == '0':
            break
        else:
            print("Invalid option")

def manage_prices_menu():
    while True:
        print("\n--- Manage Prices ---")
        print("1) Add Price")
        print("2) Update Price")
        print("3) Delete Price")
        print("4) View Prices")
        print("0) Back to Main Menu")
        choice = input("Choose option: ")
        if choice == '1':
            add_price()
        elif choice == '2':
            update_price()
        elif choice == '3':
            delete_price()
        elif choice == '4':
            view_prices()
        elif choice == '0':
            break
        else:
            print("Invalid option")

def manage_promotions_menu():
    while True:
        print("\n--- Manage Promotions ---")
        print("1) Add Promotion")
        print("2) Update Promotion")
        print("3) Delete Promotion")
        print("4) View Promotions")
        print("0) Back to Main Menu")
        choice = input("Choose option: ")
        if choice == '1':
            add_promotion()
        elif choice == '2':
            update_promotion()
        elif choice == '3':
            delete_promotion()
        elif choice == '4':
            view_promotions()
        elif choice == '0':
            break
        else:
            print("Invalid option")

def main_menu():
    while True:
        print("\n===== Burger Shop Management =====")
        print("1) Manage Products")
        print("2) Manage Prices")
        print("3) Manage Promotions")
        print("4) Generate Report")
        print("0) Exit")
        print("===================================")
        choice = input("Choose option: ")
        if choice == '1':
            manage_products_menu()
        elif choice == '2':
            manage_prices_menu()
        elif choice == '3':
            manage_promotions_menu()
        elif choice == '4':
            generate_report()
        elif choice == '0':
            print("Goodbye!")
            break
        else:
            print("Invalid option")

if __name__ == "__main__":
    main_menu()

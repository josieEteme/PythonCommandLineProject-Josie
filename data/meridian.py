import argparse
import logging
import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).parent

csv_path = BASE_DIR / "meridian_trades_small.csv"
mrf_path = BASE_DIR / "meridian_trades_small.csv"
clean_data = BASE_DIR / "clean_data.csv"


FIELDNAMES = ["row_id", "trade_id", "instrument_id", "instrument_type",
              "trade_date", "buyer", "seller", "quantity", "price", "trade_status"]


#Need to read the file but not all at once (too much for memory) 
# A solution could be reading in chunks where each chunk is 10000 rows

masterDataTable = pd.read_csv(mrf_path, dtype=str, keep_default_na=False)

error_counts = {
    "missing_trade_id": 0,
    "invalid_trade_id_format": 0,
    "duplicate_trade_id": 0,
    "missing_instrument_id": 0,
    "invalid_date_format": 0,
    "missing_buyer": 0,
    "missing_seller": 0,
    "missing_quantity": 0,
    "invalid_quantity": 0,
    "invalid_price": 0,
    "negative_price": 0,
    "price_outOf_range":0,
    "self_trades": 0
    
}

def readCSV(csv_path):
    seen_ids = set()

    for chunk in pd.read_csv(csv_path, dtype=str, keep_default_na=False, chunksize=10_000):
        price = pd.to_numeric(chunk["price"], errors="coerce")
        qty = pd.to_numeric(chunk["quantity"], errors="coerce")

        # duplicates: repeated within this chunk, or already seen in an earlier chunk
        trade_id = chunk["trade_id"].str.strip()
        has_id = trade_id != ""
        is_dup = has_id & (trade_id.duplicated() | trade_id.isin(seen_ids))
        seen_ids.update(trade_id[has_id])
        num_invalid_rows = 0
        TRADE_ID_PATTERN = "^TRD-[0-9A-Fa-f]{10}$" #the regex defining the accepted str format. Also ^ and $ enforce a fixed str structure so only this structure returns true
        DATE_PATTERN = r"^(\d{4}-\d{2}-\d{2}|\d{4}\.\d{2}\.\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})$" #the r tells python that this is a raw string and to ignore backslashes 

        checks = {
            "missing_trade_id": chunk["trade_id"].str.strip() == "", 
            "invalid_trade_id_format": ~trade_id.str.match(TRADE_ID_PATTERN),
            "duplicate_trade_id": is_dup,
            "missing_instrument_id": chunk["instrument_id"].str.strip() == "",
            "invalid_date_format": ~chunk["trade_date"].str.strip().str.match(DATE_PATTERN), #not handling the invalid formats but rather detecting any missing dates or incompletes basically dates that dont match any of the four different formats that DATE_PATTERN provides 
            "missing_buyer": chunk["buyer"].str.strip() == "",
            "missing_seller": chunk["seller"].str.strip() == "",
            "missing_quantity": chunk["quantity"].str.strip() == "",
            "invalid_quantity": qty.isna() | (qty <= 0),
            "invalid_price": price.isna(),
            "negative_price": price < 0,
            "price_outOf_range": price > 500,
            "self_trades": chunk["seller"].str.strip() == chunk["buyer"].str.strip()
        }

        for name, mask in checks.items():
            error_counts[name] += int(mask.sum())
            num_invalid_rows += mask.sum()
        
            
# def flatten(t):
#     return {
#         "trade_id": t.get("tradeReference"),
#         "instrument_id": t.get("security", {}).get("securityCode"),
#         "instrument_type": t.get("security", {}).get("securityType"),
#         "trade_date": t.get("executionDate"),
#         "buyer": t.get("counterparties", {}).get("buyingFirm"),
#         "seller": t.get("counterparties", {}).get("sellingFirm"),
#         "quantity": t.get("tradeDetails", {}).get("units"),
#         "price": t.get("tradeDetails", {}).get("executionPrice"),
#         "trade_status": t.get("tradeDetails", {}).get("settlementStatus"),
# }

# def isNoneOrEmpty(value):
#     return value is None or value == ""

# def change_date_format(s):
#     if not s:
#         return None
#     s = s.strip()
#     if "." in s:                  
#         return s.replace(".", "-")
#     if "/" in s:                      
#         d, m, y = s.split("/")
#         return f"{y}-{m}-{d}"
#     parts = s.split("-")
#     if len(parts[0]) == 2:            
#         m, d, y = parts
#         return f"{y}-{m}-{d}"
#     return s                          


# def convertToFloat(value):
#     try:
#         return float(value)
#     except (ValueError, TypeError):
#         return None

# def convertToInt(value):
#     try:
#         return int(value)
#     except (ValueError, TypeError):
#         return None


# def isValid(json_data):
#     if isNoneOrEmpty(json_data["trade_id"]):
#         return False
#     if isNoneOrEmpty(json_data["instrument_id"]):
#         return False
#     if isNoneOrEmpty(json_data["instrument_type"]):
#         return False
#     if isNoneOrEmpty(json_data["trade_date"]):
#         return False
#     if isNoneOrEmpty(json_data["buyer"]):
#         return False
#     if isNoneOrEmpty(json_data["seller"]):
#         return False
#     if isNoneOrEmpty(json_data["quantity"]):
#         return False
#     if isNoneOrEmpty(json_data["price"]):
#         return False
#     if isNoneOrEmpty(json_data["trade_status"]):
#         return False
    
#     json_data["quantity"] = convertToInt(json_data["quantity"])
#     json_data["price"] = convertToFloat(json_data["price"])
    
#     if json_data["price"] < 0:
#         return False
    
#     return True


def main():

    #Imported the logging module to directly right error logs to.
    #Level is set to INFO because I want it to include errors starting from INFO 
    #However all error count logs are at the WARNING level
    logging.basicConfig(
    filename="errors.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    )

    #argparse takes arguments and flags and turns them into variables functions can use
    #Pyproject.toml essentially triggered the meridian.exe file that imports this module and calls main()
    #argParse then parses through flags or arguments and calls function(s) to proceed with the script
    parser = argparse.ArgumentParser(description="Clean and validate data from CSV or JSON files.")
    parser.add_argument("--validate", action="store_true", help="Validate the data and write clean output files.")
    args = parser.parse_args()

    #while validate is true--as in flag exists and was typed correctly
    if args.validate: 
        readCSV(csv_path)

        #logging.warning("Validation summary:")
        for error_type, n in error_counts.items():
           #logging.warning("  %s: %d", error_type, n)
           print(f"{error_type}: {n}")


if __name__ == "__main__":
    main()



import json
import csv
import argparse
import logging

from pathlib import Path

BASE_DIR = Path(__file__).parent

csv_path = BASE_DIR / "meridian_trades_small.csv"
json_path = BASE_DIR / "meridian_trades_small.json"
clean_data = BASE_DIR / "clean_data.csv"

FIELDNAMES = ["row_id", "trade_id", "instrument_id", "instrument_type",
              "trade_date", "buyer", "seller", "quantity", "price", "trade_status"]


def flatten(t):
    return {
        "trade_id": t.get("tradeReference"),
        "instrument_id": t.get("security", {}).get("securityCode"),
        "instrument_type": t.get("security", {}).get("securityType"),
        "trade_date": t.get("executionDate"),
        "buyer": t.get("counterparties", {}).get("buyingFirm"),
        "seller": t.get("counterparties", {}).get("sellingFirm"),
        "quantity": t.get("tradeDetails", {}).get("units"),
        "price": t.get("tradeDetails", {}).get("executionPrice"),
        "trade_status": t.get("tradeDetails", {}).get("settlementStatus"),
}

def isNoneOrEmpty(value):
    return value is None or value == ""

def change_date_format(date_str):
    if not date_str:
        return None
    elif '.' in date_str:
        date_str.replace('.', '-')
    elif date_str.count('-') == 2:
        a, b, c = date_str.split('-')
        if len(a) == 2:
            new_str = '-'.join([c, b, a])
            date_str = new_str
    elif '/' in date_str:
        a, b, c = date_str.split('/')
        if int(a) > 12:
            date_str = '-'.join([c, b, a])
      
        elif int(b) > 12:
            date_str = '-'.join([c, a, b])

    return date_str


def convertToFloat(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def convertToInt(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def isValid(json_data):
    if isNoneOrEmpty(json_data["trade_id"]):
        return False
    if isNoneOrEmpty(json_data["instrument_id"]):
        return False
    if isNoneOrEmpty(json_data["instrument_type"]):
        return False
    if isNoneOrEmpty(json_data["trade_date"]):
        return False
    if isNoneOrEmpty(json_data["buyer"]):
        return False
    if isNoneOrEmpty(json_data["seller"]):
        return False
    if isNoneOrEmpty(json_data["quantity"]):
        return False
    if isNoneOrEmpty(json_data["price"]):
        return False
    if isNoneOrEmpty(json_data["trade_status"]):
        return False
    
    json_data["quantity"] = convertToInt(json_data["quantity"])
    json_data["price"] = convertToFloat(json_data["price"])
    
    if json_data["price"] < 0:
        return False
    
    return True

def writeCleanData_json(json_path):
    with open(json_path, encoding="utf-8") as json_file, \
         open(clean_data, "a", newline="", encoding="utf-8") as clean_file:

        writer = csv.DictWriter(clean_file, fieldnames=FIELDNAMES)

        for row_num, line in enumerate(json_file, start=1):
            try:
                json_data = flatten(json.loads(line))
            except json.JSONDecodeError:
                logging.warning("Malformed JSON on line %d", row_num)
                continue

            if isValid(json_data):
                json_data["trade_date"] = change_date_format(json_data["trade_date"])
                json_data["row_id"] = f"json-{row_num}"
                writer.writerow(json_data)


def writeCleanData_csv(csv_path):
    with open(csv_path, newline= "") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
        
            if isValid(row):
                with open(clean_data, "a", encoding="utf-8") as clean_file:

                    row["trade_date"] = change_date_format(row["trade_date"])

                    writer = csv.DictWriter(clean_data, fieldnames=row.keys() + ["row_id"])
                    writer.writerow(row)
                    #increment row_id for each valid row
                    row["row_id"] = writer.writerow.__func__.__code__.co_argcount + 1


def main():

    logging.basicConfig(
    filename="errors.log",
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(message)s",
    )

    #argparse to handle command line arguments
    parser = argparse.ArgumentParser(description="Clean and validate data from CSV or JSON files.")
    parser.add_argument("--validate", action="store_true", help="Validate the data and write clean output files.")
    args = parser.parse_args()

    if args.validate: 
        writeCleanData_csv(csv_path)
        writeCleanData_json(csv_path)

if __name__ == "__main__":
    main()


import streamlit as st
import pandas as pd
import os
import datetime
import requests

# Constants
START_DATE = datetime.date(2020, 1, 1)
DATE_BITS = 16
UNIT_BITS = 16
SERIAL_NUM_BYTES = 4
INPUT_LEN = 10
MIN_YEAR = 2022

# Excel download links
file_links = {
    "DHR-03000_Rev_K.xlsx": "https://raw.githubusercontent.com/jainananya24/ConnectWorkOrdersSearch/main/DHR-03000%20Rev%20K%20Electronic%20DHR%20for%20Avive%20Connect%20Responses%20(15).xlsx",
    "DHR-03000_Rev_J.xlsx": "https://raw.githubusercontent.com/jainananya24/ConnectWorkOrdersSearch/main/DHR-03000%20Rev%20J%20Electronic%20DHR%20for%20Avive%20Connect%20Responses%20(24)%20(1).xlsx",
    "DHR-03000_Rev_H.xlsx": "https://raw.githubusercontent.com/jainananya24/ConnectWorkOrdersSearch/main/DHR-03000%20Rev%20H%20Electronic%20DHR%20for%20Avive%20Connect%20Responses%20(15)%20(1).xlsx",
    "DHR-03000_Rev_G.xlsx": "https://raw.githubusercontent.com/jainananya24/ConnectWorkOrdersSearch/main/DHR-03000%20Rev%20G%20Electronic%20DHR%20for%20Avive%20Connect%20Responses%20(10)%20(1).xlsx",

}

# Download Excel files
@st.cache_data
def download_excel_files():
    for file_name, url in file_links.items():
        if not os.path.exists(file_name):
            r = requests.get(url)
            with open(file_name, 'wb') as f:
                f.write(r.content)
    return list(file_links.keys())

# Convert serial number to hex
def int_to_hex(serial_num):
    if len(serial_num) != INPUT_LEN:
        raise ValueError("Input should be 10 digits.")

    year = 2000 + int(serial_num[:2])
    month = int(serial_num[2:4])
    day = int(serial_num[4:6])

    if year < MIN_YEAR:
        raise ValueError("Year must be >= 2022.")

    serial_date = datetime.date(year, month, day)
    day_diff = (serial_date - START_DATE).days
    unit_id = int(serial_num[6:])

    binary_str = f"{day_diff:016b}" + f"{unit_id:016b}"
    hex_value = hex(int(binary_str, 2)).upper()[2:].zfill(SERIAL_NUM_BYTES * 2)
    return hex_value

# Convert hex to serial number
def hex_to_int(hex_str):
    binary_str = f"{int(hex_str, 16):032b}"
    date_bits = binary_str[:DATE_BITS]
    unit_bits = binary_str[DATE_BITS:]

    day_diff = int(date_bits, 2)
    serial_date = START_DATE + datetime.timedelta(days=day_diff)
    serial_date_str = serial_date.strftime('%y%m%d')
    unit_id = str(int(unit_bits, 2)).zfill(4)

    return serial_date_str + unit_id

# Search Excel files for work order and operator name
def get_work_order_and_operator(serial_number, file_paths):
    results = {"Work Order": "Not available", "Operator": "Not available"}
    for file in file_paths:
        try:
            df = pd.read_excel(file)
            df.columns = df.columns.str.strip()

            if 'Serial Number' not in df.columns or "Operator's Full Name" not in df.columns or 'Work Order Number' not in df.columns:
                continue

            df['Serial Number'] = df['Serial Number'].astype(str).str.strip()
            match = df[df['Serial Number'] == serial_number]
            if not match.empty:
                results["Work Order"] = match['Work Order Number'].values[0]
                results["Operator"] = match["Operator's Full Name"].values[0]
                break
        except Exception as e:
            continue
    return results

# Detect input type and process
def process_input(user_input):
    if len(user_input) == 10 and user_input.isdigit():
        serial = user_input
        hex_val = int_to_hex(serial)
    else:
        hex_val = user_input
        serial = hex_to_int(hex_val)

    file_paths = download_excel_files()
    info = get_work_order_and_operator(serial, file_paths)

    if info["Work Order"] >= "W1243":
        pcba = "PCBA used is a Rev B* or C."
    else:
        pcba = "PCBA used is Rev B or A."

    return serial, hex_val, info["Work Order"], info["Operator"], pcba

# Streamlit app
st.title("Serial Number ↔ Hex Converter and Info Finder")
user_input = st.text_input("Enter Serial Number or Hexadecimal:")

if st.button("Convert and Search"):
    if not user_input:
        st.warning("Please enter a value.")
    else:
        try:
            serial, hex_val, work_order, operator, pcba = process_input(user_input.strip())
            st.success(f"Serial Number: {serial}")
            st.success(f"Hexadecimal: {hex_val}")
            st.info(f"Work Order Number: {work_order}")
            st.info(f"Operator's Full Name: {operator}")
            st.info(pcba)
        except Exception as e:
            st.error(f"Error: {e}")

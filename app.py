import streamlit as st
import pandas as pd
import datetime
import requests
import io

# Constants
START_DATE = datetime.date(2020, 1, 1)
DATE_BITS = 16
UNIT_BITS = 16
SERIAL_NUM_BYTES = 4
INPUT_LEN = 10
MIN_YEAR = 2022

# Excel file links on GitHub
file_links = {
    "DHR-03000_Rev_K.xlsx": "https://raw.githubusercontent.com/jainananya24/ConnectWorkOrdersSearch/main/DHR-03000%20Rev%20K%20Electronic%20DHR%20for%20Avive%20Connect%20Responses%20(15).xlsx",
    "DHR-03000_Rev_J.xlsx": "https://raw.githubusercontent.com/jainananya24/ConnectWorkOrdersSearch/main/DHR-03000%20Rev%20J%20Electronic%20DHR%20for%20Avive%20Connect%20Responses%20(24)%20(1).xlsx",
    "DHR-03000_Rev_H.xlsx": "https://raw.githubusercontent.com/jainananya24/ConnectWorkOrdersSearch/main/DHR-03000%20Rev%20H%20Electronic%20DHR%20for%20Avive%20Connect%20Responses%20(15)%20(1).xlsx",
    "DHR-03000_Rev_G.xlsx": "https://raw.githubusercontent.com/jainananya24/ConnectWorkOrdersSearch/main/DHR-03000%20Rev%20G%20Electronic%20DHR%20for%20Avive%20Connect%20Responses%20(10)%20(1).xlsx",
    "STM-03002_Rev_S.xlsx": "https://raw.githubusercontent.com/jainananya24/ConnectWorkOrdersSearch/main/STM-03002%20Rev%20S%20Electronic%20Data%20Collection%20Form%20%28Responses%29.xlsx",
    "STM-03002_Rev_R.xlsx": "https://raw.githubusercontent.com/jainananya24/ConnectWorkOrdersSearch/main/STM-03002%20Rev%20R%20Electronic%20Data%20Collection%20Form%20%28Responses%29.xlsx",
    "STM-03002_Rev_Q.xlsx": "https://raw.githubusercontent.com/jainananya24/ConnectWorkOrdersSearch/main/STM-03002%20Rev%20Q%20Electronic%20Data%20Collection%20Form%20%28Responses%29.xlsx",
    "STM-03002_Rev_P.xlsx": "https://raw.githubusercontent.com/jainananya24/ConnectWorkOrdersSearch/main/STM-03002%20Rev%20P%20Electronic%20Data%20Collection%20Form%20%28Responses%29.xlsx",
    "STM-03002_Rev_M.xlsx": "https://raw.githubusercontent.com/jainananya24/ConnectWorkOrdersSearch/main/STM-03002%20Rev%20M%20electronic%20data%20collection%20form%20Responses.xlsx",
    "STM-03002_Rev_L.xlsx": "https://raw.githubusercontent.com/jainananya24/ConnectWorkOrdersSearch/main/STM-03002%20Rev%20L%20%20electronic%20data%20collection%20form.xlsx",
    "STM-03002_Rev_K.xlsx": "https://raw.githubusercontent.com/jainananya24/ConnectWorkOrdersSearch/main/STM-03002%20Rev%20K%20%20electronic%20data%20collection%20form%20Responses.xlsx",
    "STM-03002_Rev_J.xlsx": "https://raw.githubusercontent.com/jainananya24/ConnectWorkOrdersSearch/main/STM-03002%20Rev%20J%20electronic%20data%20collection%20form%20Responses.xlsx",
}

# Download and load Excel files into memory
@st.cache_data
def download_excel_files():
    dataframes = []
    for file_name, url in file_links.items():
        try:
            r = requests.get(url)
            r.raise_for_status()
            df = pd.read_excel(io.BytesIO(r.content), engine="openpyxl", header=None)
            
            # Find the header row dynamically
            header_idx = 0
            for i, row in df.iterrows():
                row_list = [str(x).strip().lower() for x in row.tolist()]
                if any('serial' in str(x) for x in row_list):
                    header_idx = i
                    break
            
            # Set the header and slice the dataframe
            df.columns = df.iloc[header_idx]
            df = df.iloc[header_idx + 1:].reset_index(drop=True)
            df.columns = df.columns.astype(str).str.strip()
            
            # Align "Operator's Name" to "Operator's Full Name" if necessary
            if "Operator's Name" in df.columns and "Operator's Full Name" not in df.columns:
                df.rename(columns={"Operator's Name": "Operator's Full Name"}, inplace=True)
                
            df["Source File"] = file_name
            dataframes.append(df)
        except Exception as e:
            st.warning(f"Could not read {file_name}: {e}")
    return dataframes

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

# Search work order and operator
def get_work_order_and_operator(serial_number, dataframes):
    work_orders = []
    operators = []
    for df in dataframes:
        if 'Serial Number' not in df.columns or "Operator's Full Name" not in df.columns or 'Work Order Number' not in df.columns:
            continue
        # Handle decimal (.0) that may come from floating point values in excel
        df['Serial Number'] = df['Serial Number'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        match = df[df['Serial Number'] == serial_number]
        
        for _, row in match.iterrows():
            wo = str(row['Work Order Number']).strip()
            op = str(row["Operator's Full Name"]).strip()
            if wo != 'nan' and wo not in work_orders:
                work_orders.append(wo)
            if op != 'nan' and op not in operators:
                operators.append(op)
                
    results = {
        "Work Order": ", ".join(work_orders) if work_orders else "Not available",
        "Operator": ", ".join(operators) if operators else "Not available"
    }
    return results

# Determine PCBA revision from work order
def get_pcba_revision(work_order_str):
    if work_order_str == "Not available":
        return "PCBA revision not available."
    
    work_orders = [wo.strip() for wo in work_order_str.split(",")]
    revisions = []
    for wo in work_orders:
        if wo >= "W1243":
            revisions.append(f"{wo}: PCBA used is a Rev B* or C.")
        else:
            revisions.append(f"{wo}: PCBA used is Rev B or A.")
            
    # deduplicate and formatting
    if len(revisions) == 1:
        return revisions[0].split(": ")[1]  # Return just the revision if only 1 work order
    
    return " | ".join(revisions)

# Process user input
def process_input(user_input):
    if len(user_input) == 10 and user_input.isdigit():
        serial = user_input
        hex_val = int_to_hex(serial)
    else:
        hex_val = user_input
        serial = hex_to_int(hex_val)
    dataframes = download_excel_files()
    info = get_work_order_and_operator(serial, dataframes)
    pcba = get_pcba_revision(info["Work Order"])
    return serial, hex_val, info["Work Order"], info["Operator"], pcba

# --- Streamlit App ---
st.title("🔎 Serial Number ↔ Hex Converter & Info Finder")
st.text("Only works for Connects Build at Avive")

user_input = st.text_input("Enter Serial Number (10 digits) or Hexadecimal (8 chars):")

if st.button("Convert and Search"):
    if not user_input:
        st.warning("Please enter a serial number or hex string.")
    else:
        try:
            serial, hex_val, work_order, operator, pcba = process_input(user_input.strip())
            st.success(f"**Serial Number:** {serial}")
            st.success(f"**Hexadecimal:** {hex_val}")
            st.info(f"**Work Order Number:** {work_order}")
            st.info(f"**Operator's Full Name:** {operator}")
            st.info(f"**{pcba}**")
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown("---")
# --- App Description and Instructions ---
with st.expander("ℹ️ About this App & How to Use"):
    st.markdown("""
        **What does this app do?**
        
        This tool is designed for Avive Connect devices to perform three key functions:
        - **Convert IDs:** It can convert a 10-digit serial number to its 8-character hex value, and vice-versa.
        - **Find Manufacturing Data:** It searches through Device History Records (DHRs) to find the Work Order and Operator name associated with a serial number.
        - **Check PCBA Revision:** It automatically determines the likely PCBA revision based on the work order.
    """)
    st.markdown("""
        **How to use it:**
        
        1.  Enter a valid 10-digit serial number (e.g., `2301150001`) or an 8-character hexadecimal string into the input box.
        2.  Click the **"Convert and Search"** button.
        3.  The results, including the converted value and any found manufacturing information, will be displayed.
    """)

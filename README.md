# Serial Number ↔ Hex Converter & Info Finder
This Streamlit web application is a specialized tool designed for Avive Connect devices. It provides a simple interface to perform two primary functions:
>
- Bidirectional Conversion: Convert a 10-digit device serial number into its corresponding 8-character hexadecimal representation, and vice-versa.
- Manufacturing Data Lookup: Fetch key manufacturing details, including the Work Order Number and Operator Name, by searching for the serial number across a set of historical Device History Record (DHR) Excel files.
- PCBA Revision Check: Automatically determine the likely Printed Circuit Board Assembly (PCBA) revision based on the retrieved Work Order number.

# ⚙️ How It Works
Input Detection: The app first checks the user's input. If it's a 10-digit number, it proceeds with the int_to_hex logic. If it's an 8-character string, it assumes it's a hex value and uses the hex_to_int logic.
>
Conversion Logic:
Serial to Hex: The 10-digit serial (YYMMDDXXXX) is broken down. The date is used to calculate the number of days that have passed since a fixed START_DATE (Jan 1, 2020). This day count and the final four digits (XXXX) are converted into a 32-bit binary number, which is then represented as an 8-character hex string.
>
Hex to Serial: The process is reversed. The hex is converted to a 32-bit binary string, which is then split to extract the day difference and the unit ID, reconstructing the original serial number.
>
Data Loading & Caching: On the first search, the download_excel_files function is called. It iterates through a dictionary of GitHub URLs, downloads each Excel file, and loads it into a pandas DataFrame. The @st.cache_data decorator ensures this function only runs once, storing the DataFrames in memory for the entire session.
>
Information Search: The app iterates through the cached DataFrames, searching for a row where the Serial Number column matches the converted serial number. If a match is found, it extracts the Work Order Number and Operator's Full Name.
>
PCBA Revision: A final check is performed on the Work Order Number. If it is numerically greater than or equal to "W1243", it's determined to be a newer revision PCBA.
>
# ▶️ How to Use the App
Enter a valid 10-digit serial number (e.g., 2301150001) or an 8-character hexadecimal string into the input box.
>
- Click the "Convert and Search" button.
>
- The results, including the converted value and any found manufacturing information, will be displayed below the button.

# ✍️ Author
This script was created by Ananya Jain

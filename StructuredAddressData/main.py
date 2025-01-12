import streamlit as st
import sqlite3
import pandas as pd
import os
import logging
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create directories for file input/output
os.makedirs('data/input', exist_ok=True)
os.makedirs('data/output', exist_ok=True)

# Column mapping for output CSV
ADDRESS_COLUMNS = [
    'BuildingNumber',
    'StreetName',
    'TownName',
    'CountrySubDivision',
    'Country',
    'PostCode '
]

# Database setup to store company data
def init_db():
    conn = sqlite3.connect('company_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS company_data
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT, address_line1 TEXT,
                    address_line2 TEXT, address_line3 TEXT,
                    city TEXT, state TEXT, country TEXT,
                    postal_code TEXT, processed INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def save_to_db(data):
    conn = sqlite3.connect('company_data.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO company_data 
                      (company_name, address_line1, address_line2, address_line3, 
                       city, state, country, postal_code)
                      VALUES (?,?,?,?,?,?,?,?)''', tuple(data.values()))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id

def save_to_csv(data, record_id):
    # Map the input data to the required output format
    output_data = {
        'Entity.LegalAddress.FirstAddressLine': data['address_line1'],
        'Entity.LegalAddress.AdditionalAddressLine.1': data['address_line2'],
        'Entity.LegalAddress.AdditionalAddressLine.2': data['address_line3'],
        'Entity.LegalAddress.AdditionalAddressLine.3': '',  # Empty as per requirements
        'Entity.LegalAddress.City': data['city'],
        'Entity.LegalAddress.Region': data['state'],
        'Entity.LegalAddress.Country': data['country'],
        'Entity.LegalAddress.PostalCode': data['postal_code']
    }
    
    input_df = pd.DataFrame([output_data])
    input_file = f'data/input/{record_id}.csv'
    input_df.to_csv(input_file, index=False)
    logger.info(f"Input data saved to {input_file}")
    return input_file

def run_processing_pipeline(input_file):
    try:
        # Run parser.py
        logger.info("Starting parser.py")
        subprocess.run(['python', 'parser.py', input_file], check=True)
        
        # Run engine.py
        logger.info("Starting engine.py")
        subprocess.run(['python', 'engine.py', input_file], check=True)
        
        logger.info("Processing pipeline completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error in processing pipeline: {str(e)}")
        return False

def main():
    st.title("Company Information Form")
    st.sidebar.title("Input Details")
    
    with st.form("company_form"):
        company_name = st.text_input("Company Name")
        address_line1 = st.text_input("Address Line 1")
        address_line2 = st.text_input("Address Line 2")
        address_line3 = st.text_input("Address Line 3")
        city = st.text_input("City")
        state = st.text_input("State")
        country = st.text_input("Country")
        postal_code = st.text_input("Postal Code")
        
        submit = st.form_submit_button("Submit")
    
    if submit and company_name and address_line1 and city and state and country and postal_code:
        data = {
            'company_name': company_name,
            'address_line1': address_line1,
            'address_line2': address_line2,
            'address_line3': address_line3,
            'city': city,
            'state': state,
            'country': country,
            'postal_code': postal_code
        }
        
        # Save to database
        record_id = save_to_db(data)
        st.success(f"Data saved to database with ID: {record_id}")
        
        # Save to CSV with the required column format
        input_file = save_to_csv(data, record_id)
        st.success(f"CSV file created: {input_file}")
        
        # Run the processing pipeline
        if run_processing_pipeline(input_file):
            st.success("Processing pipeline completed successfully")
        else:
            st.error("Error occurred during processing")
        
        # Show the saved data in a table format
        st.write("**Unstructured Data Submitted:**")
        st.table(pd.DataFrame([data]))
        
        # Show the structured data in a table format
        output_data = {
            'BuildingNo': data['address_line1'],
            'StreetName': data['address_line2'],
            'TownName': data['address_line3'],
            'CountrySubDivision': data['state'],
            'Country': data['country'],
            'PostalCode': data['postal_code']
        }
        st.write("**Structured Data:**")
        st.table(pd.DataFrame([output_data]))

if __name__ == "__main__":
    init_db()
    main()

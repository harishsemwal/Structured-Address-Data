import streamlit as st
import sqlite3
import pandas as pd
import os
import matplotlib.pyplot as plt

# Database file
DB_FILE = "company_data.db"  # Use the same database for DB_FILE_1 and DB_FILE_2 for comparison

# Function to create tables if they don't exist
def create_table():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS company_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            address_line1 TEXT,
            address_line2 TEXT,
            address_line3 TEXT,
            state TEXT,
            country TEXT,
            postal_code TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Call create_table to ensure the table is created on startup
create_table()

# Function to insert data into the database
def insert_data(company_name, address_line1, address_line2, address_line3, state, country, postal_code):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO company_data (company_name, address_line1, address_line2, address_line3, state, country, postal_code)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (company_name, address_line1, address_line2, address_line3, state, country, postal_code))
    conn.commit()
    conn.close()
    st.write("Data inserted successfully!")

# Function to fetch data from the database
def fetch_data():
    conn = sqlite3.connect(DB_FILE)
    query = 'SELECT * FROM company_data'
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Function to save data to CSV
def save_to_csv(dataframe, file_path):
    dataframe.to_csv(file_path, index=False)
    st.write(f"CSV saved at {file_path}")

# UI Setup
st.set_page_config(page_title="Company Info Form", layout="centered")
st.title("Company Information Form")
st.markdown("Please fill out the details below:")

# Form for input
with st.form("company_form", clear_on_submit=True):
    company_name = st.text_input("Company Name", placeholder="Enter the company name")
    address_line1 = st.text_input("Address Line 1", placeholder="Enter the first line of address")
    address_line2 = st.text_input("Address Line 2", placeholder="Enter the second line of address (optional)")
    address_line3 = st.text_input("Address Line 3", placeholder="Enter the third line of address (optional)")
    state = st.text_input("State", placeholder="Enter the state")
    country = st.text_input("Country", placeholder="Enter the country")
    postal_code = st.text_input("Postal Code", placeholder="Enter the postal code")

    submit_button = st.form_submit_button("Submit")

# Display the submitted data immediately
if submit_button:
    if company_name and address_line1 and state and country and postal_code:
        insert_data(company_name, address_line1, address_line2, address_line3, state, country, postal_code)
        st.success("Company information saved successfully!")

        # Display the submitted data in an attractive key-value format
        st.subheader("Submitted Data:")
        st.markdown(
            f"""
            <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; background-color: #f9f9f9;">
                <strong>Company Name:</strong> {company_name}<br>
                <strong>Address Line 1:</strong> {address_line1}<br>
                <strong>Address Line 2:</strong> {address_line2}<br>
                <strong>Address Line 3:</strong> {address_line3}<br>
                <strong>State:</strong> {state}<br>
                <strong>Country:</strong> {country}<br>
                <strong>Postal Code:</strong> {postal_code}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.error("Please fill in all the required fields.")

# Button to display history and save it to CSV
if st.button("Show History"):
    st.header("Saved Data from Database")
    data = fetch_data()
    if not data.empty:
        # Save data to CSV instantly
        save_to_csv(data, "company_info_history.csv")

        # Display data and download option
        st.dataframe(data, use_container_width=True)
        with open("company_info_history.csv", "rb") as file:
            st.download_button(
                label="Download Data as CSV",
                data=file,
                file_name="company_info_history.csv",
                mime="text/csv",
            )
    else:
        st.info("No records available. Please submit the form to add data.")

# Second page to compare the data
if st.button("Compare Data"):
    st.header("Data Comparison")

    # Input to search by company ID or Name
    search_term = st.text_input("Enter Company Name or ID to Compare:")
    if search_term:
        # Fetch data from the database
        data = fetch_data()

        # Filter based on search term (company name or ID)
        filtered_data = data[data['company_name'].str.contains(search_term, case=False, na=False)]
        if not filtered_data.empty:
            # Display results
            st.subheader(f"Comparison Results for {search_term}:")
            st.dataframe(filtered_data)

            # Pie chart showing the comparison (accuracy)
            matched_rows = filtered_data[filtered_data.notnull().all(axis=1)]
            accuracy = (len(matched_rows) / len(filtered_data)) * 100 if len(filtered_data) > 0 else 0
            pie_data = [accuracy, 100 - accuracy]
            labels = ['Matches', 'Changes']

            fig, ax = plt.subplots()
            ax.pie(pie_data, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
            st.pyplot(fig)
        else:
            st.warning(f"No data found for {search_term}")

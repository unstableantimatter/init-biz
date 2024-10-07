import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
import matplotlib.pyplot as plt

# Initialize or connect to the SQLite database
def get_connection(db_path="business_expenses.db"):
    return sqlite3.connect(db_path)

# Function to create the expenses table if it doesn't exist
def initialize_db(conn):
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        category TEXT,
        description TEXT,
        amount REAL,
        notes TEXT
    )
    ''')
    conn.commit()

# Function to add an expense to the database
def add_expense(conn, date, category, description, amount, notes):
    c = conn.cursor()
    c.execute('''
    INSERT INTO expenses (date, category, description, amount, notes)
    VALUES (?, ?, ?, ?, ?)
    ''', (date, category, description, amount, notes))
    conn.commit()

# Function to fetch all expenses from the database
def fetch_expenses(conn):
    c = conn.cursor()
    c.execute('SELECT date, category, description, amount, notes FROM expenses')
    data = c.fetchall()
    return pd.DataFrame(data, columns=["Date", "Expense Category", "Expense Description", "Amount", "Notes"])

# Step Navigation
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'db_path' not in st.session_state:
    st.session_state.db_path = "business_expenses.db"

# Step indicator with navigation buttons
steps = ["Enter Business Details", "Add Expenses", "View Dashboard"]

# Function to handle navigation
def change_step(increment):
    st.session_state.step = min(max(st.session_state.step + increment, 0), len(steps) - 1)

# Step Navigation Buttons
if st.session_state.step > 0:
    st.button("Back", on_click=change_step, args=[-1])
if st.session_state.step < len(steps) - 1:
    st.button("Next", on_click=change_step, args=[1])

# Step 1: Enter Business Details
if st.session_state.step == 0:
    st.title("Business Tax Calculation App")
    st.subheader("Step 1: Enter Business Details")
    
    # Database Selection
    st.write("Load an existing database or continue with a new one.")
    uploaded_file = st.file_uploader("Choose an existing SQLite database", type="db")
    if uploaded_file is not None:
        st.session_state.db_path = os.path.join(os.getcwd(), uploaded_file.name)
        with open(st.session_state.db_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"Loaded database: {uploaded_file.name}")

    # Initialize database
    conn = get_connection(st.session_state.db_path)
    initialize_db(conn)
    
    # Business Details Input with session state storage
    st.session_state.business_name = st.text_input("Business Name", value=st.session_state.get("business_name", ""))
    st.session_state.tax_year = st.number_input("Tax Year", min_value=2000, max_value=2100, value=st.session_state.get("tax_year", datetime.now().year))
    st.session_state.jurisdiction = st.selectbox("Jurisdiction", ["Delaware", "Other"])

# Step 2: Add Expenses
elif st.session_state.step == 1:
    st.title("Add Expenses")
    st.subheader("Step 2: Enter Expense Details")
    
    # Expense Entry Form
    category = st.selectbox("Select Expense Category", ["Salaries", "Contractors", "Travel", "Networking", "Other"])
    date = st.date_input("Expense Date")
    description = st.text_input("Description")
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    notes = st.text_area("Notes")
    
    if st.button("Add Expense"):
        conn = get_connection(st.session_state.db_path)
        add_expense(conn, date, category, description, amount, notes)
        conn.close()
        st.success("Expense added successfully!")

# Step 3: View Dashboard
elif st.session_state.step == 2:
    # Ensure that business_name and tax_year are available
    if not st.session_state.get("business_name") or not st.session_state.get("tax_year"):
        st.warning("Please enter your business details first.")
        st.button("Go Back", on_click=change_step, args=[-1])
    else:
        # Access business_name and tax_year from session state
        business_name = st.session_state.business_name
        tax_year = st.session_state.tax_year

        st.title(f"{business_name} - {tax_year} Tax Year Dashboard")
        st.subheader("Cumulative Profit & Loss Summary")
        
        # Fetch data from the database for the dashboard
        conn = get_connection(st.session_state.db_path)
        expenses_df = fetch_expenses(conn)
        conn.close()
        
        total_expenses = expenses_df['Amount'].sum()
        st.write(f"Total Expenses: ${total_expenses:.2f}")
        
        # Visualization
        st.subheader("Expense Breakdown by Category")
        fig, ax = plt.subplots()
        expense_summary = expenses_df.groupby("Expense Category").sum()["Amount"]
        ax.pie(expense_summary, labels=expense_summary.index, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        st.pyplot(fig)
        
        # Display expenses data and export option
        st.subheader("Expense Data")
        st.dataframe(expenses_df)
        
        csv = expenses_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name=f"{business_name}_expenses_{tax_year}.csv",
            mime="text/csv"
        )

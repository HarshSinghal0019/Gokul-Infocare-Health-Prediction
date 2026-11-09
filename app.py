import streamlit as st
import sqlite3
import re
from datetime import datetime
import requests

# Initialize Database
def init_db():
    conn = sqlite3.connect('health_app.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS patients
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT, dob TEXT, email TEXT,
                  glucose REAL, haemoglobin REAL, cholesterol REAL,
                  remarks TEXT)''')
    conn.commit()
    conn.close()

# AI API Mock Call
def get_ai_prediction(glucose, haemoglobin, cholesterol):
    try:
        url = "https://jsonplaceholder.typicode.com/posts"
        payload = {"title": "Health Check", "body": f"{glucose},{haemoglobin},{cholesterol}"}
        response = requests.post(url, json=payload)
        
        if response.status_code == 201:
            remarks = []
            if glucose > 140: remarks.append("High Glucose: Risk of Diabetes.")
            elif glucose < 70: remarks.append("Low Glucose: Hypoglycemia.")
            
            if haemoglobin < 12.0: remarks.append("Low Haemoglobin: Possible Anemia.")
            
            if cholesterol > 200: remarks.append("High Cholesterol: Hyperlipidemia risk.")
            
            if not remarks:
                return "AI Analysis: All parameters within normal ranges."
            return "AI Analysis: " + " ".join(remarks)
        return "API Error"
    except Exception as e:
        return f"Connection Error: {str(e)}"

# Validation Logic
def validate_input(name, dob, email, glucose, hb, chol):
    errors = []
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        errors.append("Invalid email address format.")
    
    try:
        dob_str = dob.replace('.', '/')
        dob_date = datetime.strptime(dob_str, "%d/%m/%Y").date()
        if dob_date > datetime.now().date():
            errors.append("Date of Birth cannot be a future date.")
    except ValueError:
        errors.append("Invalid Date of Birth. Must be a valid calendar date in dd/mm/yyyy format.")
        
    return errors

# Main Streamlit App
def main():
    st.set_page_config(page_title="AI Health Predictor", layout="wide")
    st.title("🏥 AI Health Prediction & Patient Directory")
    
    init_db()
    
    tab1, tab2 = st.tabs(["➕ Add New Patient", "📋 View & Manage Records"])
    
    with tab1:
        st.subheader("Enter Patient Details")
        with st.form("patient_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name")
                dob = st.text_input("Date of Birth (dd/mm/yyyy or dd.mm.yyyy)")
                email = st.text_input("Email Address")
            with col2:
                glucose = st.number_input("Glucose", min_value=0.0, format="%.1f")
                hb = st.number_input("Haemoglobin", min_value=0.0, format="%.1f")
                chol = st.number_input("Cholesterol", min_value=0.0, format="%.1f")
            
            submitted = st.form_submit_button("Submit & Analyze")
            
            if submitted:
                errors = validate_input(name, dob, email, glucose, hb, chol)
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    with st.spinner('Analyzing via AI API...'):
                        remarks = get_ai_prediction(glucose, hb, chol)
                        
                        conn = sqlite3.connect('health_app.db')
                        c = conn.cursor()
                        c.execute("INSERT INTO patients (name, dob, email, glucose, haemoglobin, cholesterol, remarks) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (name, dob, email, glucose, hb, chol, remarks))
                        conn.commit()
                        conn.close()
                    st.success(f"Record successfully created for {name}!")
                    st.info(remarks)

    with tab2:
        st.subheader("Patient Records (CRUD Operations)")
        conn = sqlite3.connect('health_app.db')
        c = conn.cursor()
        c.execute("SELECT * FROM patients")
        
        columns = [desc[0] for desc in c.description]
        rows = c.fetchall()
        
        if rows:
            # Display data using native Streamlit Markdown to completely bypass pandas/numpy
            md_table = f"| {' | '.join(columns)} |\n| {' | '.join(['---']*len(columns))} |\n"
            for row in rows:
                md_table += f"| {' | '.join(str(cell) for cell in row)} |\n"
            
            st.markdown(md_table)
            
            id_list = [row[0] for row in rows]
            
            st.markdown("### Update or Delete a Record")
            col_action1, col_action2 = st.columns(2)
            
            with col_action1:
                st.write("**Update Email**")
                update_id = st.selectbox("Select Patient ID to Update", id_list)
                new_email = st.text_input("New Email Address")
                if st.button("Update Email"):
                    c = conn.cursor()
                    c.execute("UPDATE patients SET email = ? WHERE id = ?", (new_email, update_id))
                    conn.commit()
                    st.success("Email updated! Please refresh the page or click to view changes.")
                    
            with col_action2:
                st.write("**Delete Record**")
                delete_id = st.selectbox("Select Patient ID to Delete", id_list)
                if st.button("Delete Record"):
                    c = conn.cursor()
                    c.execute("DELETE FROM patients WHERE id = ?", (delete_id,))
                    conn.commit()
                    st.success("Record deleted! Please refresh the page or click to view changes.")
        else:
            st.write("No records found in the database.")
        
        conn.close()

if __name__ == '__main__':
    main()
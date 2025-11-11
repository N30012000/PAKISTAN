"""
PIA Operations - Complete Professional System with Supabase
ALL FEATURES INCLUDED
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import hashlib
import secrets
import os
import json
import time

PRIMARY_COLOR = "#006C35"
ACCENT_COLOR = "#C8102E"

SUPABASE_URL = os.getenv("SUPABASE_URL", st.secrets.get("SUPABASE_URL", ""))
SUPABASE_KEY = os.getenv("SUPABASE_KEY", st.secrets.get("SUPABASE_KEY", ""))

@st.cache_resource
def init_supabase():
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase.table('users').select("id").limit(1).execute()
        return supabase
    except:
        return None

supabase = init_supabase()

def init_session():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None

def login_user(username: str, password: str):
    if not supabase:
        return False, "Database unavailable"
    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        response = supabase.table('users').select("*").eq('username', username).eq('password_hash', password_hash).execute()
        if response.data:
            user = response.data[0]
            st.session_state.authenticated = True
            st.session_state.current_user = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role']
            }
            return True, "Success!"
        return False, "Invalid credentials"
    except:
        return False, "Error"

def signup_user(username, email, password, full_name):
    if not supabase or len(username) < 3 or len(password) < 6:
        return False, "Invalid input"
    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        supabase.table('users').insert({
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'full_name': full_name,
            'role': 'user'
        }).execute()
        return True, "Account created!"
    except:
        return False, "Username/email exists"

def logout():
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.rerun()

def get_data(table, limit=1000):
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table(table).select("*").limit(limit).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except:
        return pd.DataFrame()

def insert_data(table, data):
    if not supabase:
        return False
    try:
        if st.session_state.current_user:
            data['created_by'] = st.session_state.current_user['username']
        supabase.table(table).insert(data).execute()
        return True
    except:
        return False

def bulk_insert(table, records):
    if not supabase:
        return 0
    count = 0
    for record in records:
        if insert_data(table, record):
            count += 1
    return count

def generate_demo_data():
    if not supabase:
        return
    response = supabase.table('maintenance').select("id").limit(1).execute()
    if response.data:
        return
    
    import random
    aircraft = [f"AP-BH{chr(65+i)}" for i in range(10)]
    
    # Maintenance
    records = []
    for i in range(50):
        records.append({
            'aircraft_registration': random.choice(aircraft),
            'maintenance_type': random.choice(["A-Check", "B-Check", "C-Check", "Engine Overhaul"]),
            'scheduled_date': (datetime.now() - timedelta(days=random.randint(0, 180))).strftime('%Y-%m-%d'),
            'technician_name': f"Tech-{random.randint(100, 999)}",
            'hours_spent': round(random.uniform(2, 120), 1),
            'cost': round(random.uniform(5000, 500000), 2),
            'status': random.choice(["Scheduled", "In Progress", "Completed"]),
            'priority': random.choice(['Low', 'Medium', 'High', 'Critical']),
            'description': f"Maintenance {i+1}",
            'created_by': 'system'
        })
    supabase.table('maintenance').insert(records).execute()
    
    # Incidents
    records = []
    for i in range(30):
        records.append({
            'incident_date': (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d'),
            'incident_type': random.choice(["Bird Strike", "Hard Landing", "Engine Issue"]),
            'severity': random.choice(["Minor", "Moderate", "Major", "Critical"]),
            'aircraft_registration': random.choice(aircraft),
            'flight_number': f"PK{random.randint(100, 999)}",
            'location': random.choice(['Karachi', 'Lahore', 'Islamabad']),
            'description': f"Incident {i+1}",
            'investigation_status': random.choice(['Open', 'Closed']),
            'created_by': 'system'
        })
    supabase.table('safety_incidents').insert(records).execute()
    
    # Flights
    records = []
    for i in range(100):
        dep = datetime.now() + timedelta(days=random.randint(-30, 30))
        arr = dep + timedelta(hours=random.randint(2, 12))
        records.append({
            'flight_number': f"PK{random.randint(100, 999)}",
            'aircraft_registration': random.choice(aircraft),
            'departure_airport': random.choice(["KHI", "LHE", "ISB", "DXB", "LHR"]),
            'arrival_airport': random.choice(["KHI", "LHE", "ISB", "DXB", "LHR"]),
            'scheduled_departure': dep.isoformat(),
            'scheduled_arrival': arr.isoformat(),
            'passengers_count': random.randint(50, 350),
            'flight_status': random.choice(["Scheduled", "On Time", "Delayed", "Arrived"]),
            'created_by': 'system'
        })
    supabase.table('flights').insert(records).execute()

def apply_css():
    st.markdown(f"""
        <style>
        .stButton>button {{width: 100%; background-color: {PRIMARY_COLOR}; color: white;}}
        .dashboard-header {{
            background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, #004d26 100%);
            padding: 2rem; border-radius: 10px; color: white; margin-bottom: 2rem;
        }}
        </style>
    """, unsafe_allow_html=True)

def show_auth():
    st.markdown('<div style="text-align:center;font-size:4rem;">✈️</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;color:{PRIMARY_COLOR};font-size:2.5rem;font-weight:700;">PIA Operations</div>', unsafe_allow_html=True)
    
    if not supabase:
        st.error("⚠️ Supabase not connected. Check secrets.")
        st.stop()
    
    tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Sign Up", "🔑 Reset"])
    
    with tab1:
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                success, msg = login_user(username, password)
                if success:
                    st.success(msg)
                    time.sleep(0.3)
                    st.rerun()
                else:
                    st.error(msg)
    
    with tab2:
        with st.form("signup"):
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            username = st.text_input("Username (3+ chars)")
            password = st.text_input("Password (6+ chars)", type="password")
            password2 = st.text_input("Confirm", type="password")
            if st.form_submit_button("Sign Up"):
                if password != password2:
                    st.error("Passwords don't match")
                else:
                    success, msg = signup_user(username, email, password, name)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
    
    with tab3:
        st.info("Password reset - contact admin")

def page_dashboard():
    st.markdown('<div class="dashboard-header"><h1>✈️ PIA Operations Dashboard</h1><p>Real-time airline operations</p></div>', unsafe_allow_html=True)
    
    maint = get_data('maintenance')
    incidents = get_data('safety_incidents')
    flights = get_data('flights')
    
    if maint.empty:
        if st.button("📊 Generate Demo Data"):
            with st.spinner("Generating..."):
                generate_demo_data()
                st.success("Done!")
                st.rerun()
        return
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Maintenance", len(maint))
    with col2:
        critical = len(incidents[incidents['severity'].isin(['Major', 'Critical'])]) if not incidents.empty else 0
        st.metric("Incidents", len(incidents), f"{critical} critical")
    with col3:
        st.metric("Flights", len(flights))
    with col4:
        hours = maint['hours_spent'].sum() if not maint.empty else 0
        st.metric("Hours", f"{hours:,.0f}")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if not maint.empty:
            st.subheader("Maintenance by Type")
            counts = maint.groupby('maintenance_type').size().reset_index(name='count')
            fig = px.bar(counts, x='maintenance_type', y='count', color_discrete_sequence=[PRIMARY_COLOR])
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if not incidents.empty:
            st.subheader("Incidents by Severity")
            counts = incidents.groupby('severity').size().reset_index(name='count')
            fig = px.pie(counts, names='severity', values='count')
            st.plotly_chart(fig, use_container_width=True)

def page_forms():
    st.header("📝 Forms & Submit")
    
    tab1, tab2, tab3 = st.tabs(["✈️ Maintenance", "⚠️ Safety Incident", "🛫 Flight"])
    
    with tab1:
        with st.form("maint_form"):
            st.subheader("Add Maintenance")
            col1, col2 = st.columns(2)
            with col1:
                aircraft = st.text_input("Aircraft*", placeholder="AP-BHA")
                mtype = st.selectbox("Type*", ["A-Check", "B-Check", "C-Check", "Engine Overhaul"])
                date = st.date_input("Date*")
                tech = st.text_input("Technician")
            with col2:
                hours = st.number_input("Hours", min_value=0.0)
                cost = st.number_input("Cost", min_value=0.0)
                status = st.selectbox("Status", ["Scheduled", "In Progress", "Completed"])
                priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
            desc = st.text_area("Description")
            
            if st.form_submit_button("Add"):
                if aircraft and mtype:
                    if insert_data('maintenance', {
                        'aircraft_registration': aircraft,
                        'maintenance_type': mtype,
                        'scheduled_date': date.strftime('%Y-%m-%d'),
                        'technician_name': tech,
                        'hours_spent': hours,
                        'cost': cost,
                        'status': status,
                        'priority': priority,
                        'description': desc
                    }):
                        st.success("✅ Added!")
                        st.balloons()

def page_csv_upload():
    st.header("📤 CSV Upload")
    
    table = st.selectbox("Target Table", ["maintenance", "safety_incidents", "flights"])
    
    uploaded = st.file_uploader("Upload CSV", type=['csv'])
    
    if uploaded:
        df = pd.read_csv(uploaded)
        st.success(f"Loaded {len(df)} rows")
        st.dataframe(df.head())
        
        if st.button("Import All"):
            records = df.to_dict('records')
            count = bulk_insert(table, records)
            st.success(f"Imported {count} records!")

def page_data():
    st.header("🗂️ Data Management")
    
    table = st.selectbox("Table", ["Maintenance", "Safety Incidents", "Flights"])
    table_map = {"Maintenance": "maintenance", "Safety Incidents": "safety_incidents", "Flights": "flights"}
    
    df = get_data(table_map[table])
    
    if not df.empty:
        st.dataframe(df, use_container_width=True, height=400)
        csv = df.to_csv(index=False).encode()
        st.download_button("📥 Download", csv, f"{table_map[table]}.csv")
    else:
        st.info("No data")

def page_nl_query():
    st.header("💬 NL/AI Query")
    
    query = st.text_input("Ask a question", placeholder="total maintenance hours")
    
    if st.button("Search"):
        if "total maintenance hours" in query.lower():
            df = get_data('maintenance')
            if not df.empty:
                total = df['hours_spent'].sum()
                st.success(f"Total maintenance hours: {total:,.1f}")
                st.dataframe(df[['aircraft_registration', 'maintenance_type', 'hours_spent']])
        elif "emergency" in query.lower() or "critical" in query.lower():
            df = get_data('safety_incidents')
            critical = df[df['severity'].isin(['Major', 'Critical'])] if not df.empty else pd.DataFrame()
            st.success(f"Found {len(critical)} critical incidents")
            st.dataframe(critical)
        else:
            st.info("Try: 'total maintenance hours' or 'show emergency incidents'")

def page_reports():
    st.header("📊 Reports")
    
    col1, col2 = st.columns(2)
    with col1:
        report_type = st.selectbox("Type", ["Maintenance Summary", "Safety Report", "Flight Operations"])
    with col2:
        period = st.selectbox("Period", ["Weekly", "Monthly", "Quarterly", "Annual"])
    
    if st.button("Generate Report"):
        if "Maintenance" in report_type:
            df = get_data('maintenance')
            if not df.empty:
                st.subheader("Maintenance Summary")
                st.metric("Total Tasks", len(df))
                st.metric("Total Hours", f"{df['hours_spent'].sum():,.0f}")
                st.metric("Total Cost", f"PKR {df['cost'].sum():,.0f}")
                st.dataframe(df)
                csv = df.to_csv(index=False).encode()
                st.download_button("Download Report", csv, "maintenance_report.csv")

def main():
    st.set_page_config(page_title="PIA Operations", page_icon="✈️", layout="wide")
    
    init_session()
    apply_css()
    
    if not st.session_state.authenticated:
        show_auth()
        return
    
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.current_user['full_name']}")
        st.caption(f"**{st.session_state.current_user['role'].upper()}**")
        st.divider()
        
        page = st.radio("Navigation", [
            "📊 Dashboard",
            "📝 Forms & Submit",
            "📤 CSV Upload",
            "🗂️ Data Management",
            "💬 NL/AI Query",
            "📊 Reports"
        ])
        
        st.divider()
        st.caption("**System Status**")
        if supabase:
            st.success("✅ Supabase")
        st.caption(f"Mode: {'PRODUCTION' if supabase else 'DEMO'}")
        st.divider()
        
        if st.button("🚪 Logout"):
            logout()
    
    if "Dashboard" in page:
        page_dashboard()
    elif "Forms" in page:
        page_forms()
    elif "CSV" in page:
        page_csv_upload()
    elif "Data Management" in page:
        page_data()
    elif "NL/AI" in page:
        page_nl_query()
    elif "Reports" in page:
        page_reports()

if __name__ == "__main__":
    main()

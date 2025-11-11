"""
PIA Operations - Professional Airline Management System
PRODUCTION VERSION with Supabase (Persistent Data)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import hashlib
import secrets
import os
from typing import Optional, Dict
import time

# ============================================================================
# CONFIGURATION
# ============================================================================

PRIMARY_COLOR = "#006C35"
ACCENT_COLOR = "#C8102E"

# Get Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL", st.secrets.get("SUPABASE_URL", ""))
SUPABASE_KEY = os.getenv("SUPABASE_KEY", st.secrets.get("SUPABASE_KEY", ""))

# ============================================================================
# SUPABASE CONNECTION
# ============================================================================

@st.cache_resource
def init_supabase():
    """Initialize Supabase"""
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase.table('users').select("id").limit(1).execute()
        return supabase
    except:
        return None

supabase = init_supabase()

# ============================================================================
# SESSION STATE
# ============================================================================

def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None

# ============================================================================
# AUTH FUNCTIONS
# ============================================================================

def signup_user(username: str, email: str, password: str, full_name: str) -> tuple:
    if not supabase:
        return False, "Database not available"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
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
    except Exception as e:
        if "duplicate" in str(e).lower():
            return False, "Username/email exists"
        return False, str(e)

def login_user(username: str, password: str) -> tuple:
    if not supabase:
        return False, "Database not available"
    
    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        response = supabase.table('users').select("*").eq('username', username).eq('password_hash', password_hash).execute()
        
        if response.data and len(response.data) > 0:
            user = response.data[0]
            
            supabase.table('users').update({'last_login': datetime.now().isoformat()}).eq('id', user['id']).execute()
            
            st.session_state.authenticated = True
            st.session_state.current_user = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role']
            }
            return True, "Login successful!"
        return False, "Invalid credentials"
    except Exception as e:
        return False, str(e)

def request_reset(email: str) -> tuple:
    if not supabase:
        return False, "Database not available"
    
    try:
        response = supabase.table('users').select("id").eq('email', email).execute()
        if not response.data:
            return False, "Email not found"
        
        token = secrets.token_urlsafe(32)
        expiry = (datetime.now() + timedelta(hours=1)).isoformat()
        
        supabase.table('users').update({
            'reset_token': token,
            'reset_token_expiry': expiry
        }).eq('id', response.data[0]['id']).execute()
        
        return True, f"Token: {token}"
    except Exception as e:
        return False, str(e)

def reset_password(token: str, new_password: str) -> tuple:
    if not supabase:
        return False, "Database not available"
    
    try:
        response = supabase.table('users').select("*").eq('reset_token', token).execute()
        if not response.data:
            return False, "Invalid token"
        
        user = response.data[0]
        expiry = datetime.fromisoformat(user['reset_token_expiry'])
        if datetime.now() > expiry:
            return False, "Token expired"
        
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        supabase.table('users').update({
            'password_hash': password_hash,
            'reset_token': None,
            'reset_token_expiry': None
        }).eq('id', user['id']).execute()
        
        return True, "Password reset!"
    except Exception as e:
        return False, str(e)

def logout():
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.rerun()

# ============================================================================
# DATA FUNCTIONS
# ============================================================================

def get_data(table: str, limit: int = 1000) -> pd.DataFrame:
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table(table).select("*").limit(limit).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except:
        return pd.DataFrame()

def insert_data(table: str, data: Dict) -> bool:
    if not supabase:
        return False
    try:
        if st.session_state.current_user:
            data['created_by'] = st.session_state.current_user['username']
        supabase.table(table).insert(data).execute()
        return True
    except:
        return False

def generate_demo_data():
    if not supabase:
        return
    
    # Check if exists
    response = supabase.table('maintenance').select("id").limit(1).execute()
    if response.data:
        return
    
    import random
    
    # Maintenance
    aircraft = [f"AP-BH{chr(65+i)}" for i in range(10)]
    types = ["A-Check", "B-Check", "C-Check", "Engine Overhaul"]
    statuses = ["Scheduled", "In Progress", "Completed"]
    
    records = []
    for i in range(50):
        records.append({
            'aircraft_registration': random.choice(aircraft),
            'maintenance_type': random.choice(types),
            'scheduled_date': (datetime.now() - timedelta(days=random.randint(0, 180))).strftime('%Y-%m-%d'),
            'technician_name': f"Tech-{random.randint(100, 999)}",
            'hours_spent': round(random.uniform(2, 120), 1),
            'cost': round(random.uniform(5000, 500000), 2),
            'status': random.choice(statuses),
            'priority': random.choice(['Low', 'Medium', 'High', 'Critical']),
            'description': f"Maintenance {i+1}",
            'created_by': 'system'
        })
    
    supabase.table('maintenance').insert(records).execute()
    
    # Incidents
    incident_types = ["Bird Strike", "Hard Landing", "Engine Issue"]
    severities = ["Minor", "Moderate", "Major", "Critical"]
    
    records = []
    for i in range(30):
        records.append({
            'incident_date': (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d'),
            'incident_type': random.choice(incident_types),
            'severity': random.choice(severities),
            'aircraft_registration': random.choice(aircraft),
            'flight_number': f"PK{random.randint(100, 999)}",
            'location': random.choice(['Karachi', 'Lahore', 'Islamabad']),
            'description': f"Incident {i+1}",
            'investigation_status': random.choice(['Open', 'Closed']),
            'created_by': 'system'
        })
    
    supabase.table('safety_incidents').insert(records).execute()
    
    # Flights
    airports = ["KHI", "LHE", "ISB", "DXB", "LHR"]
    flight_statuses = ["Scheduled", "On Time", "Delayed", "Arrived"]
    
    records = []
    for i in range(100):
        dep = datetime.now() + timedelta(days=random.randint(-30, 30))
        arr = dep + timedelta(hours=random.randint(2, 12))
        
        records.append({
            'flight_number': f"PK{random.randint(100, 999)}",
            'aircraft_registration': random.choice(aircraft),
            'departure_airport': random.choice(airports),
            'arrival_airport': random.choice(airports),
            'scheduled_departure': dep.isoformat(),
            'scheduled_arrival': arr.isoformat(),
            'passengers_count': random.randint(50, 350),
            'flight_status': random.choice(flight_statuses),
            'created_by': 'system'
        })
    
    supabase.table('flights').insert(records).execute()

# ============================================================================
# UI
# ============================================================================

def apply_css():
    st.markdown(f"""
        <style>
        .stButton>button {{
            width: 100%;
            background-color: {PRIMARY_COLOR};
            color: white;
        }}
        .auth-logo {{ text-align: center; font-size: 4rem; }}
        .auth-title {{ text-align: center; color: {PRIMARY_COLOR}; font-size: 2.5rem; font-weight: 700; }}
        .dashboard-header {{
            background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, #004d26 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
        }}
        </style>
    """, unsafe_allow_html=True)

def show_auth():
    st.markdown('<div class="auth-logo">✈️</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">PIA Operations</div>', unsafe_allow_html=True)
    
    if not supabase:
        st.error("⚠️ Run SQL in Supabase first!")
        st.code("""
-- Copy and run in Supabase SQL Editor:

CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    reset_token TEXT,
    reset_token_expiry TIMESTAMP
);

INSERT INTO users (username, email, password_hash, full_name, role)
VALUES ('admin', 'admin@pia.com', 
        '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9',
        'Administrator', 'admin');

CREATE TABLE maintenance (
    id BIGSERIAL PRIMARY KEY,
    aircraft_registration TEXT NOT NULL,
    maintenance_type TEXT NOT NULL,
    description TEXT,
    scheduled_date DATE NOT NULL,
    completion_date DATE,
    technician_name TEXT,
    hours_spent REAL DEFAULT 0,
    cost REAL DEFAULT 0,
    status TEXT DEFAULT 'Scheduled',
    priority TEXT DEFAULT 'Medium',
    created_at TIMESTAMP DEFAULT NOW(),
    created_by TEXT
);

CREATE TABLE safety_incidents (
    id BIGSERIAL PRIMARY KEY,
    incident_date DATE NOT NULL,
    incident_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    aircraft_registration TEXT,
    flight_number TEXT,
    location TEXT,
    description TEXT NOT NULL,
    immediate_action TEXT,
    investigation_status TEXT DEFAULT 'Open',
    reporter_name TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by TEXT
);

CREATE TABLE flights (
    id BIGSERIAL PRIMARY KEY,
    flight_number TEXT NOT NULL,
    aircraft_registration TEXT NOT NULL,
    departure_airport TEXT NOT NULL,
    arrival_airport TEXT NOT NULL,
    scheduled_departure TIMESTAMP NOT NULL,
    actual_departure TIMESTAMP,
    scheduled_arrival TIMESTAMP NOT NULL,
    actual_arrival TIMESTAMP,
    passengers_count INTEGER DEFAULT 0,
    cargo_weight REAL DEFAULT 0,
    flight_status TEXT DEFAULT 'Scheduled',
    delay_reason TEXT,
    captain_name TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by TEXT
);
        """, language="sql")
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
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(msg)
        st.info("**Demo:** admin / admin123")
    
    with tab2:
        with st.form("signup"):
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            username = st.text_input("Username (3+ chars)")
            password = st.text_input("Password (6+ chars)", type="password")
            password2 = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Sign Up"):
                if password != password2:
                    st.error("Passwords don't match")
                else:
                    success, msg = signup_user(username, email, password, name)
                    if success:
                        st.success(msg)
                        st.balloons()
                    else:
                        st.error(msg)
    
    with tab3:
        step = st.radio("", ["Request Token", "Reset Password"])
        if step == "Request Token":
            with st.form("request"):
                email = st.text_input("Email")
                if st.form_submit_button("Get Token"):
                    success, msg = request_reset(email)
                    if success:
                        st.success("✅ Token generated!")
                        st.code(msg)
                    else:
                        st.error(msg)
        else:
            with st.form("reset"):
                token = st.text_input("Token")
                new_pass = st.text_input("New Password", type="password")
                confirm = st.text_input("Confirm", type="password")
                if st.form_submit_button("Reset"):
                    if new_pass != confirm:
                        st.error("Passwords don't match")
                    else:
                        success, msg = reset_password(token, new_pass)
                        if success:
                            st.success(msg)
                            st.balloons()
                        else:
                            st.error(msg)

def page_dashboard():
    st.markdown("""
        <div class="dashboard-header">
            <h1>✈️ PIA Operations Dashboard</h1>
            <p>Real-time airline operations management</p>
        </div>
    """, unsafe_allow_html=True)
    
    maint = get_data('maintenance')
    incidents = get_data('safety_incidents')
    flights = get_data('flights')
    
    if maint.empty:
        if st.button("📊 Generate Demo Data"):
            with st.spinner("Generating..."):
                generate_demo_data()
                st.success("Demo data created!")
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
    st.header("📝 Data Entry")
    
    with st.form("maintenance_form"):
        st.subheader("Add Maintenance Record")
        col1, col2 = st.columns(2)
        with col1:
            aircraft = st.text_input("Aircraft*", placeholder="AP-BHA")
            maint_type = st.selectbox("Type*", ["A-Check", "B-Check", "C-Check", "Engine Overhaul"])
            date = st.date_input("Date*")
            tech = st.text_input("Technician")
        with col2:
            hours = st.number_input("Hours", min_value=0.0)
            cost = st.number_input("Cost", min_value=0.0)
            status = st.selectbox("Status", ["Scheduled", "In Progress", "Completed"])
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
        
        desc = st.text_area("Description")
        
        if st.form_submit_button("Add"):
            if aircraft and maint_type:
                if insert_data('maintenance', {
                    'aircraft_registration': aircraft,
                    'maintenance_type': maint_type,
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

def page_data():
    st.header("🗂️ Data Management")
    
    table = st.selectbox("Table", ["Maintenance", "Safety Incidents", "Flights"])
    table_map = {"Maintenance": "maintenance", "Safety Incidents": "safety_incidents", "Flights": "flights"}
    
    df = get_data(table_map[table])
    
    if not df.empty:
        st.dataframe(df, use_container_width=True, height=400)
        csv = df.to_csv(index=False).encode()
        st.download_button("📥 Download", csv, f"{table_map[table]}.csv", "text/csv")
    else:
        st.info("No data. Generate from Dashboard.")

def main():
    st.set_page_config(page_title="PIA Operations", page_icon="✈️", layout="wide")
    
    init_session_state()
    apply_css()
    
    if not st.session_state.authenticated:
        show_auth()
        return
    
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.current_user['full_name']}")
        st.caption(f"**{st.session_state.current_user['role'].upper()}**")
        st.divider()
        
        page = st.radio("Navigation", ["📊 Dashboard", "📝 Forms", "🗂️ Data"])
        
        st.divider()
        if supabase:
            st.success("✅ Supabase")
        st.divider()
        
        if st.button("🚪 Logout"):
            logout()
    
    if "Dashboard" in page:
        page_dashboard()
    elif "Forms" in page:
        page_forms()
    else:
        page_data()

if __name__ == "__main__":
    main()

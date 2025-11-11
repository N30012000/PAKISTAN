"""
PIA Operations - Professional Airline Operations Management System
Complete authentication with Login, Signup, and Password Reset
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import hashlib
import secrets
import sqlite3
from typing import Optional, Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Application configuration"""
    # Database
    DATABASE_FILE = "pia_operations.db"
    USERS_DB_FILE = "pia_users.db"
    
    # API Keys
    GEMINI_API_KEY = os.getenv("AIzaSyBeBYUhILPIp3JEsLAWI7zUMDnzSp5YfiU", "")
    GROQ_API_KEY = os.getenv("gsk_GXIDsotkDUgI18b6qeyFWGdyb3FYITTTYCSRmZCKdgpa0fAOzM1YD", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # PIA Brand Colors
    PRIMARY_COLOR = "#006C35"
    SECONDARY_COLOR = "#FFFFFF"
    ACCENT_COLOR = "#C8102E"
    TEXT_COLOR = "#1E1E1E"
    
    # Security
    SESSION_TIMEOUT = 3600  # 1 hour

config = Config()

# ============================================================================
# USER AUTHENTICATION SYSTEM
# ============================================================================

class UserAuth:
    """Complete user authentication system with signup, login, and password reset"""
    
    def __init__(self):
        self.conn = sqlite3.connect(config.USERS_DB_FILE, check_same_thread=False)
        self._init_users_db()
    
    def _init_users_db(self):
        """Initialize users database"""
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                reset_token TEXT,
                reset_token_expiry TIMESTAMP
            )
        """)
        
        # Create default admin if doesn't exist
        try:
            admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            """, ("admin", "admin@pia.com", admin_hash, "System Administrator", "admin"))
            self.conn.commit()
            logger.info("Default admin user created")
        except sqlite3.IntegrityError:
            pass  # Admin already exists
    
    def signup_user(self, username: str, email: str, password: str, full_name: str) -> tuple:
        """Register new user"""
        try:
            # Validate inputs
            if len(username) < 3:
                return False, "Username must be at least 3 characters"
            if len(password) < 6:
                return False, "Password must be at least 6 characters"
            if "@" not in email:
                return False, "Invalid email address"
            
            # Hash password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Insert user
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name)
                VALUES (?, ?, ?, ?)
            """, (username, email, password_hash, full_name))
            self.conn.commit()
            
            return True, "Account created successfully!"
            
        except sqlite3.IntegrityError:
            return False, "Username or email already exists"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def login_user(self, username: str, password: str) -> tuple:
        """Login user"""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, username, email, full_name, role, is_active
                FROM users
                WHERE username = ? AND password_hash = ?
            """, (username, password_hash))
            
            user = cursor.fetchone()
            
            if user:
                if user[5] == 0:  # is_active
                    return False, "Account is deactivated", None
                
                # Update last login
                cursor.execute("""
                    UPDATE users SET last_login = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (user[0],))
                self.conn.commit()
                
                user_data = {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'full_name': user[3],
                    'role': user[4]
                }
                
                return True, "Login successful!", user_data
            else:
                return False, "Invalid username or password", None
                
        except Exception as e:
            return False, f"Error: {str(e)}", None
    
    def generate_reset_token(self, email: str) -> tuple:
        """Generate password reset token"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if not user:
                return False, "Email not found"
            
            # Generate token
            token = secrets.token_urlsafe(32)
            expiry = datetime.now() + timedelta(hours=1)
            
            cursor.execute("""
                UPDATE users 
                SET reset_token = ?, reset_token_expiry = ?
                WHERE email = ?
            """, (token, expiry, email))
            self.conn.commit()
            
            return True, f"Reset token generated: {token}"
            
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def reset_password(self, token: str, new_password: str) -> tuple:
        """Reset password using token"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, reset_token_expiry FROM users 
                WHERE reset_token = ?
            """, (token,))
            user = cursor.fetchone()
            
            if not user:
                return False, "Invalid reset token"
            
            # Check if token expired
            expiry = datetime.fromisoformat(user[1])
            if datetime.now() > expiry:
                return False, "Reset token expired"
            
            # Update password
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            cursor.execute("""
                UPDATE users 
                SET password_hash = ?, reset_token = NULL, reset_token_expiry = NULL
                WHERE id = ?
            """, (password_hash, user[0]))
            self.conn.commit()
            
            return True, "Password reset successfully!"
            
        except Exception as e:
            return False, f"Error: {str(e)}"

# Initialize auth system
auth = UserAuth()

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'auth_page' not in st.session_state:
        st.session_state.auth_page = 'login'

def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.auth_page = 'login'
    st.rerun()

# ============================================================================
# PROFESSIONAL AUTHENTICATION UI
# ============================================================================

def show_auth_page():
    """Show professional authentication page"""
    
    st.markdown("""
        <style>
        .auth-container {
            max-width: 450px;
            margin: 0 auto;
            padding: 2rem;
        }
        .auth-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .auth-logo {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        .auth-title {
            color: #006C35;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .auth-subtitle {
            color: #666;
            font-size: 1rem;
        }
        .form-container {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .stButton>button {
            width: 100%;
            background-color: #006C35;
            color: white;
            border-radius: 5px;
            padding: 0.75rem;
            font-weight: 600;
            border: none;
        }
        .stButton>button:hover {
            background-color: #004d26;
        }
        .auth-links {
            text-align: center;
            margin-top: 1rem;
        }
        .auth-link {
            color: #006C35;
            cursor: pointer;
            text-decoration: underline;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div class="auth-header">
                <div class="auth-logo">✈️</div>
                <div class="auth-title">PIA Operations</div>
                <div class="auth-subtitle">Professional Airline Management System</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Auth tabs
    tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Sign Up", "🔑 Reset Password"])
    
    with tab1:
        show_login_form()
    
    with tab2:
        show_signup_form()
    
    with tab3:
        show_reset_form()

def show_login_form():
    """Show login form"""
    st.markdown("### Welcome Back")
    st.markdown("Login to access your PIA Operations dashboard")
    
    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("👤 Username", placeholder="Enter your username")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            remember = st.checkbox("Remember me")
        
        submit = st.form_submit_button("🚀 Login")
        
        if submit:
            if not username or not password:
                st.error("Please fill in all fields")
            else:
                success, message, user_data = auth.login_user(username, password)
                
                if success:
                    st.session_state.authenticated = True
                    st.session_state.user = user_data
                    st.success(message)
                    st.balloons()
                    st.rerun()
                else:
                    st.error(message)
    
    st.divider()
    st.info("**Default Admin:** username: `admin` | password: `admin123`")

def show_signup_form():
    """Show signup form"""
    st.markdown("### Create Your Account")
    st.markdown("Join PIA Operations for professional airline management")
    
    with st.form("signup_form", clear_on_submit=True):
        full_name = st.text_input("👤 Full Name", placeholder="John Doe")
        email = st.text_input("📧 Email", placeholder="john@example.com")
        username = st.text_input("👤 Username", placeholder="Choose a username")
        password = st.text_input("🔒 Password", type="password", placeholder="At least 6 characters")
        password_confirm = st.text_input("🔒 Confirm Password", type="password", placeholder="Re-enter password")
        
        terms = st.checkbox("I agree to the Terms & Conditions")
        
        submit = st.form_submit_button("📝 Create Account")
        
        if submit:
            if not all([full_name, email, username, password, password_confirm]):
                st.error("Please fill in all fields")
            elif password != password_confirm:
                st.error("Passwords do not match")
            elif not terms:
                st.error("Please accept Terms & Conditions")
            else:
                success, message = auth.signup_user(username, email, password, full_name)
                
                if success:
                    st.success(message)
                    st.info("You can now login with your credentials")
                    st.balloons()
                else:
                    st.error(message)

def show_reset_form():
    """Show password reset form"""
    st.markdown("### Reset Your Password")
    
    reset_step = st.radio("", ["Request Reset Token", "Reset with Token"], horizontal=True)
    
    if reset_step == "Request Reset Token":
        with st.form("request_reset_form"):
            email = st.text_input("📧 Email Address", placeholder="Enter your registered email")
            submit = st.form_submit_button("📨 Send Reset Token")
            
            if submit:
                if not email:
                    st.error("Please enter your email")
                else:
                    success, message = auth.generate_reset_token(email)
                    if success:
                        st.success("Reset token generated!")
                        st.info(message)
                        st.warning("⚠️ In production, this would be sent via email. Copy the token above.")
                    else:
                        st.error(message)
    
    else:
        with st.form("reset_password_form"):
            token = st.text_input("🔑 Reset Token", placeholder="Paste your reset token here")
            new_password = st.text_input("🔒 New Password", type="password", placeholder="At least 6 characters")
            confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Re-enter password")
            
            submit = st.form_submit_button("🔄 Reset Password")
            
            if submit:
                if not all([token, new_password, confirm_password]):
                    st.error("Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    success, message = auth.reset_password(token, new_password)
                    if success:
                        st.success(message)
                        st.info("You can now login with your new password")
                        st.balloons()
                    else:
                        st.error(message)

# ============================================================================
# DATABASE LAYER
# ============================================================================

class DatabaseManager:
    """Database manager for operations data"""
    
    def __init__(self):
        self.conn = sqlite3.connect(config.DATABASE_FILE, check_same_thread=False)
        self._create_schema()
    
    def _create_schema(self):
        """Create database schema"""
        cursor = self.conn.cursor()
        
        # Maintenance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT
            )
        """)
        
        # Safety incidents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS safety_incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT
            )
        """)
        
        # Flights table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT
            )
        """)
        
        self.conn.commit()
    
    def query(self, table: str, filters: Optional[Dict] = None, limit: int = 1000) -> pd.DataFrame:
        """Query table"""
        try:
            query = f"SELECT * FROM {table}"
            params = []
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"{key} = ?")
                    params.append(value)
                query += " WHERE " + " AND ".join(conditions)
            
            query += f" LIMIT {limit}"
            return pd.read_sql_query(query, self.conn, params=params)
        except Exception as e:
            logger.error(f"Query error: {e}")
            return pd.DataFrame()
    
    def insert(self, table: str, data: Dict) -> bool:
        """Insert record"""
        try:
            data['created_by'] = st.session_state.user['username'] if st.session_state.user else 'system'
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            cursor = self.conn.cursor()
            cursor.execute(query, list(data.values()))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Insert error: {e}")
            return False

# Initialize database
@st.cache_resource
def get_database():
    return DatabaseManager()

db = get_database()

# ============================================================================
# DEMO DATA GENERATOR
# ============================================================================

def generate_demo_data():
    """Generate demo data if tables are empty"""
    import random
    
    # Check if data exists
    if len(db.query('maintenance', limit=1)) > 0:
        return
    
    logger.info("Generating demo data...")
    
    # Generate maintenance records
    aircraft = [f"AP-BH{chr(65+i)}" for i in range(10)]
    maintenance_types = ["A-Check", "B-Check", "C-Check", "Engine Overhaul", "Landing Gear"]
    statuses = ["Scheduled", "In Progress", "Completed", "Delayed"]
    priorities = ["Low", "Medium", "High", "Critical"]
    
    for i in range(50):
        db.insert('maintenance', {
            'aircraft_registration': random.choice(aircraft),
            'maintenance_type': random.choice(maintenance_types),
            'description': f"Routine {random.choice(maintenance_types)} maintenance",
            'scheduled_date': (datetime.now() - timedelta(days=random.randint(0, 180))).date(),
            'technician_name': f"Tech-{random.randint(100, 999)}",
            'hours_spent': round(random.uniform(2, 120), 1),
            'cost': round(random.uniform(5000, 500000), 2),
            'status': random.choice(statuses),
            'priority': random.choice(priorities)
        })
    
    logger.info("Demo data generated successfully")

# ============================================================================
# UI STYLING
# ============================================================================

def apply_custom_css():
    """Apply PIA branding"""
    st.markdown(f"""
        <style>
        .main-header {{
            background: linear-gradient(135deg, {config.PRIMARY_COLOR} 0%, #004d26 100%);
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            color: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .main-header h1 {{
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
        }}
        .kpi-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid {config.PRIMARY_COLOR};
        }}
        .kpi-value {{
            font-size: 2rem;
            font-weight: 700;
            color: {config.PRIMARY_COLOR};
        }}
        .stButton>button {{
            background-color: {config.PRIMARY_COLOR};
            color: white;
        }}
        .stButton>button:hover {{
            background-color: #004d26;
        }}
        </style>
    """, unsafe_allow_html=True)

# ============================================================================
# DASHBOARD PAGE
# ============================================================================

def page_dashboard():
    """Main dashboard"""
    st.markdown("""
        <div class="main-header">
            <h1>✈️ PIA Operations Dashboard</h1>
            <p>Real-time operational reporting and analytics</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Generate demo data if needed
    generate_demo_data()
    
    # Fetch data
    maintenance_df = db.query('maintenance')
    incidents_df = db.query('safety_incidents')
    flights_df = db.query('flights')
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_maintenance = len(maintenance_df)
        completed = len(maintenance_df[maintenance_df['status']=='Completed'])
        st.metric("Maintenance Tasks", total_maintenance, f"{completed} completed")
    
    with col2:
        total_incidents = len(incidents_df)
        critical = len(incidents_df[incidents_df['severity'].isin(['Major', 'Critical'])])
        st.metric("Safety Incidents", total_incidents, f"{critical} critical", delta_color="inverse")
    
    with col3:
        total_flights = len(flights_df)
        delayed = len(flights_df[flights_df['flight_status']=='Delayed'])
        st.metric("Total Flights", total_flights, f"{delayed} delayed", delta_color="inverse")
    
    with col4:
        total_hours = maintenance_df['hours_spent'].sum() if not maintenance_df.empty else 0
        st.metric("Maintenance Hours", f"{total_hours:,.0f}", "This period")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if not maintenance_df.empty:
            st.subheader("Maintenance by Type")
            fig = px.bar(maintenance_df.groupby('maintenance_type').size().reset_index(name='count'),
                        x='maintenance_type', y='count',
                        color_discrete_sequence=[config.PRIMARY_COLOR])
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if not incidents_df.empty:
            st.subheader("Safety Incidents by Severity")
            fig = px.pie(incidents_df.groupby('severity').size().reset_index(name='count'),
                        names='severity', values='count')
            st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# FORMS PAGE
# ============================================================================

def page_forms():
    """Data entry forms"""
    st.header("📝 Data Entry Forms")
    
    tab1, tab2, tab3 = st.tabs(["✈️ Maintenance", "⚠️ Safety Incident", "🛫 Flight"])
    
    with tab1:
        with st.form("maintenance_form"):
            col1, col2 = st.columns(2)
            with col1:
                aircraft = st.text_input("Aircraft Registration*")
                maint_type = st.selectbox("Type*", ["A-Check", "B-Check", "C-Check", "Engine Overhaul"])
                date = st.date_input("Scheduled Date*")
            with col2:
                technician = st.text_input("Technician")
                hours = st.number_input("Hours", min_value=0.0)
                cost = st.number_input("Cost (PKR)", min_value=0.0)
            
            description = st.text_area("Description")
            
            if st.form_submit_button("Submit"):
                if aircraft and maint_type:
                    if db.insert('maintenance', {
                        'aircraft_registration': aircraft,
                        'maintenance_type': maint_type,
                        'scheduled_date': date,
                        'technician_name': technician,
                        'hours_spent': hours,
                        'cost': cost,
                        'description': description,
                        'status': 'Scheduled',
                        'priority': 'Medium'
                    }):
                        st.success("✅ Record created!")
                        st.balloons()

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application"""
    
    st.set_page_config(
        page_title="PIA Operations",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    apply_custom_css()
    init_session_state()
    
    # Check authentication
    if not st.session_state.authenticated:
        show_auth_page()
        return
    
    # Show main app
    with st.sidebar:
        st.markdown(f"### Welcome, {st.session_state.user['full_name']}!")
        st.caption(f"Role: {st.session_state.user['role'].upper()}")
        
        st.divider()
        
        page = st.radio("Navigation", [
            "📊 Dashboard",
            "📝 Forms",
            "🗂️ Data Management"
        ])
        
        st.divider()
        
        if st.button("🚪 Logout", use_container_width=True):
            logout()
    
    # Route pages
    if "Dashboard" in page:
        page_dashboard()
    elif "Forms" in page:
        page_forms()

if __name__ == "__main__":
    main()

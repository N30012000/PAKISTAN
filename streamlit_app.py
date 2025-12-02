"""
PIA Operations - Production-Ready Airline Operational Reporting System
A scalable, secure, and comprehensive operations management system for Pakistan International Airlines
FIXED VERSION WITH WORKING GOOGLE OAUTH + GEMINI AI + GROQ AI + GENERIC CHAT + BEAUTIFUL UI
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from typing import Optional, Dict, List, Any
import hashlib
import logging
from io import BytesIO
import base64
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION & ENVIRONMENT
# ============================================================================

class Config:
    """Application configuration from environment variables"""
    # Database
    SUPABASE_URL = os.getenv("SUPABASE_URL", st.secrets.get("SUPABASE_URL", "") if hasattr(st, 'secrets') else "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", st.secrets.get("SUPABASE_KEY", "") if hasattr(st, 'secrets') else "")
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    
    # AI API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, 'secrets') else "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", "") if hasattr(st, 'secrets') else "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", st.secrets.get("OPENAI_API_KEY", "") if hasattr(st, 'secrets') else "")
    OPENSKY_USERNAME = os.getenv("OPENSKY_USERNAME", st.secrets.get("OPENSKY_USERNAME", "") if hasattr(st, 'secrets') else "")
    OPENSKY_PASSWORD = os.getenv("OPENSKY_PASSWORD", st.secrets.get("OPENSKY_PASSWORD", "") if hasattr(st, 'secrets') else "")
    
    # Timezone - Pakistan Standard Time (GMT+5)
    TIMEZONE_OFFSET = 5  # GMT+5
    
    # App Settings
    APP_MODE = os.getenv("APP_MODE", "production") 
    ENABLE_AUTH = os.getenv("ENABLE_AUTH", "true").lower() == "true"
    
    # PIA Brand Colors - Enhanced
    PRIMARY_COLOR = "#006C35"  # PIA Green
    PRIMARY_LIGHT = "#00A651"  # Lighter Green
    PRIMARY_DARK = "#004d26"   # Darker Green
    SECONDARY_COLOR = "#FFFFFF"  # White
    ACCENT_COLOR = "#C8102E"  # Red
    ACCENT_LIGHT = "#E85D75"  # Light Red
    TEXT_COLOR = "#1E1E1E"
    TEXT_LIGHT = "#6C757D"
    BACKGROUND = "#F8F9FA"
    CARD_BG = "#FFFFFF"

config = Config()

# ============================================================================
# TIMEZONE HELPER
# ============================================================================

def get_pakistan_time():
    """Get current time in Pakistan Standard Time (GMT+5)"""
    from datetime import timezone
    pkt = timezone(timedelta(hours=config.TIMEZONE_OFFSET))
    return datetime.now(pkt)

# ============================================================================
# DATABASE LAYER
# ============================================================================

class DatabaseManager:
    """Unified database manager supporting Supabase, PostgreSQL, MySQL, and SQLite"""
    
    def __init__(self):
        self.db_type = self._detect_db_type()
        self.connection = None
        self._init_database()
    
    def _detect_db_type(self) -> str:
        """Detect which database to use based on available credentials"""
        if config.SUPABASE_URL and config.SUPABASE_KEY:
            return "supabase"
        elif config.DATABASE_URL:
            if "postgres" in config.DATABASE_URL:
                return "postgresql"
            elif "mysql" in config.DATABASE_URL:
                return "mysql"
        return "sqlite"
    
    def _init_database(self):
        """Initialize database connection and create schema"""
        try:
            if self.db_type == "supabase":
                self._init_supabase()
            elif self.db_type == "sqlite":
                self._init_sqlite()
            else:
                self._init_sql_database()
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            self.db_type = "sqlite"
            self._init_sqlite()
    
    def _init_supabase(self):
        """Initialize Supabase connection"""
        try:
            from supabase import create_client, Client
            self.connection: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            logger.info("Connected to Supabase")
        except ImportError:
            logger.warning("supabase-py not installed, falling back to SQLite")
            self.db_type = "sqlite"
            self._init_sqlite()
    
    def _init_sqlite(self):
        """Initialize SQLite connection with schema"""
        import sqlite3
        self.connection = sqlite3.connect('pia_operations.db', check_same_thread=False)
        self._create_sqlite_schema()
        logger.info("Connected to SQLite")
    
    def _init_sql_database(self):
        """Initialize PostgreSQL/MySQL connection"""
        try:
            from sqlalchemy import create_engine
            self.connection = create_engine(config.DATABASE_URL, pool_pre_ping=True)
            logger.info(f"Connected to {self.db_type}")
        except Exception as e:
            logger.error(f"Failed to connect to {self.db_type}: {e}")
            self.db_type = "sqlite"
            self._init_sqlite()
    
    def _create_sqlite_schema(self):
        """Create SQLite tables"""
        cursor = self.connection.cursor()
        
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.connection.commit()
        logger.info("SQLite schema created")
    
    def query(self, table: str, filters: Optional[Dict] = None, limit: int = 1000) -> pd.DataFrame:
        """Generic query method"""
        try:
            if self.db_type == "supabase":
                return self._query_supabase(table, filters, limit)
            elif self.db_type == "sqlite":
                return self._query_sqlite(table, filters, limit)
            else:
                return self._query_sql(table, filters, limit)
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return pd.DataFrame()
    
    def _query_supabase(self, table: str, filters: Optional[Dict], limit: int) -> pd.DataFrame:
        """Query Supabase"""
        query = self.connection.table(table).select("*")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        response = query.limit(limit).execute()
        return pd.DataFrame(response.data)
    
    def _query_sqlite(self, table: str, filters: Optional[Dict], limit: int) -> pd.DataFrame:
        """Query SQLite"""
        query = f"SELECT * FROM {table}"
        params = []
        
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)
        
        query += f" LIMIT {limit}"
        return pd.read_sql_query(query, self.connection, params=params)
    
    def _query_sql(self, table: str, filters: Optional[Dict], limit: int) -> pd.DataFrame:
        """Query PostgreSQL/MySQL"""
        query = f"SELECT * FROM {table}"
        if filters:
            conditions = [f"{k} = :{k}" for k in filters.keys()]
            query += " WHERE " + " AND ".join(conditions)
        query += f" LIMIT {limit}"
        return pd.read_sql_query(query, self.connection, params=filters)
    
    def insert(self, table: str, data: Dict) -> bool:
        """Insert record"""
        try:
            if self.db_type == "supabase":
                self.connection.table(table).insert(data).execute()
            elif self.db_type == "sqlite":
                self._insert_sqlite(table, data)
            else:
                self._insert_sql(table, data)
            return True
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            return False
    
    def _insert_sqlite(self, table: str, data: Dict):
        """Insert into SQLite"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        cursor = self.connection.cursor()
        cursor.execute(query, list(data.values()))
        self.connection.commit()
    
    def _insert_sql(self, table: str, data: Dict):
        """Insert into PostgreSQL/MySQL"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f":{k}" for k in data.keys()])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        self.connection.execute(query, data)
    
    def bulk_insert(self, table: str, records: List[Dict]) -> int:
        """Bulk insert records"""
        success_count = 0
        for record in records:
            if self.insert(table, record):
                success_count += 1
        return success_count
    
    def update(self, table: str, record_id: int, data: Dict) -> bool:
        """Update record"""
        try:
            data['updated_at'] = datetime.now().isoformat()
            if self.db_type == "supabase":
                self.connection.table(table).update(data).eq('id', record_id).execute()
            elif self.db_type == "sqlite":
                self._update_sqlite(table, record_id, data)
            else:
                self._update_sql(table, record_id, data)
            return True
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return False
    
    def _update_sqlite(self, table: str, record_id: int, data: Dict):
        """Update SQLite record"""
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE id = ?"
        cursor = self.connection.cursor()
        cursor.execute(query, list(data.values()) + [record_id])
        self.connection.commit()
    
    def _update_sql(self, table: str, record_id: int, data: Dict):
        """Update PostgreSQL/MySQL record"""
        set_clause = ", ".join([f"{k} = :{k}" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE id = :id"
        data['id'] = record_id
        self.connection.execute(query, data)
    
    def delete(self, table: str, record_id: int) -> bool:
        """Delete record"""
        try:
            if self.db_type == "supabase":
                self.connection.table(table).delete().eq('id', record_id).execute()
            elif self.db_type == "sqlite":
                cursor = self.connection.cursor()
                cursor.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
                self.connection.commit()
            else:
                self.connection.execute(f"DELETE FROM {table} WHERE id = :id", {'id': record_id})
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    def clear_table(self, table: str) -> bool:
        """Clear all records from a table"""
        try:
            if self.db_type == "supabase":
                self.connection.table(table).delete().neq('id', 0).execute()
            elif self.db_type == "sqlite":
                cursor = self.connection.cursor()
                cursor.execute(f"DELETE FROM {table}")
                self.connection.commit()
            else:
                self.connection.execute(f"DELETE FROM {table}")
            return True
        except Exception as e:
            logger.error(f"Clear table failed: {e}")
            return False

# Initialize database
@st.cache_resource
def get_database():
    return DatabaseManager()

db = get_database()

# ============================================================================
# GEMINI AI HELPER
# ============================================================================

class GeminiAI:
    """Gemini AI integration for chat and analysis"""
    
    @staticmethod
    def chat(message: str, system_prompt: str = "") -> str:
        """Send message to Gemini and get response"""
        if not config.GEMINI_API_KEY:
            return "❌ Gemini API key not configured. Please add GEMINI_API_KEY to your secrets."
        
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=config.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-pro')
            
            # Combine system prompt with user message
            full_prompt = f"{system_prompt}\n\nUser: {message}" if system_prompt else message
            
            response = model.generate_content(full_prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return f"❌ Error communicating with Gemini: {str(e)}"
    
    @staticmethod
    def analyze_data(df: pd.DataFrame, question: str) -> str:
        """Use Gemini to analyze data and answer questions"""
        if not config.GEMINI_API_KEY:
            return "❌ Gemini API key not configured."
        
        try:
            # Prepare data summary
            data_summary = f"""
Dataset Information:
- Shape: {df.shape[0]} rows, {df.shape[1]} columns
- Columns: {', '.join(df.columns)}

Sample Data (first 5 rows):
{df.head().to_string()}

Statistics:
{df.describe().to_string()}
"""
            
            system_prompt = """You are an AI data analyst for Pakistan International Airlines. 
Analyze the provided data and answer the user's question with specific insights, patterns, and recommendations.
Be concise but thorough. Use bullet points for clarity."""
            
            full_prompt = f"{system_prompt}\n\nData:\n{data_summary}\n\nQuestion: {question}"
            
            import google.generativeai as genai
            genai.configure(api_key=config.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-pro')
            
            response = model.generate_content(full_prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini analysis error: {e}")
            return f"❌ Analysis error: {str(e)}"

# ============================================================================
# GROQ AI HELPER
# ============================================================================

class GroqAI:
    """Groq AI integration for fast inference"""
    
    @staticmethod
    def chat(message: str, system_prompt: str = "") -> str:
        """Send message to Groq and get response"""
        if not config.GROQ_API_KEY:
            return "❌ Groq API key not configured. Please add GROQ_API_KEY to your secrets."
        
        try:
            from groq import Groq
            
            client = Groq(api_key=config.GROQ_API_KEY)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
            
            response = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=messages,
                temperature=0.7,
                max_tokens=1024
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return f"❌ Error communicating with Groq: {str(e)}"
    
    @staticmethod
    def analyze_data(df: pd.DataFrame, question: str) -> str:
        """Use Groq to analyze data and answer questions"""
        if not config.GROQ_API_KEY:
            return "❌ Groq API key not configured."
        
        try:
            from groq import Groq
            
            # Prepare data summary
            data_summary = f"""
Dataset Information:
- Shape: {df.shape[0]} rows, {df.shape[1]} columns
- Columns: {', '.join(df.columns)}

Sample Data (first 5 rows):
{df.head().to_string()}

Statistics:
{df.describe().to_string()}
"""
            
            system_prompt = """You are an AI data analyst for Pakistan International Airlines. 
Analyze the provided data and answer the user's question with specific insights, patterns, and recommendations.
Be concise but thorough. Use bullet points for clarity."""
            
            client = Groq(api_key=config.GROQ_API_KEY)
            
            response = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Data:\n{data_summary}\n\nQuestion: {question}"}
                ],
                temperature=0.7,
                max_tokens=2048
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq analysis error: {e}")
            return f"❌ Analysis error: {str(e)}"

# ============================================================================
# FIXED AUTHENTICATION - Using streamlit-supabase-auth
# ============================================================================

def check_password():
    """
    FIXED Google OAuth Authentication using streamlit-supabase-auth
    This method works properly on Streamlit Cloud!
    """
    
    # 1. Check if user is already authenticated in Session State
    if st.session_state.get('authenticated', False):
        return True
    
    try:
        from streamlit_supabase_auth import login_form, logout_button
        
        # Show login page header
        st.markdown(f'''
            <div style="text-align:center;margin:3rem 0 2rem 0;">
                <div style="font-size:6rem;margin-bottom:1rem;animation:float 3s ease-in-out infinite;">✈️</div>
                <div style="background:linear-gradient(135deg, {config.PRIMARY_COLOR} 0%, {config.PRIMARY_DARK} 100%);
                            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                            font-size:3.5rem;font-weight:800;margin-bottom:0.5rem;letter-spacing:-1px;">
                    PIA Operations
                </div>
                <div style="color:{config.TEXT_LIGHT};font-size:1.2rem;font-weight:300;">
                    Secure Enterprise Login
                </div>
            </div>
            <style>
            @keyframes float {{
                0%, 100% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-20px); }}
            }}
            </style>
        ''', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info("🔒 Access is restricted to authorized personnel.")
            
            # Display login form with Google OAuth
            session = login_form(
                url=config.SUPABASE_URL,
                apiKey=config.SUPABASE_KEY,
                providers=["google"],
            )
            
            if session:
                # User is logged in - populate session state
                st.session_state.authenticated = True
                st.session_state.current_user = {
                    'id': session.get('user', {}).get('id', ''),
                    'email': session.get('user', {}).get('email', ''),
                    'username': session.get('user', {}).get('email', '').split('@')[0],
                    'full_name': session.get('user', {}).get('user_metadata', {}).get('full_name', 
                                 session.get('user', {}).get('email', '')),
                    'role': 'admin' if 'admin' in session.get('user', {}).get('email', '') else 'user'
                }
                
                # Clear URL parameters
                st.query_params.clear()
                st.rerun()
        
        return False
        
    except ImportError:
        # Fallback: If streamlit-supabase-auth is not installed, use direct Supabase approach
        st.error("❌ `streamlit-supabase-auth` package not found. Please add it to requirements.txt")
        st.code("pip install streamlit-supabase-auth", language="bash")
        return False

# ============================================================================
# DATA INTEGRATION SERVICES
# ============================================================================

class ExternalDataService:
    """Integration with external data sources"""
    
    @staticmethod
    def fetch_opensky_flights() -> Optional[pd.DataFrame]:
        """Fetch live flight data from OpenSky Network"""
        if not config.OPENSKY_USERNAME:
            return None
        
        try:
            import requests
            auth = (config.OPENSKY_USERNAME, config.OPENSKY_PASSWORD) if config.OPENSKY_PASSWORD else None
            response = requests.get(
                "https://opensky-network.org/api/states/all",
                auth=auth,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('states'):
                    df = pd.DataFrame(data['states'], columns=[
                        'icao24', 'callsign', 'origin_country', 'time_position',
                        'last_contact', 'longitude', 'latitude', 'baro_altitude',
                        'on_ground', 'velocity', 'true_track', 'vertical_rate',
                        'sensors', 'geo_altitude', 'squawk', 'spi', 'position_source'
                    ])
                    df = df[df['callsign'].str.strip().str.startswith('PIA', na=False)]
                    return df
        except Exception as e:
            logger.error(f"OpenSky API error: {e}")
        
        return None
    
    @staticmethod
    def fetch_weather(city: str = "Karachi") -> Optional[Dict]:
        """Fetch weather data from Open-Meteo (FREE, no API key needed!)"""
        try:
            import requests
            
            # City coordinates (latitude, longitude)
            city_coords = {
                "Karachi": (24.8607, 67.0011),
                "Lahore": (31.5204, 74.3587),
                "Islamabad": (33.6844, 73.0479),
                "Peshawar": (34.0151, 71.5249),
                "Quetta": (30.1798, 66.9750)
            }
            
            lat, lon = city_coords.get(city, (24.8607, 67.0011))  # Default to Karachi
            
            # Open-Meteo API - completely free, no API key required!
            url = f"https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': lat,
                'longitude': lon,
                'current_weather': True,
                'temperature_unit': 'celsius',
                'windspeed_unit': 'ms',
                'timezone': 'auto'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                current = data.get('current_weather', {})
                
                # Map weather codes to descriptions
                weather_codes = {
                    0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
                    45: 'Foggy', 48: 'Foggy', 51: 'Light drizzle', 53: 'Moderate drizzle',
                    55: 'Dense drizzle', 61: 'Slight rain', 63: 'Moderate rain',
                    65: 'Heavy rain', 71: 'Slight snow', 73: 'Moderate snow',
                    75: 'Heavy snow', 77: 'Snow grains', 80: 'Slight rain showers',
                    81: 'Moderate rain showers', 82: 'Violent rain showers',
                    85: 'Slight snow showers', 86: 'Heavy snow showers',
                    95: 'Thunderstorm', 96: 'Thunderstorm with hail', 99: 'Thunderstorm with hail'
                }
                
                weather_code = current.get('weathercode', 0)
                description = weather_codes.get(weather_code, 'Unknown')
                
                return {
                    'main': {
                        'temp': current.get('temperature', 0),
                        'humidity': 50
                    },
                    'weather': [{
                        'description': description,
                        'main': description.split()[0] if description else 'Clear'
                    }],
                    'wind': {
                        'speed': current.get('windspeed', 0)
                    },
                    'source': 'Open-Meteo (Free)'
                }
                
        except Exception as e:
            logger.error(f"Weather API error: {e}")
        
        return None

# ============================================================================
# NL QUERY ENGINE - USING GEMINI OR GROQ
# ============================================================================

class NLQueryEngine:
    """Natural language query processing with rule-based and AI fallback"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.rule_patterns = {
            'total_maintenance_hours': ['total maintenance hours', 'sum of maintenance hours', 'maintenance hours total'],
            'emergency_incidents': ['emergency', 'critical incidents', 'show emergency'],
            'delayed_flights': ['delayed flights', 'flight delays', 'delays'],
            'aircraft_status': ['aircraft status', 'status of aircraft', 'fleet status'],
            'recent_incidents': ['recent incidents', 'latest incidents', 'new incidents'],
        }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process natural language query"""
        query_lower = query.lower().strip()
        
        # Try rule-based matching first
        result = self._rule_based_query(query_lower)
        if result:
            return result
        
        # Try AI-powered query (Gemini first, then Groq)
        if config.GEMINI_API_KEY:
            result = self._ai_query(query, "gemini")
            if result:
                return result
        
        if config.GROQ_API_KEY:
            result = self._ai_query(query, "groq")
            if result:
                return result
        
        return {
            'success': False,
            'message': 'Could not understand query. Try: "total maintenance hours", "show emergency incidents", "delayed flights"',
            'data': None
        }
    
    def _rule_based_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Rule-based query matching"""
        
        if any(pattern in query for pattern in self.rule_patterns['total_maintenance_hours']):
            df = self.db.query('maintenance')
            if not df.empty:
                total_hours = df['hours_spent'].sum()
                return {
                    'success': True,
                    'message': f'Total maintenance hours: {total_hours:,.1f}',
                    'data': df[['aircraft_registration', 'maintenance_type', 'hours_spent', 'status']],
                    'chart_type': 'bar',
                    'metric': total_hours
                }
        
        if any(pattern in query for pattern in self.rule_patterns['emergency_incidents']):
            df = self.db.query('safety_incidents')
            if not df.empty:
                critical_df = df[df['severity'].isin(['Major', 'Critical'])]
                return {
                    'success': True,
                    'message': f'Found {len(critical_df)} critical incidents',
                    'data': critical_df,
                    'chart_type': 'table'
                }
        
        if any(pattern in query for pattern in self.rule_patterns['delayed_flights']):
            df = self.db.query('flights')
            if not df.empty:
                delayed_df = df[df['flight_status'] == 'Delayed']
                return {
                    'success': True,
                    'message': f'Found {len(delayed_df)} delayed flights',
                    'data': delayed_df[['flight_number', 'departure_airport', 'arrival_airport', 
                                        'scheduled_departure', 'delay_reason']],
                    'chart_type': 'table'
                }
        
        if any(pattern in query for pattern in self.rule_patterns['recent_incidents']):
            df = self.db.query('safety_incidents')
            if not df.empty:
                df['incident_date'] = pd.to_datetime(df['incident_date'])
                recent_df = df.nlargest(10, 'incident_date')
                return {
                    'success': True,
                    'message': f'10 most recent incidents',
                    'data': recent_df,
                    'chart_type': 'table'
                }
        
        return None
    
    def _ai_query(self, query: str, provider: str) -> Optional[Dict[str, Any]]:
        """AI-powered query using Gemini or Groq"""
        try:
            schema_info = """
            Available tables:
            1. maintenance: aircraft_registration, maintenance_type, scheduled_date, hours_spent, cost, status, priority
            2. safety_incidents: incident_date, incident_type, severity, aircraft_registration, flight_number, description
            3. flights: flight_number, aircraft_registration, departure_airport, arrival_airport, passengers_count, flight_status
            """
            
            prompt = f"""Given this database schema:
{schema_info}

Determine which table would answer this query: "{query}"

Respond with ONLY the table name: maintenance, safety_incidents, or flights"""
            
            if provider == "gemini":
                table = GeminiAI.chat(prompt).strip().lower()
            else:
                table = GroqAI.chat(prompt).strip().lower()
            
            # Validate table name
            if table not in ['maintenance', 'safety_incidents', 'flights']:
                return None
            
            df = self.db.query(table)
            
            return {
                'success': True,
                'message': f'Found {len(df)} records in {table} (via {provider.title()} AI)',
                'data': df,
                'chart_type': 'table'
            }
            
        except Exception as e:
            logger.error(f"AI query error: {e}")
            return None

# ============================================================================
# AI ANALYSIS ENGINE - USING GEMINI OR GROQ
# ============================================================================

class AIAnalysisEngine:
    """AI-powered analysis and reporting using Gemini or Groq"""
    
    @staticmethod
    def analyze_data(df: pd.DataFrame, analysis_type: str, prompt: str = "", provider: str = "gemini") -> str:
        """Analyze data and provide insights"""
        if df.empty:
            return "No data available for analysis."
        
        analysis = f"## Data Analysis Results\n\n"
        analysis += f"**Total Records:** {len(df)}\n\n"
        
        if analysis_type == "summary":
            analysis += "### Summary Statistics\n"
            analysis += df.describe().to_markdown() if hasattr(df.describe(), 'to_markdown') else str(df.describe())
        
        elif analysis_type == "trends":
            analysis += "### Trend Analysis\n"
            date_cols = df.select_dtypes(include=['datetime64']).columns
            if len(date_cols) > 0:
                analysis += f"Analyzing trends across {len(date_cols)} time-based dimensions.\n"
            else:
                analysis += "No time-based data found for trend analysis.\n"
        
        elif analysis_type == "anomalies":
            analysis += "### Anomaly Detection\n"
            numeric_cols = df.select_dtypes(include=['number']).columns
            for col in numeric_cols:
                mean = df[col].mean()
                std = df[col].std()
                anomalies = df[(df[col] > mean + 2*std) | (df[col] < mean - 2*std)]
                if len(anomalies) > 0:
                    analysis += f"- **{col}**: {len(anomalies)} potential anomalies detected\n"
        
        elif analysis_type == "root_cause":
            analysis += "### Root Cause Analysis Hints\n"
            analysis += "Based on the data patterns:\n"
            analysis += "- Check correlations between variables\n"
            analysis += "- Review temporal patterns\n"
            analysis += "- Identify common factors in incidents\n"
        
        # Enhance with AI insights
        if prompt:
            try:
                if provider == "gemini" and config.GEMINI_API_KEY:
                    ai_insight = GeminiAI.analyze_data(df, prompt)
                    analysis += f"\n\n### AI-Enhanced Insights (Gemini)\n{ai_insight}"
                elif provider == "groq" and config.GROQ_API_KEY:
                    ai_insight = GroqAI.analyze_data(df, prompt)
                    analysis += f"\n\n### AI-Enhanced Insights (Groq)\n{ai_insight}"
            except Exception as e:
                logger.error(f"AI analysis error: {e}")
        
        return analysis

# ============================================================================
# REPORT GENERATOR
# ============================================================================

class ReportGenerator:
    """Generate downloadable reports in various formats"""
    
    @staticmethod
    def generate_csv_report(df: pd.DataFrame, filename: str) -> bytes:
        """Generate CSV report"""
        return df.to_csv(index=False).encode('utf-8')
    
    @staticmethod
    def generate_excel_report(df: pd.DataFrame, filename: str) -> bytes:
        """Generate Excel report"""
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
        return output.getvalue()
    
    @staticmethod
    def generate_pdf_report(content: str, title: str) -> bytes:
        """Generate PDF report using reportlab"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            
            output = BytesIO()
            doc = SimpleDocTemplate(output, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor(config.PRIMARY_COLOR),
                spaceAfter=30
            )
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.2*inch))
            
            for line in content.split('\n'):
                if line.strip():
                    if line.startswith('##'):
                        story.append(Paragraph(line.replace('##', ''), styles['Heading2']))
                    elif line.startswith('-'):
                        story.append(Paragraph(line, styles['Bullet']))
                    else:
                        story.append(Paragraph(line, styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
            
            footer_text = f"Generated by PIA Operations System on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph(footer_text, styles['Italic']))
            
            doc.build(story)
            return output.getvalue()
            
        except ImportError:
            return content.encode('utf-8')

# ============================================================================
# PREDICTIVE ANALYTICS
# ============================================================================

class PredictiveAnalytics:
    """Predictive analytics module with baseline models"""
    
    @staticmethod
    def predict_delays(historical_data: pd.DataFrame) -> Dict[str, Any]:
        """Predict flight delays using simple baseline model"""
        if historical_data.empty:
            return {'error': 'Insufficient data'}
        
        try:
            delayed = historical_data[historical_data['flight_status'] == 'Delayed']
            delay_rate = len(delayed) / len(historical_data) * 100
            
            return {
                'overall_delay_rate': f"{delay_rate:.1f}%",
                'high_risk_routes': delayed.groupby('departure_airport').size().nlargest(5).to_dict(),
                'recommendation': 'Consider additional buffer time for high-risk routes',
                'model': 'Baseline Statistical Model'
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def forecast_maintenance_hours(maintenance_data: pd.DataFrame, periods: int = 30) -> Dict[str, Any]:
        """Forecast maintenance hours using moving average baseline"""
        if maintenance_data.empty or len(maintenance_data) < 10:
            return {'error': 'Insufficient historical data (need at least 10 records)'}
        
        try:
            daily_hours = maintenance_data.groupby('scheduled_date')['hours_spent'].sum()
            ma_7 = daily_hours.rolling(window=7).mean()
            forecast_value = ma_7.iloc[-1] if not ma_7.empty else daily_hours.mean()
            
            return {
                'forecast_daily_hours': f"{forecast_value:.1f}",
                'forecast_period': f"{periods} days",
                'total_forecast': f"{forecast_value * periods:.1f} hours",
                'model': 'Moving Average Baseline',
                'note': 'Install statsmodels for ARIMA forecasting'
            }
        except Exception as e:
            return {'error': str(e)}

# ============================================================================
# UI COMPONENTS - ENHANCED
# ============================================================================

def apply_custom_css():
    """Apply custom PIA branding and styling - ENHANCED VERSION"""
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        * {{
            font-family: 'Inter', sans-serif;
        }}
        
        .stApp {{
            background: linear-gradient(135deg, #f5f7fa 0%, #e8ecef 100%);
        }}
        
        .main-header {{
            background: linear-gradient(135deg, {config.PRIMARY_COLOR} 0%, {config.PRIMARY_DARK} 100%);
            padding: 2.5rem 2rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            color: white;
            box-shadow: 0 10px 30px rgba(0,108,53,0.2);
        }}
        
        .main-header h1 {{
            margin: 0;
            font-size: 2.8rem;
            font-weight: 800;
        }}
        
        .kpi-card {{
            background: linear-gradient(135deg, white 0%, #f8f9fa 100%);
            padding: 1.8rem;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border-left: 5px solid {config.PRIMARY_COLOR};
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
        }}
        
        .kpi-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0,108,53,0.15);
        }}
        
        .kpi-value {{
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, {config.PRIMARY_COLOR} 0%, {config.PRIMARY_LIGHT} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .kpi-label {{
            color: {config.TEXT_LIGHT};
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }}
        
        .stButton>button {{
            background: linear-gradient(135deg, {config.PRIMARY_COLOR} 0%, {config.PRIMARY_DARK} 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.7rem 2.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,108,53,0.2);
        }}
        
        .stButton>button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,108,53,0.3);
        }}
        
        [data-testid="stMetricValue"] {{
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, {config.PRIMARY_COLOR} 0%, {config.PRIMARY_LIGHT} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render application header with live clock in GMT+5"""
    pkt_time = get_pakistan_time()
    st.markdown(f"""
        <div class="main-header">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
                <div style="flex:1;min-width:300px;">
                    <h1>✈️ PIA Operations Dashboard</h1>
                    <p>Real-time operational reporting and analytics for Pakistan International Airlines</p>
                </div>
                <div style="text-align:right;min-width:200px;">
                    <div style="background:rgba(255,255,255,0.15);padding:1rem 1.5rem;border-radius:12px;">
                        <div style="color:white;font-size:0.75rem;opacity:0.9;margin-bottom:0.3rem;">
                            PAKISTAN TIME (GMT+5)
                        </div>
                        <div style="color:white;font-size:1.8rem;font-weight:700;">
                            {pkt_time.strftime('%H:%M:%S')}
                        </div>
                        <div style="color:white;font-size:0.75rem;opacity:0.8;margin-top:0.2rem;">
                            {pkt_time.strftime('%a, %d %b %Y')}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ============================================================================
# PAGE: DASHBOARD
# ============================================================================

def page_dashboard():
    """Main dashboard page with KPIs and charts"""
    st.header("📊 Operations Dashboard")
    
    # Fetch data
    maintenance_df = db.query('maintenance', limit=1000)
    incidents_df = db.query('safety_incidents', limit=1000)
    flights_df = db.query('flights', limit=1000)
    
    # Show message if no data
    if maintenance_df.empty and incidents_df.empty and flights_df.empty:
        st.info("📝 **No data found.** Please add data using:")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("- **📝 Forms & Submit** - Add individual records")
        with col2:
            st.markdown("- **📤 CSV Upload** - Bulk import data")
        return
    
    # KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_maintenance = len(maintenance_df)
        completed = len(maintenance_df[maintenance_df['status']=='Completed']) if not maintenance_df.empty else 0
        st.metric("Maintenance Tasks", total_maintenance, delta=f"{completed} completed")
    
    with col2:
        total_incidents = len(incidents_df)
        critical = len(incidents_df[incidents_df['severity'].isin(['Major', 'Critical'])]) if not incidents_df.empty else 0
        st.metric("Safety Incidents", total_incidents, delta=f"{critical} critical", delta_color="inverse")
    
    with col3:
        total_flights = len(flights_df)
        delayed = len(flights_df[flights_df['flight_status']=='Delayed']) if not flights_df.empty else 0
        st.metric("Total Flights", total_flights, delta=f"{delayed} delayed", delta_color="inverse")
    
    with col4:
        total_hours = maintenance_df['hours_spent'].sum() if not maintenance_df.empty else 0
        st.metric("Maintenance Hours", f"{total_hours:,.0f}", delta="This period")
    
    with col5:
        weather_data = ExternalDataService.fetch_weather("Karachi")
        if weather_data:
            temp = weather_data['main']['temp']
            description = weather_data['weather'][0]['description'].title()
            st.metric(f"☀️ Karachi", f"{temp:.1f}°C", delta=description)
        else:
            st.metric("🌤️ Weather", "Loading...", delta="Fetching data")
    
    st.divider()
    
    # Charts Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Maintenance by Type")
        if not maintenance_df.empty:
            maint_type_counts = maintenance_df['maintenance_type'].value_counts()
            fig = px.bar(x=maint_type_counts.index, y=maint_type_counts.values,
                         labels={'x': 'Type', 'y': 'Count'},
                         color_discrete_sequence=[config.PRIMARY_COLOR])
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No maintenance data available")
    
    with col2:
        st.subheader("Safety Incidents by Severity")
        if not incidents_df.empty:
            severity_counts = incidents_df['severity'].value_counts()
            fig = px.pie(values=severity_counts.values, names=severity_counts.index,
                         color_discrete_sequence=[config.PRIMARY_COLOR, config.ACCENT_COLOR, '#FFA500', '#FFD700'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No incident data available")

# ============================================================================
# PAGE: FORMS & SUBMIT
# ============================================================================

def page_forms():
    """CRUD forms for data entry"""
    st.header("📝 Data Entry Forms")
    
    tab1, tab2, tab3 = st.tabs(["✈️ Maintenance", "⚠️ Safety Incident", "🛫 Flight Record"])
    
    with tab1:
        st.subheader("Maintenance Record")
        with st.form("maintenance_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                aircraft = st.text_input("Aircraft Registration*", placeholder="AP-BHA")
                maint_type = st.selectbox("Maintenance Type*", 
                    ["A-Check", "B-Check", "C-Check", "D-Check", "Engine Overhaul", 
                     "Landing Gear", "Avionics", "Interior Refurb"])
                scheduled_date = st.date_input("Scheduled Date*", datetime.now())
                completion_date = st.date_input("Completion Date", None)
            
            with col2:
                technician = st.text_input("Technician Name", placeholder="Tech-001")
                hours = st.number_input("Hours Spent", min_value=0.0, step=0.5)
                cost = st.number_input("Cost (PKR)", min_value=0.0, step=1000.0)
                status = st.selectbox("Status", ["Scheduled", "In Progress", "Completed", "Delayed"])
            
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
            description = st.text_area("Description")
            
            submitted = st.form_submit_button("Submit Maintenance Record")
            
            if submitted:
                if not aircraft or not maint_type:
                    st.error("Please fill required fields marked with *")
                else:
                    record = {
                        'aircraft_registration': aircraft,
                        'maintenance_type': maint_type,
                        'description': description,
                        'scheduled_date': scheduled_date.isoformat(),
                        'completion_date': completion_date.isoformat() if completion_date else None,
                        'technician_name': technician,
                        'hours_spent': hours,
                        'cost': cost,
                        'status': status,
                        'priority': priority
                    }
                    
                    if db.insert('maintenance', record):
                        st.success("✅ Maintenance record created successfully!")
                        st.balloons()
                    else:
                        st.error("Failed to create record")
    
    with tab2:
        st.subheader("Safety Incident Report")
        with st.form("incident_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                incident_date = st.date_input("Incident Date*", datetime.now())
                incident_type = st.selectbox("Incident Type*",
                    ["Bird Strike", "Hard Landing", "Engine Issue", "Weather Diversion",
                     "Cabin Pressure", "Hydraulic Failure", "Ground Incident", "Medical Emergency"])
                severity = st.selectbox("Severity*", ["Minor", "Moderate", "Major", "Critical"])
                aircraft = st.text_input("Aircraft Registration", placeholder="AP-BHA")
            
            with col2:
                flight_number = st.text_input("Flight Number", placeholder="PK300")
                location = st.text_input("Location", placeholder="Karachi")
                reporter = st.text_input("Reporter Name", placeholder="Capt. Khan")
                investigation_status = st.selectbox("Investigation Status", 
                    ["Open", "Under Investigation", "Closed", "Pending"])
            
            description = st.text_area("Incident Description*", height=100)
            immediate_action = st.text_area("Immediate Action Taken", height=100)
            
            submitted = st.form_submit_button("Submit Incident Report")
            
            if submitted:
                if not incident_date or not incident_type or not severity or not description:
                    st.error("Please fill required fields marked with *")
                else:
                    record = {
                        'incident_date': incident_date.isoformat(),
                        'incident_type': incident_type,
                        'severity': severity,
                        'aircraft_registration': aircraft,
                        'flight_number': flight_number,
                        'location': location,
                        'description': description,
                        'immediate_action': immediate_action,
                        'investigation_status': investigation_status,
                        'reporter_name': reporter
                    }
                    
                    if db.insert('safety_incidents', record):
                        st.success("✅ Incident report submitted successfully!")
                        st.balloons()
                    else:
                        st.error("Failed to submit report")
    
    with tab3:
        st.subheader("Flight Record")
        with st.form("flight_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                flight_number = st.text_input("Flight Number*", placeholder="PK300")
                aircraft = st.text_input("Aircraft Registration*", placeholder="AP-BHA")
                departure = st.text_input("Departure Airport*", placeholder="KHI")
                arrival = st.text_input("Arrival Airport*", placeholder="LHE")
                scheduled_dep = st.text_input("Scheduled Departure*", value=datetime.now().strftime("%Y-%m-%d %H:%M"))
            
            with col2:
                scheduled_arr = st.text_input("Scheduled Arrival*", 
                    value=(datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"))
                passengers = st.number_input("Passengers", min_value=0, max_value=500, step=1)
                cargo = st.number_input("Cargo Weight (kg)", min_value=0.0, step=100.0)
                status = st.selectbox("Status", 
                    ["Scheduled", "On Time", "Delayed", "Departed", "Arrived", "Cancelled"])
                captain = st.text_input("Captain Name", placeholder="Capt. Khan")
            
            delay_reason = st.text_input("Delay Reason (if applicable)")
            
            submitted = st.form_submit_button("Submit Flight Record")
            
            if submitted:
                if not flight_number or not aircraft or not departure or not arrival:
                    st.error("Please fill required fields marked with *")
                else:
                    record = {
                        'flight_number': flight_number,
                        'aircraft_registration': aircraft,
                        'departure_airport': departure,
                        'arrival_airport': arrival,
                        'scheduled_departure': scheduled_dep,
                        'actual_departure': None,
                        'scheduled_arrival': scheduled_arr,
                        'actual_arrival': None,
                        'passengers_count': passengers,
                        'cargo_weight': cargo,
                        'flight_status': status,
                        'delay_reason': delay_reason,
                        'captain_name': captain
                    }
                    
                    if db.insert('flights', record):
                        st.success("✅ Flight record created successfully!")
                        st.balloons()
                    else:
                        st.error("Failed to create record")

# ============================================================================
# PAGE: CSV UPLOAD
# ============================================================================

def page_csv_upload():
    """Bulk CSV upload with flexible header mapping"""
    st.header("📤 CSV Bulk Upload")
    
    st.markdown("### 📥 Download CSV Templates")
    st.info("💡 **New to bulk upload?** Download a template file below, fill it with your data, and upload it back!")
    
    col1, col2, col3 = st.columns(3)
    
    templates = {
        'maintenance': {
            'data': """aircraft_registration,maintenance_type,description,scheduled_date,completion_date,technician_name,hours_spent,cost,status,priority
AP-BHA,A-Check,Routine A-Check inspection,2024-01-15,2024-01-16,Tech-101,8.5,45000,Completed,Medium""",
            'filename': 'maintenance_template.csv',
            'icon': '✈️'
        },
        'safety_incidents': {
            'data': """incident_date,incident_type,severity,aircraft_registration,flight_number,location,description,immediate_action,investigation_status,reporter_name
2024-01-10,Bird Strike,Minor,AP-BHA,PK301,Karachi,Bird strike during takeoff,Flight continued safely,Closed,Capt. Khan""",
            'filename': 'safety_incidents_template.csv',
            'icon': '⚠️'
        },
        'flights': {
            'data': """flight_number,aircraft_registration,departure_airport,arrival_airport,scheduled_departure,scheduled_arrival,passengers_count,cargo_weight,flight_status,delay_reason,captain_name
PK301,AP-BHA,KHI,LHE,2024-01-15 08:00,2024-01-15 09:30,245,8500,Arrived,,Capt. Khan""",
            'filename': 'flights_template.csv',
            'icon': '🛫'
        }
    }
    
    with col1:
        st.markdown(f"#### {templates['maintenance']['icon']} Maintenance")
        st.download_button(
            label="Download Template",
            data=templates['maintenance']['data'],
            file_name=templates['maintenance']['filename'],
            mime='text/csv',
            key='download_maintenance',
            use_container_width=True
        )
    
    with col2:
        st.markdown(f"#### {templates['safety_incidents']['icon']} Safety Incidents")
        st.download_button(
            label="Download Template",
            data=templates['safety_incidents']['data'],
            file_name=templates['safety_incidents']['filename'],
            mime='text/csv',
            key='download_incidents',
            use_container_width=True
        )
    
    with col3:
        st.markdown(f"#### {templates['flights']['icon']} Flights")
        st.download_button(
            label="Download Template",
            data=templates['flights']['data'],
            file_name=templates['flights']['filename'],
            mime='text/csv',
            key='download_flights',
            use_container_width=True
        )
    
    st.divider()
    
    st.markdown("### 📤 Upload Your CSV File")
    
    table_choice = st.selectbox("Select Target Table", 
        ["maintenance", "safety_incidents", "flights"])
    
    uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ File uploaded: {len(df)} rows found")
            st.dataframe(df.head())
            
            if st.button("Import Data", type="primary"):
                with st.spinner("Importing data..."):
                    records = df.to_dict('records')
                    success_count = db.bulk_insert(table_choice, records)
                    
                    if success_count > 0:
                        st.success(f"✅ Successfully imported {success_count} records!")
                        st.balloons()
                    else:
                        st.error("Failed to import records")
        
        except Exception as e:
            st.error(f"Error processing file: {e}")

# ============================================================================
# PAGE: DATA MANAGEMENT
# ============================================================================

def page_data_management():
    """View, edit, and delete records"""
    st.header("🗂️ Data Management")
    
    table = st.selectbox("Select Table", ["maintenance", "safety_incidents", "flights"])
    
    df = db.query(table, limit=1000)
    
    if df.empty:
        st.warning("No records found")
        return
    
    st.subheader(f"Total Records: {len(df)}")
    st.dataframe(df, use_container_width=True, height=400)
    
    st.subheader("Delete Record")
    
    if 'id' in df.columns:
        record_id = st.number_input("Record ID to Delete", min_value=1, step=1)
        
        if st.button("🗑️ Delete Record", type="secondary"):
            if db.delete(table, record_id):
                st.success("Record deleted successfully!")
                st.rerun()
            else:
                st.error("Failed to delete record")

# ============================================================================
# PAGE: NL/AI QUERY
# ============================================================================

def page_nl_query():
    """Natural language query interface with AI"""
    st.header("💬 Natural Language Query")
    
    st.markdown("""
    Ask questions about your operations data in plain English. Examples:
    - "Total maintenance hours"
    - "Show emergency incidents"
    - "Delayed flights"
    """)
    
    query_engine = NLQueryEngine(db)
    
    query = st.text_input("Enter your question:", placeholder="Total maintenance hours")
    
    if st.button("Search", type="primary"):
        if query:
            with st.spinner("Processing query..."):
                result = query_engine.process_query(query)
                
                if result['success']:
                    st.success(result['message'])
                    
                    if result['data'] is not None and not result['data'].empty:
                        st.dataframe(result['data'], use_container_width=True)
                else:
                    st.warning(result['message'])
    
    st.divider()
    st.subheader("🤖 AI Analysis Assistant")
    
    # Show AI status
    col1, col2 = st.columns(2)
    with col1:
        if config.GEMINI_API_KEY:
            st.success("✅ Gemini AI enabled")
        else:
            st.warning("⚠️ Gemini AI not configured")
    with col2:
        if config.GROQ_API_KEY:
            st.success("✅ Groq AI enabled")
        else:
            st.warning("⚠️ Groq AI not configured")
    
    if not config.GEMINI_API_KEY and not config.GROQ_API_KEY:
        st.error("❌ No AI provider configured. Add GEMINI_API_KEY or GROQ_API_KEY to secrets.")
        return
    
    analysis_prompt = st.text_area("Ask for analysis or insights:", 
        placeholder="Analyze maintenance trends and suggest optimizations...")
    
    col1, col2 = st.columns(2)
    with col1:
        analysis_type = st.selectbox("Analysis Type", 
            ["summary", "trends", "anomalies", "root_cause"])
    with col2:
        ai_provider = st.selectbox("AI Provider", 
            [p for p in ["gemini", "groq"] if getattr(config, f"{p.upper()}_API_KEY")])
    
    table_for_analysis = st.selectbox("Data Source", 
        ["maintenance", "safety_incidents", "flights"])
    
    if st.button("Analyze", type="primary"):
        if analysis_prompt:
            with st.spinner(f"Analyzing data with {ai_provider.title()} AI..."):
                df = db.query(table_for_analysis, limit=1000)
                
                if df.empty:
                    st.warning("No data available for analysis")
                else:
                    analysis = AIAnalysisEngine.analyze_data(df, analysis_type, analysis_prompt, ai_provider)
                    st.markdown(analysis)

# ============================================================================
# PAGE: GENERIC AI CHAT
# ============================================================================

def page_ai_chat():
    """Generic AI chat assistant using Gemini or Groq"""
    st.header("🤖 AI Assistant")
    
    st.markdown("""
    Chat with an AI assistant about anything! Choose between Gemini or Groq.
    """)
    
    # Show AI status
    col1, col2 = st.columns(2)
    with col1:
        if config.GEMINI_API_KEY:
            st.success("✅ Gemini AI available")
        else:
            st.info("ℹ️ Gemini not configured")
    with col2:
        if config.GROQ_API_KEY:
            st.success("✅ Groq AI available")
        else:
            st.info("ℹ️ Groq not configured")
    
    if not config.GEMINI_API_KEY and not config.GROQ_API_KEY:
        st.error("❌ **No AI configured.** Please add GEMINI_API_KEY or GROQ_API_KEY to your secrets.")
        return
    
    # Choose AI provider
    available_providers = []
    if config.GEMINI_API_KEY:
        available_providers.append("Gemini (Google)")
    if config.GROQ_API_KEY:
        available_providers.append("Groq (Fast)")
    
    ai_provider = st.selectbox("Select AI Provider", available_providers)
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Clear chat button
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            st.markdown(f"**You:** {message['content']}")
        else:
            st.markdown(f"**AI ({message.get('provider', 'AI')}):** {message['content']}")
        st.divider()
    
    # Chat input
    user_message = st.text_area("Your message:", placeholder="Ask me anything...", height=100)
    
    if st.button("📤 Send", type="primary"):
        if user_message:
            # Add user message to history
            st.session_state.chat_history.append({'role': 'user', 'content': user_message})
            
            with st.spinner(f"{ai_provider} is thinking..."):
                system_prompt = """You are a helpful AI assistant for Pakistan International Airlines. 
Be friendly, informative, and concise. Help with airline operations, technology, or general topics."""
                
                if "Gemini" in ai_provider:
                    ai_response = GeminiAI.chat(user_message, system_prompt)
                    provider_name = "Gemini"
                else:
                    ai_response = GroqAI.chat(user_message, system_prompt)
                    provider_name = "Groq"
                
                # Add AI response to history
                st.session_state.chat_history.append({
                    'role': 'assistant', 
                    'content': ai_response,
                    'provider': provider_name
                })
            
            st.rerun()

# ============================================================================
# PAGE: REPORTS
# ============================================================================

def page_reports():
    """Generate scheduled and on-demand reports"""
    st.header("📊 Reports & Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        report_type = st.selectbox("Report Type", 
            ["Maintenance Summary", "Safety Report", "Flight Operations"])
        format_choice = st.selectbox("Format", ["CSV", "Excel"])
    
    with col2:
        date_from = st.date_input("From Date", datetime.now() - timedelta(days=30))
        date_to = st.date_input("To Date", datetime.now())
    
    if st.button("Generate Report", type="primary"):
        with st.spinner("Generating report..."):
            if report_type == "Maintenance Summary":
                df = db.query('maintenance', limit=1000)
            elif report_type == "Safety Report":
                df = db.query('safety_incidents', limit=1000)
            else:
                df = db.query('flights', limit=1000)
            
            if not df.empty:
                if format_choice == "CSV":
                    csv_data = ReportGenerator.generate_csv_report(df, f"{report_type}.csv")
                    st.download_button("Download CSV", csv_data,
                        f"{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv")
                else:
                    excel_data = ReportGenerator.generate_excel_report(df, f"{report_type}.xlsx")
                    st.download_button("Download Excel", excel_data,
                        f"{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
                st.dataframe(df, use_container_width=True)
                st.success("Report generated successfully!")
            else:
                st.warning("No data available for selected criteria")

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    
    st.set_page_config(
        page_title="PIA Operations",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    apply_custom_css()
    
    # FIXED: Use new authentication
    if not check_password():
        return
    
    render_header()
    
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/thumb/9/9b/Pakistan_International_Airlines_Logo.svg/1200px-Pakistan_International_Airlines_Logo.svg.png", use_container_width=True)
        
        # Live Clock
        pkt_time = get_pakistan_time()
        st.markdown(f"""
            <div style="background:linear-gradient(135deg, {config.PRIMARY_COLOR} 0%, {config.PRIMARY_DARK} 100%);
                        padding:1.5rem;border-radius:12px;margin-bottom:1rem;text-align:center;">
                <div style="color:white;font-size:0.85rem;font-weight:600;">🕐 PAKISTAN TIME (GMT+5)</div>
                <div style="color:white;font-size:1.8rem;font-weight:800;">{pkt_time.strftime('%H:%M:%S')}</div>
                <div style="color:white;font-size:0.85rem;opacity:0.8;">{pkt_time.strftime('%A, %B %d, %Y')}</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.title("Navigation")
        
        page = st.radio("Go to", [
            "📊 Dashboard",
            "📝 Forms & Submit",
            "📤 CSV Upload",
            "🗂️ Data Management",
            "💬 NL/AI Query",
            "🤖 AI Assistant",
            "📊 Reports"
        ])
        
        st.divider()
        
        if st.session_state.get('current_user'):
            user = st.session_state.current_user
            st.markdown(f"### 👤 {user['full_name']}")
            st.caption(f"@{user['username']} | {user['role'].title()}")
            
            # Logout button using streamlit-supabase-auth
            try:
                from streamlit_supabase_auth import logout_button
                logout_button(url=config.SUPABASE_URL, apiKey=config.SUPABASE_KEY)
            except:
                if st.button("🚪 Logout", use_container_width=True):
                    st.session_state.authenticated = False
                    st.session_state.current_user = None
                    st.rerun()
        
        st.divider()
        
        # System Status
        st.subheader("System Status")
        st.caption(f"Database: {db.db_type.upper()}")
        
        # AI Status
        if config.GEMINI_API_KEY:
            st.success("✅ Gemini AI")
        if config.GROQ_API_KEY:
            st.success("✅ Groq AI")
        if not config.GEMINI_API_KEY and not config.GROQ_API_KEY:
            st.warning("⚠️ No AI configured")
    
    # Route to pages
    if "Dashboard" in page:
        page_dashboard()
    elif "Forms" in page:
        page_forms()
    elif "CSV" in page:
        page_csv_upload()
    elif "Data Management" in page:
        page_data_management()
    elif "NL/AI Query" in page:
        page_nl_query()
    elif "AI Assistant" in page:
        page_ai_chat()
    elif "Reports" in page:
        page_reports()
    
    st.divider()
    st.caption("© 2025 Pakistan International Airlines - Operations Management System v2.0 | Powered by Gemini & Groq AI")

if __name__ == "__main__":
    main()

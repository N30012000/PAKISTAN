# ⚡ Quick Start Guide - PIA Operations

Get your PIA Operations system running in **under 5 minutes**!

## 🎯 What You'll Get

A fully functional airline operations management system with:
- ✅ Real-time operational dashboards
- ✅ Maintenance tracking and management
- ✅ Safety incident reporting
- ✅ Flight operations logging
- ✅ AI-powered analytics (optional)
- ✅ Automated reporting
- ✅ Data import/export capabilities

---

## 🚀 Option 1: Instant Cloud Deploy (EASIEST - 5 min)

### Step 1: Get Free Supabase Database
1. Go to [supabase.com](https://supabase.com)
2. Click "Start your project" → Sign up (GitHub account works)
3. Create new project: Name it "pia-operations"
4. Copy your credentials:
   - **URL**: `https://xxxxx.supabase.co`
   - **API Key**: Long string starting with `eyJ...`

### Step 2: Deploy to Streamlit Cloud
1. Upload all files to GitHub (or fork this repo)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app"
4. Select repository → Main file: `streamlit_app.py`
5. Click "Advanced" → Add secrets:
   ```toml
   SUPABASE_URL = "your-url-here"
   SUPABASE_KEY = "your-key-here"
   ```
6. Click "Deploy"

### Step 3: Access Your App
- URL will be: `https://yourapp.streamlit.app`
- Demo data loads automatically
- Start using immediately!

**🎉 Done! Your system is live.**

---

## 💻 Option 2: Run Locally (FASTEST - 2 min)

### Prerequisites
- Python 3.9+ installed
- That's it!

### Commands
```bash
# 1. Install dependencies
pip install streamlit pandas plotly sqlalchemy

# 2. Run the app
streamlit run streamlit_app.py

# 3. Open browser
# Automatically opens at http://localhost:8501
```

**Note**: Without Supabase, it uses SQLite automatically (creates local `pia_operations.db` file)

---

## 🎓 First Time Using the App?

### 1. Explore the Dashboard (Default Page)
- View KPI cards: maintenance tasks, incidents, flights
- Check interactive charts
- Explore demo data (auto-loaded)

### 2. Add Your First Record
- Click "📝 Forms & Submit" in sidebar
- Choose a tab: Maintenance / Safety / Flight
- Fill the form and submit
- See it appear in Dashboard!

### 3. Import Bulk Data
- Click "📤 CSV Upload"
- Use provided `sample_*.csv` files
- Map columns and import

### 4. Try Natural Language Queries
- Click "💬 NL/AI Query"
- Type: "total maintenance hours"
- Or: "show emergency incidents"

### 5. Generate Reports
- Click "📊 Reports"
- Select period and format
- Download PDF/Excel/CSV

---

## 🔧 Configuration (Optional Enhancements)

### Enable AI Features
Add to secrets/environment:
```
OPENAI_API_KEY=sk-your-key
```
**Get free credits**: [platform.openai.com](https://platform.openai.com)

**Unlocks**:
- Advanced natural language queries
- AI-powered analysis
- Intelligent insights

### Enable Live Flight Tracking
```
OPENSKY_USERNAME=your-username
OPENSKY_PASSWORD=your-password
```
**Free signup**: [opensky-network.org](https://opensky-network.org)

### Enable Weather Data
```
WEATHER_API_KEY=your-key
```
**Free tier**: [openweathermap.org](https://openweathermap.org/api)

### Enable Authentication
```
ENABLE_AUTH=true
ADMIN_PASSWORD_HASH=your-sha256-hash
```
**Generate hash**:
```bash
echo -n "yourpassword" | sha256sum
```

---

## 📊 Sample Data Included

Three ready-to-use CSV files:

1. **sample_maintenance.csv** - 15 maintenance records
2. **sample_safety_incidents.csv** - 12 safety incidents
3. **sample_flights.csv** - 20 flight operations

**To import**: CSV Upload → Select table → Upload file → Map columns → Import

---

## 🎯 Common Tasks

### View All Maintenance Records
1. Sidebar → "🗂️ Data Management"
2. Select "maintenance"
3. Filter, sort, export

### Create Weekly Report
1. Sidebar → "📊 Reports"
2. Tab: "📅 Scheduled Reports"
3. Choose "Weekly" period
4. Select format (PDF/Excel/CSV)
5. Generate & Download

### Query with Natural Language
1. Sidebar → "💬 NL/AI Query"
2. Type question: "Show me all high priority maintenance"
3. View results
4. Download as needed

### Get AI Insights
1. Sidebar → "💬 NL/AI Query"
2. Scroll to "🤖 AI Analysis Assistant"
3. Type: "Analyze maintenance trends"
4. Select analysis type
5. Click "Analyze"

---

## 🆘 Troubleshooting

### App won't start locally
```bash
# Update pip and reinstall
pip install --upgrade pip
pip install -r requirements.txt
```

### No demo data showing
- Refresh the page (browser refresh)
- Check "Dashboard" page is selected
- Demo data auto-loads on first visit

### CSV upload fails
- Check CSV format matches samples
- Ensure required columns are present
- Map all required fields (marked with *)

### Database errors
- **Supabase**: Verify URL and KEY are correct
- **SQLite**: Delete `pia_operations.db` and restart
- Check logs in terminal

### Features not working
- **AI Query**: Need OPENAI_API_KEY
- **Live Flights**: Need OpenSky credentials
- **Weather**: Need Weather API key

---

## 📚 Next Steps

Once you're comfortable:

1. **Read Full Documentation**: `README.md`
2. **Deployment Guide**: `DEPLOYMENT.md`
3. **Customize**: Edit `streamlit_app.py`
4. **Add Features**: System is modular
5. **Scale**: Move to production database

---

## 💡 Pro Tips

### Keyboard Shortcuts
- `R` - Rerun app
- `C` - Clear cache
- `S` - Open settings

### Best Practices
- Import demo data first to understand structure
- Use filters in Data Management for large datasets
- Generate reports regularly for trend analysis
- Enable authentication before sharing publicly

### Performance
- SQLite: Good for < 10K records
- Supabase: Scales to millions
- Add indexes for large datasets

---

## 🎨 Customization

### Change Colors
Edit `Config` class in `streamlit_app.py`:
```python
PRIMARY_COLOR = "#006C35"  # Your color
ACCENT_COLOR = "#C8102E"   # Your color
```

### Add Logo
Replace placeholder in sidebar:
```python
st.image("path/to/your/logo.png")
```

### Modify Forms
Edit `page_forms()` function to add/remove fields

---

## 📞 Support

**Having issues?**
1. Check `README.md` for detailed help
2. Review logs in terminal
3. Verify environment variables
4. Try SQLite mode (no external DB)

**Everything working?**
Great! Start customizing and scaling your system.

---

## ✅ Quick Checklist

- [ ] App running (cloud or local)
- [ ] Dashboard loads with demo data
- [ ] Submitted a test form
- [ ] Imported sample CSV
- [ ] Ran a natural language query
- [ ] Generated a report
- [ ] (Optional) Configured API keys
- [ ] (Optional) Enabled authentication

**All checked?** You're ready to go! 🚀

---

## 🌟 What's Next?

### Immediate
- Replace demo data with real operations data
- Configure API keys for enhanced features
- Set up scheduled reports

### Short Term
- Train team on the system
- Establish data entry workflows
- Monitor system analytics

### Long Term
- Scale database as needed
- Add custom integrations
- Implement advanced ML models

---

**Need More Help?**
- 📖 Full docs: `README.md`
- 🚀 Deployment: `DEPLOYMENT.md`
- 📧 Support: Open GitHub issue

**Happy Operating! ✈️**

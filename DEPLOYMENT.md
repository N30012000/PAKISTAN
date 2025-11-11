# 🚀 Quick Deployment Guide - PIA Operations

## Pre-Deployment Checklist

- [ ] All code files in place
- [ ] `requirements.txt` present
- [ ] `.env.example` copied to `.env` (for local) or secrets configured (for cloud)
- [ ] Supabase project created (or other DB ready)
- [ ] Git repository initialized

## 1. Streamlit Cloud (Fastest & FREE)

### Setup Time: 5 minutes

1. **Prepare Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial PIA Operations deployment"
   git remote add origin https://github.com/yourusername/pia-operations.git
   git push -u origin main
   ```

2. **Deploy**
   - Go to https://share.streamlit.io
   - Click "New app"
   - Select your repository
   - Main file: `streamlit_app.py`
   - Click "Deploy"

3. **Configure Secrets**
   In Streamlit Cloud dashboard → Settings → Secrets:
   ```toml
   SUPABASE_URL = "https://xxxxx.supabase.co"
   SUPABASE_KEY = "your-key"
   OPENAI_API_KEY = "sk-..."
   ENABLE_AUTH = "false"
   APP_MODE = "production"
   ```

4. **Done!** Your app is live at `https://yourapp.streamlit.app`

---

## 2. Render.com (Alternative FREE option)

### Setup Time: 10 minutes

1. **Create Account** at https://render.com

2. **New Web Service**
   - Connect GitHub repository
   - Name: `pia-operations`
   - Environment: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`

3. **Environment Variables**
   Add in Render dashboard:
   ```
   PYTHON_VERSION = 3.9.0
   SUPABASE_URL = your-supabase-url
   SUPABASE_KEY = your-key
   APP_MODE = production
   ```

4. **Deploy** - Render will auto-deploy from GitHub

---

## 3. Heroku (Traditional FREE tier)

### Setup Time: 10 minutes

1. **Install Heroku CLI**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Windows
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login & Create App**
   ```bash
   heroku login
   heroku create pia-operations
   ```

3. **Set Environment Variables**
   ```bash
   heroku config:set SUPABASE_URL=your-url
   heroku config:set SUPABASE_KEY=your-key
   heroku config:set APP_MODE=production
   ```

4. **Deploy**
   ```bash
   git push heroku main
   heroku open
   ```

---

## 4. Docker (Self-Hosted or Cloud)

### For any VPS, AWS, GCP, Azure, DigitalOcean

1. **Build Image**
   ```bash
   docker build -t pia-operations .
   ```

2. **Run Container**
   ```bash
   docker run -d \
     -p 8501:8501 \
     -e SUPABASE_URL=your-url \
     -e SUPABASE_KEY=your-key \
     -e APP_MODE=production \
     --name pia-ops \
     pia-operations
   ```

3. **Access** at `http://your-server-ip:8501`

---

## Database Setup - Supabase (Recommended)

### Setup Time: 5 minutes

1. **Create Project**
   - Go to https://supabase.com
   - Click "New project"
   - Name: `pia-operations`
   - Database password: (choose strong password)
   - Region: Select closest to your users

2. **Get Credentials**
   - Project Settings → API
   - Copy `URL` and `anon public` key

3. **Tables Auto-Created**
   - App creates tables on first run
   - Or run SQL from README if preferred

4. **Verify**
   - Go to Table Editor in Supabase
   - You should see: `maintenance`, `safety_incidents`, `flights`

---

## Testing Deployment

### 1. Health Check
- Visit your deployed URL
- Should see PIA Operations header
- Dashboard should load

### 2. Demo Data
- Dashboard auto-loads demo data if empty
- Check KPI cards show numbers

### 3. Features Test
- [ ] Dashboard loads
- [ ] Forms submit successfully
- [ ] CSV upload works
- [ ] Data management shows records
- [ ] NL Query responds
- [ ] Reports generate

### 4. API Integration Test (if keys configured)
- [ ] OpenSky flight data fetches
- [ ] Weather API responds
- [ ] AI query works (OpenAI)

---

## Troubleshooting

### App won't start
```bash
# Check logs
streamlit run streamlit_app.py --logger.level=debug

# Verify dependencies
pip install -r requirements.txt --upgrade
```

### Database connection fails
```bash
# Test Supabase connection
curl https://your-project.supabase.co/rest/v1/
# Should return 404 (means API is reachable)

# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_KEY
```

### Demo data not loading
- Check database is empty: Dashboard → Data Management
- Manually trigger: Delete `pia_operations.db` (SQLite) or truncate tables (Supabase)
- Restart app

---

## Performance Optimization

### For Production with Real Data

1. **Database Indexing**
   ```sql
   CREATE INDEX idx_aircraft ON maintenance(aircraft_registration);
   CREATE INDEX idx_date ON flights(scheduled_departure);
   CREATE INDEX idx_severity ON safety_incidents(severity);
   ```

2. **Caching**
   App uses `@st.cache_resource` for database
   Clear cache: Streamlit menu → Clear cache

3. **Rate Limiting**
   - OpenSky: Max 400/day free
   - OpenWeather: Max 1000/day free
   - OpenAI: Set billing limits

---

## Security Checklist

- [ ] `.env` not committed to Git
- [ ] Strong database password
- [ ] Supabase RLS enabled (optional)
- [ ] Admin password hash changed
- [ ] API keys rotated periodically
- [ ] HTTPS enabled (auto on Streamlit/Render/Heroku)
- [ ] Secrets stored in platform secrets manager

---

## Monitoring

### Streamlit Cloud
- Dashboard → Logs
- Real-time viewer
- Download logs

### Render/Heroku
```bash
# Render
render logs -a pia-operations --tail

# Heroku
heroku logs --tail -a pia-operations
```

### Docker
```bash
docker logs -f pia-ops
```

---

## Scaling

### Free Tier Limits
- **Streamlit Cloud**: Unlimited public apps
- **Render**: 750 hours/month (always-on = 1 app)
- **Heroku**: 550 hours/month free dyno
- **Supabase**: 500MB DB, 2GB bandwidth

### When to Upgrade
- More than 100 concurrent users → Upgrade hosting
- More than 10K records/table → Optimize queries, add indexes
- Heavy API usage → Consider caching layer

---

## Backup & Recovery

### Automated Backups (Supabase)
- Settings → Database → Backups
- Daily backups on free tier
- Point-in-time recovery on paid tiers

### Manual Export
```bash
# From app: Reports → Export All Data → CSV
# Or use Supabase dashboard → Table Editor → Export
```

---

## Support

- **GitHub Issues**: Report bugs
- **Streamlit Forums**: General questions
- **Supabase Discord**: Database questions

---

## Quick Commands Reference

```bash
# Local development
streamlit run streamlit_app.py

# Check requirements
pip list | grep -E 'streamlit|pandas|plotly|supabase'

# Test database connection
python -c "from supabase import create_client; print('OK')"

# Generate password hash
echo -n "mypassword" | sha256sum

# Docker quick start
docker build -t pia-ops . && docker run -p 8501:8501 pia-ops

# Git deploy
git add . && git commit -m "Update" && git push origin main
```

---

**Deployment Complete! 🎉**

Your PIA Operations system is now live and ready to manage airline operations efficiently.

# Deployment Guide

Complete guide for deploying the Swimming Schedule Converter to various platforms.

---

## 📋 Prerequisites

- GitHub account
- Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- Your fork of this repository

---

## 🚀 Option 1: Streamlit Community Cloud (FREE)

**Best for**: Personal use, small teams, quick deployment  
**Cost**: 100% FREE  
**Time**: ~5 minutes

### Step 1: Prepare Repository

**1a. Create GitHub repository**
```bash
# Go to github.com and create a new repository
# Name: swimming-schedule-converter (or any name you like)
# Make it Public or Private (both work)
```

**1b. Push your code**
```bash
# In your project folder
git remote add origin https://github.com/YOUR-USERNAME/swimming-schedule-converter.git
git branch -M main
git push -u origin main
```

**Important**: Your `.env` file is gitignored, so your API key is NOT uploaded ✅

### Step 2: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"Sign in with GitHub"**
3. Click **"New app"**
4. Fill in the form:
   - **Repository**: Select your repo
   - **Branch**: `main`
   - **Main file path**: `app.py`

5. Click **"Advanced settings"** → **Secrets** section:
```toml
GEMINI_API_KEY = "paste-your-actual-api-key-here"
```

6. Click **"Deploy"**

Your app will be live at: `https://swimming-schedule-converter-xxx.streamlit.app`

### 🔐 Password Protection (Optional)

To secure your public URL:

**Add to Streamlit Secrets:**
```toml
GEMINI_API_KEY = "your-actual-api-key-here"
APP_PASSWORD = "your-secure-password-here"
```

**Benefits:**
- ✅ Public URL is safe to share
- ✅ FREE (no Pro subscription needed)
- ✅ Protects your API quota
- ✅ Easy to change password

**Testing locally:**
Add to `.streamlit/secrets.toml`:
```toml
APP_PASSWORD = "test123"
```

---

## 🐧 Option 2: Linux Server Deployment

**Best for**: Organizations, custom infrastructure, full control

### Prerequisites
- Linux server with Python 3.10+
- Git installed
- SSH access

### Method A: Git Clone (Recommended)

**Step 1: Push to GitHub**
```bash
# Verify secrets are gitignored
git check-ignore .env  # Should output: .env

# Push code
git add .
git commit -m "Deploy to Linux"
git push origin main
```

**Step 2: Clone on Linux**
```bash
ssh user@your-server
git clone https://github.com/yourusername/swimming-schedule-converter.git
cd swimming-schedule-converter
```

**Step 3: Transfer API Key Securely**

**Option A - SCP (Best):**
```bash
# From Windows
scp .env user@your-server:~/swimming-schedule-converter/.env
```

**Option B - Manual:**
```bash
# On server
nano .env
# Add: GEMINI_API_KEY=your-key-here
chmod 600 .env
```

**Step 4: Setup Environment**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test
python tests/test_api.py
```

**Step 5: Run App**
```bash
# Development mode
streamlit run app.py --server.address 0.0.0.0 --server.port 8501

# Production with systemd
sudo nano /etc/systemd/system/swim-calendar.service
```

**Systemd Service File:**
```ini
[Unit]
Description=Swimming Calendar Converter
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/swimming-schedule-converter
Environment="PATH=/home/youruser/swimming-schedule-converter/venv/bin"
ExecStart=/home/youruser/swimming-schedule-converter/venv/bin/streamlit run app.py --server.address 0.0.0.0 --server.port 8501
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable swim-calendar
sudo systemctl start swim-calendar
sudo systemctl status swim-calendar
```

### Method B: Docker Deployment

**Build image:**
```bash
docker build -t swim-calendar .
```

**Run container:**
```bash
docker run -p 8501:8501 \
  -e GEMINI_API_KEY=your-key-here \
  swim-calendar
```

---

## 🔒 Security Guide

### API Key Protection

**Local Development:**
- ✅ API key in `.env` file (gitignored)
- ✅ Plain text is industry standard for local dev
- ✅ Protected by OS user account permissions

**Production:**
- ✅ Environment variables or systemd secrets
- ✅ File permissions: `chmod 600 .env`
- ✅ Never log or display API keys

**Risk Assessment:**
- ⚠️ Low-Medium risk for local development
- ✅ Safe from network attacks (localhost binding)
- ✅ Safe from git leaks (gitignored)
- ❌ Vulnerable to local malware/physical access

### Network Security

**Local Development:**
```bash
# Secure (localhost only)
streamlit run app.py --server.address 127.0.0.1

# Network accessible (use with caution)
streamlit run app.py --server.address 0.0.0.0
```

**Production Recommendations:**
- Use reverse proxy (nginx) with SSL
- Enable firewall rules
- Consider VPN for internal access
- Regular security updates

### If API Key Compromised

1. **Immediately disable key** at [Google AI Studio](https://aistudio.google.com/app/apikey)
2. **Generate new key**
3. **Update all deployments**
4. **Review usage logs** for unauthorized requests
5. **Rotate password** if using password protection

---

## 📊 Cost & Performance

### Streamlit Cloud (FREE)
✅ **Included:**
- Unlimited app usage
- Auto-deployments from GitHub
- HTTPS & custom URLs
- 1GB RAM, 1 CPU core

⚠️ **Limitations:**
- App sleeps after inactivity (~10 min)
- 3 apps maximum per account
- Community support only

💰 **Streamlit Cloud Pro ($20/month):**
- Always-on apps
- Unlimited apps
- Priority support
- More resources

### Self-Hosted Costs
- **VPS**: $5-20/month (DigitalOcean, Linode)
- **Domain**: $10-15/year (optional)
- **SSL**: Free (Let's Encrypt)

---

## 🐛 Troubleshooting

### Common Issues

**❌ "API key not valid"**
```bash
# Test API key
python tests/test_api.py

# Restart Streamlit
# Ctrl+C → streamlit run app.py
```

**❌ "App is sleeping" (Streamlit Cloud)**
- Visit URL again to wake up (10 seconds)
- Consider upgrading to Pro for always-on

**❌ "Can't connect to app"**
- Check firewall settings
- Verify port 8501 is open
- Confirm app is running: `ps aux | grep streamlit`

**❌ Deployment fails**
```bash
# Check logs
sudo journalctl -u swim-calendar -f

# Verify dependencies
pip list
pip install -r requirements.txt --force-reinstall
```

### Getting Help

1. **Check logs** first (systemd, Docker, Streamlit Cloud)
2. **Test API key** independently
3. **Verify network connectivity**
4. **Review deployment steps**

---

## 📝 Updates & Maintenance

### Updating Deployed App

**Streamlit Cloud:**
```bash
git add .
git commit -m "Update feature"
git push
# Auto-deploys in ~1 minute
```

**Linux Server:**
```bash
ssh user@server
cd swimming-schedule-converter
git pull
sudo systemctl restart swim-calendar
```

**Change API Key:**
- Streamlit Cloud: Settings → Secrets
- Linux: Update `.env` → restart service
- Docker: Update environment variable

### Monitoring

**Health Checks:**
```bash
# Test endpoint
curl http://localhost:8501/_stcore/health

# Check service
sudo systemctl status swim-calendar
```

**Log Monitoring:**
```bash
# Real-time logs
sudo journalctl -u swim-calendar -f

# Recent errors
sudo journalctl -u swim-calendar --since "1 hour ago" -p err
```

**Best for**: Personal use, small teams, quick deployment  
**Cost**: 100% FREE  
**Time**: ~5 minutes

### Complete Step-by-Step Guide:

#### Step 1: Prepare Your Repository

**1a. Create GitHub repository**
```bash
# Go to github.com and create a new repository
# Name: swimming-schedule-converter (or any name you like)
# Make it Public or Private (both work)
# Don't initialize with README (we already have one)
```

**1b. Push your code to GitHub**
```bash
# In your project folder (D:\code\calendar_import)
git remote add origin https://github.com/YOUR-USERNAME/swimming-schedule-converter.git
git branch -M main
git push -u origin main
```

**Important**: Your `.env` file is gitignored, so your API key is NOT uploaded to GitHub ✅

---

#### Step 2: Deploy to Streamlit Cloud

**2a. Sign in to Streamlit**
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"Sign in with GitHub"**
3. Authorize Streamlit to access your GitHub repositories

**2b. Create New App**
1. Click **"New app"** (big button in top right)
2. Fill in the form:
   - **Repository**: Select your `swimming-schedule-converter` repo
   - **Branch**: `main`
   - **Main file path**: `app.py`
   
3. Click **"Advanced settings"** (bottom left)

**2c. Configure Secrets (CRITICAL STEP)**
In the **Secrets** section, add this **EXACT** format:
```toml
GEMINI_API_KEY = "paste-your-actual-api-key-here"
```

⚠️ **Important**:
- Replace with YOUR actual API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- Keep the quotes around the key
- Use `.toml` format (not JSON)
- Name must be EXACTLY `GEMINI_API_KEY`

**2d. Deploy!**
1. Click **"Deploy"** button
2. Wait 2-3 minutes while Streamlit builds your app
3. Your app will be live at: `https://swimming-schedule-converter-xxx.streamlit.app`

---

#### Step 3: Share with Your Team

Your app URL will look like:
```
https://swimming-schedule-converter-abc123.streamlit.app
```

Share this URL with anyone! They can:
- ✅ Use the app without API key
- ✅ Access from any device (phone, tablet, computer)
- ✅ Use on any network (not just local WiFi)
- ❌ Cannot see your API key (it's hidden in secrets)

---

### Managing Your Deployment

**Update the app**:
```bash
# Make changes locally
git add .
git commit -m "Update feature"
git push

# Streamlit Cloud auto-deploys in ~1 minute ✅
```

**Change API key**:
1. Go to your app on [share.streamlit.io](https://share.streamlit.io)
2. Click **⚙️ Settings** → **Secrets**
3. Update `GEMINI_API_KEY` value
4. Click **Save**
5. App restarts automatically

**View logs** (if errors occur):
1. Click **"Manage app"** on your app page
2. Click **"Logs"** tab
3. See real-time errors and debugging info

**Delete app**:
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **⋮** (three dots) on your app
3. Select **"Delete"**

---

### Troubleshooting Deployment

**❌ Error: "GEMINI_API_KEY not found"**
- Go to Settings → Secrets
- Verify format is: `GEMINI_API_KEY = "your-key"`
- Check for typos in variable name
- Make sure quotes are present

**❌ Error: "Invalid API key"**
- Get new key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- Update in Streamlit secrets
- Wait for app to restart

**❌ App is slow to load**
- First load takes ~30 seconds (free tier)
- Subsequent loads are faster
- Consider upgrading to Streamlit Cloud Pro ($20/month) for better performance

**❌ App shows "Sleeping"**
- Free tier apps sleep after inactivity
- Just visit the URL again to wake it up
- Takes ~10 seconds to restart

---

### Cost & Limits (FREE Tier)

✅ **Included FREE**:
- Unlimited app usage
- Auto-deployments from GitHub
- HTTPS & custom URLs
- Community support

⚠️ **Limits**:
- 1 GB RAM (plenty for this app)
- 1 CPU core (sufficient)
- App sleeps after inactivity
- 3 apps maximum per account

💰 **If you need more**:
- Streamlit Cloud Pro: $20/month
- Unlimited apps, always-on, more resources

---

### Security on Streamlit Cloud

✅ **What's secure**:
- API key stored as secret (encrypted)
- HTTPS by default
- Not visible in logs or UI
- Isolated from other apps

⚠️ **What to know**:
- App is public by default (anyone with URL can use it)
- Can't restrict by IP address on free tier
- Usage counts against YOUR API key quota (1500 free/day)

---

### 🔐 Securing Your App with Password Protection (FREE)

This app includes a **built-in password gatekeeper** that works on Streamlit Cloud's free tier!

#### How It Works

1. **Without password set**: App runs normally (great for local development)
2. **With password set**: Users must enter correct password to access the app

#### Setting Up Password Protection

**Step 1: Add password to Streamlit Secrets**

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Find your app → Click **⚙️ Settings** → **Secrets**
3. Add the following line:

```toml
GEMINI_API_KEY = "your-actual-api-key-here"
APP_PASSWORD = "your-secure-password-here"
```

4. Click **Save** - app will restart automatically

**Step 2: Share with authorized users**

Now when anyone visits your app URL:
- They see a login screen in the sidebar
- They must enter the correct password
- Without the password, they cannot access the app

#### Benefits

✅ **Public URL is now safe to share** - strangers can't get past the login screen  
✅ **No cost** - works on free tier (no Pro subscription needed)  
✅ **Easy to change** - just update the secret and app restarts  
✅ **Protects your API quota** - only authorized users consume your Gemini credits  

#### Testing Locally

To test password protection locally:

1. Create `.streamlit/secrets.toml` (this file is gitignored):
```toml
GEMINI_API_KEY = "your-local-api-key"
APP_PASSWORD = "test123"
```

2. Run the app - you'll see the password prompt
3. Enter `test123` to access

**Tip**: Remove `APP_PASSWORD` from local secrets to disable the password during development.

#### Security Notes

⚠️ **Choose a strong password**:
- At least 12 characters
- Mix of letters, numbers, symbols
- Don't reuse passwords from other accounts

⚠️ **Share password securely**:
- Don't email it in plain text
- Use encrypted messaging (Signal, WhatsApp)
- Tell team members in person

---

## Option 2: Docker (Any Cloud Provider)

**Best for**: Organizations, custom infrastructure, full control

### Build Image:

```bash
# Build
docker build -t swim-calendar .

# Run locally
docker run -p 8501:8501 \
  -e GEMINI_API_KEY=your-key-here \
  swim-calendar

# Test at http://localhost:8501
```

### Push to Docker Hub:

```bash
# Tag
docker tag swim-calendar your-username/swim-calendar:latest

# Push
docker push your-username/swim-calendar:latest
```

### Deploy to Any Cloud:
- AWS ECS
- Google Cloud Run
- Azure Container Instances
- DigitalOcean App Platform

---

## Option 3: Render.com (FREE Tier Available)

**Best for**: Easy deployment with persistent disk

### Steps:

1. **Create `render.yaml`** (already included):
   ```yaml
   services:
     - type: web
       name: swim-calendar
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: streamlit run app.py
       envVars:
         - key: GEMINI_API_KEY
           sync: false
   ```

2. **Connect Repository**
   - Go to [render.com](https://render.com)
   - Click "New +"
   - Select "Blueprint"
   - Connect your GitHub repository

3. **Add Environment Variable**
   - In dashboard, add `GEMINI_API_KEY`

4. **Deploy**
   - Render auto-deploys on push
   - Free tier available

---

## Option 4: Railway (Simple & Fast)

**Best for**: Quick deployment with Git integration

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize
railway init

# Add environment variable
railway variables set GEMINI_API_KEY=your-key-here

# Deploy
railway up
```

---

## Option 5: Fly.io (Global Edge Deployment)

**Best for**: Low latency globally

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Launch app
fly launch

# Set secret
fly secrets set GEMINI_API_KEY=your-key-here

# Deploy
fly deploy
```

---

## Environment Variables

All deployments need these environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Your Gemini API key |

---

## Configuration Persistence

The app saves configuration to `config.json`. For cloud deployments:

### Streamlit Cloud:
- Automatically persisted in app storage

### Docker:
- Mount a volume:
  ```bash
  docker run -v $(pwd)/data:/app \
    -e GEMINI_API_KEY=your-key \
    swim-calendar
  ```

### Render/Railway/Fly:
- Use persistent disk/volume features

---

## Custom Domain

### Streamlit Cloud:
- Settings → Custom domain
- Add CNAME record

### Render:
- Settings → Custom domain

### Others:
- Follow platform-specific instructions

---

## Monitoring

### Health Checks:

```bash
# Check if app is running
curl https://your-app-url/_stcore/health
```

### Logs:

- **Streamlit Cloud**: Dashboard → Logs
- **Render**: Dashboard → Logs
- **Docker**: `docker logs <container-id>`

---

## Scaling

### Streamlit Cloud:
- Limited to 1 instance
- Good for <1000 users/month

### Docker-based:
- Horizontal scaling with load balancer
- Auto-scaling based on CPU/memory

---

## Security Checklist

- ✅ API key stored as environment variable (never in code)
- ✅ `.env` in `.gitignore`
- ✅ HTTPS enabled (automatic on most platforms)
- ✅ No user data persistence
- ✅ All processing server-side

---

## Cost Estimates

| Platform | Free Tier | Paid |
|----------|-----------|------|
| Streamlit Cloud | 1 app | Unlimited from $20/mo |
| Render | 750 hrs/mo | From $7/mo |
| Railway | $5 credit/mo | Pay as you go |
| Fly.io | 3 VMs | From $1.94/mo |
| Docker (self-hosted) | Free | Infrastructure cost |

---

## Troubleshooting

**App not starting**:
- Check environment variables are set
- Check logs for errors
- Verify `requirements.txt` is installed

**Slow performance**:
- Gemini API has rate limits
- Consider caching results
- Use faster deployment region

**Configuration not saving**:
- Check persistent storage is configured
- Verify write permissions

---

## Support

- **Issues**: [GitHub Issues](your-repo-url/issues)
- **Discussions**: [GitHub Discussions](your-repo-url/discussions)
- **Email**: your-email@example.com

---

**Happy Deploying! 🚀**

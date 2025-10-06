# 🚀 Google Drive Migration Guide - APC Gym Log System

This guide will help you move your gymlog project to a new computer via Google Drive with minimal setup required.

## 📋 What You Need on the New Computer

Before moving, ensure the new computer has:
- **Python 3.8+** ([Download here](https://python.org))
- **Node.js 16+** ([Download here](https://nodejs.org))
- **Git** (optional, but recommended - [Download here](https://git-scm.com))

## 🎯 Migration Strategy

### Step 1: Prepare for Upload to Google Drive

#### Files to EXCLUDE from Google Drive (Create .gdriveignore mentally):
```
# Don't upload these folders/files:
node_modules/          # Will be recreated with npm install
gym_app/__pycache__/   # Python cache files
gymlog_backend/__pycache__/  # Python cache files
**/__pycache__/        # All Python cache directories
*.pyc                  # Python compiled files
.git/                  # Git repository data (if exists)
venv/                  # Virtual environment (if exists)
env/                   # Virtual environment (if exists)
.vscode/              # Editor settings (optional)
.idea/                # Editor settings (optional)
```

#### Files to INCLUDE (Essential):
```
✅ All source code files (.py, .jsx, .js, .css, .html)
✅ Configuration files (package.json, requirements.txt, vite.config.js, etc.)
✅ Database file (db.sqlite3) - Contains all your data!
✅ Documentation (README.md, SETUP.md)
✅ Scripts (start-dev.py, create_admin.py, etc.)
✅ Migration files (gym_app/migrations/*.py)
✅ RFID_stuff/ folder (if using RFID features)
✅ OLD_LOGS/ folder (historical data)
```

### Step 2: Upload to Google Drive

1. **Create a folder** in Google Drive called `gymlogv2-backup`
2. **Upload ONLY the essential files** (avoid node_modules and __pycache__ folders)
3. **Verify the upload** - should be around 5-10 MB max (not hundreds of MB)

### Step 3: Download on New Computer

1. **Download** the folder from Google Drive
2. **Extract** to your desired location (e.g., `C:\Projects\gymlogv2\`)
3. **Open terminal/command prompt** in the project folder

### Step 4: Quick Setup on New Computer

#### Option A: Automated Setup (Easiest) ⭐
```bash
# Navigate to the project folder
cd path\to\gymlogv2

# Run the comprehensive setup script
python quick-setup.py
```
This script will:
- ✅ Check system requirements (Python 3.8+, Node.js 16+)
- ✅ Verify all project files are present
- ✅ Install all dependencies automatically
- ✅ Set up the database
- ✅ Verify the installation works
- ✅ Provide next steps

#### Option B: Simple Setup (Minimal)
```bash
# For users who prefer a basic approach
python simple-setup.py
```

#### Option C: Windows Double-Click (Easiest for Windows)
```bash
# Just double-click the batch file
setup.bat
```

#### Option D: Manual Setup (Traditional)
```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Node.js dependencies  
npm install

# 3. Set up database
python manage.py migrate

# 4. Start both servers
python start-dev.py
```

## 🔧 Important Notes

### Database Considerations
- **db.sqlite3 file**: This contains ALL your student data, gym logs, and admin accounts
- **Include this file** in your Google Drive upload
- **No additional setup needed** - the database will work immediately on the new computer

### Secret Keys & Security
- The current setup uses a development SECRET_KEY in `settings.py`
- **For production**: Consider using environment variables
- **For development**: The current setup will work fine as-is

### File Size Optimization
Your project should be **small** for Google Drive transfer:
- **Without node_modules**: ~5-10 MB
- **With node_modules**: ~200+ MB (avoid uploading this!)

### Port Configuration
The project is configured to run on:
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:5173
- These ports are already configured in the CORS settings

## 🚀 Quick Start Commands (New Computer)

After downloading from Google Drive:

```bash
# Option 1: Automated setup (Recommended)
python quick-setup.py

# Option 2: Simple setup
python simple-setup.py

# Option 3: Windows double-click (Easiest for Windows users)
# Just double-click setup.bat

# Option 4: One-command manual setup
pip install -r requirements.txt && npm install && python manage.py migrate && python start-dev.py
```

## ✅ Verification Checklist

After setup on the new computer, verify:

- [ ] Backend starts without errors: `http://localhost:8000/api/`
- [ ] Frontend loads properly: `http://localhost:5173`
- [ ] Database data is intact (check admin panel: `http://localhost:8000/admin`)
- [ ] Student registration works
- [ ] Gym check-in/check-out functions work
- [ ] Statistics page displays correctly

## 🐛 Troubleshooting

### Common Issues & Solutions:

**"Module not found" errors:**
```bash
# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Then install dependencies
pip install -r requirements.txt
```

**"npm install" fails:**
```bash
# Clear npm cache and try again
npm cache clean --force
npm install
```

**Database errors:**
```bash
# If migrations fail, try:
python manage.py migrate --run-syncdb
```

**Port conflicts:**
```bash
# If ports are in use, change them:
python manage.py runserver 8001  # Backend on different port
# Frontend will auto-suggest alternative port
```

## 📦 Alternative: Create a Portable Package

If you want to make migration even easier, create a setup script:

```python
# quick-setup.py
import subprocess
import sys
import os

def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("🚀 Setting up APC Gym Log System...")
    
    # Install Python dependencies
    print("📦 Installing Python dependencies...")
    if not run_command("pip install -r requirements.txt"):
        print("❌ Failed to install Python dependencies")
        return
    
    # Install Node dependencies
    print("📦 Installing Node.js dependencies...")
    if not run_command("npm install"):
        print("❌ Failed to install Node.js dependencies")
        return
    
    # Run migrations
    print("🔄 Setting up database...")
    if not run_command("python manage.py migrate"):
        print("❌ Failed to set up database")
        return
    
    print("✅ Setup complete! Run 'python start-dev.py' to start the system.")

if __name__ == "__main__":
    main()
```

## 🎉 Final Notes

This migration approach ensures:
- ✅ **Minimal file size** for Google Drive transfer
- ✅ **All data preserved** (including student records)
- ✅ **Quick setup** on new computer (5-10 minutes)
- ✅ **No configuration changes** needed
- ✅ **Database integrity** maintained

The system is designed to be portable and will work on any computer with Python 3.8+ and Node.js 16+ installed.

---

**Happy Migration! 🚀**

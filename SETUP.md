# 🚀 Quick Setup Guide - APC Gym Log System

This guide will help you get the APC Gym Log System running in just a few minutes!

## 📋 Prerequisites

Before you start, make sure you have:
- **Python 3.8+** installed ([Download here](https://python.org))
- **Node.js 16+** installed ([Download here](https://nodejs.org))
- **Git** installed ([Download here](https://git-scm.com))

## ⚡ Quick Start (3 Steps)

### Step 1: Clone & Navigate
```bash
git clone <repository-url>
cd gymlogv2
```

### Step 2: Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies  
npm install
```

### Step 3: Start Development Servers
```bash
# Option A: Use the automatic starter script
python start-dev.py

# Option B: Start manually (in separate terminals)
# Terminal 1 - Backend
python manage.py migrate
python manage.py runserver

# Terminal 2 - Frontend  
npm run dev
```

## 🎉 You're Ready!

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api
- **Admin Panel**: http://localhost:8000/admin

## 🎯 Test the System

### Create Sample Data (Optional)
```bash
python scripts/dev-setup.py
```

This creates sample students you can use for testing:
- Student ID: `2023-123456` (Juan Dela Cruz)
- Student ID: `2023-234567` (Maria Santos)  
- Student ID: `2023-345678` (Jose Rizal)
- And more...

### Try These Features
1. **Register a new student** at `/register`
2. **Login with Student ID** on the home page
3. **Check in/out** of the gym
4. **View statistics** with the heatmap

## 🔧 Development Commands

```bash
# Backend Commands
python manage.py migrate          # Run database migrations
python manage.py createsuperuser  # Create admin account
python manage.py runserver        # Start Django server

# Frontend Commands  
npm run dev                       # Start development server
npm run build                     # Build for production
npm run preview                   # Preview production build

# Utility Scripts
python scripts/dev-setup.py       # Create sample data
python start-dev.py               # Start both servers
```

## 📱 Usage Flow

### For New Students
1. Go to "Register" page
2. Fill out student information
3. Return to home page and enter Student ID
4. Start using the gym!

### For Existing Students  
1. Enter Student ID on home page
2. Click "Check In to Gym" to start session
3. Click "Check Out" when done
4. View your stats and progress!

## 🐛 Troubleshooting

### Common Issues

**"Module not found" errors**
```bash
# Make sure virtual environment is activated (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Then reinstall dependencies
pip install -r requirements.txt
```

**Port already in use**
- Backend: Change port with `python manage.py runserver 8001`
- Frontend: Vite will automatically suggest alternative port

**Database errors**
```bash
# Reset database (⚠️ This deletes all data)
del db.sqlite3  # Windows
rm db.sqlite3   # macOS/Linux
python manage.py migrate
```

**CORS errors in browser**
- Make sure both servers are running
- Check that frontend is accessing `http://localhost:8000/api`

## 📚 Project Structure Overview

```
gymlogv2/
├── 🐍 Backend (Django)
│   ├── gymlog_backend/     # Project settings
│   └── gym_app/            # Main application
├── ⚛️ Frontend (React)  
│   └── src/
│       ├── components/     # Reusable components
│       ├── pages/          # Page components
│       └── services/       # API communication
├── 📜 Scripts
│   ├── dev-setup.py        # Create sample data
│   └── start-dev.py        # Start both servers
└── 📖 Documentation
    ├── README.md           # Full documentation
    └── SETUP.md           # This file
```

## 🎨 Key Features

- ✅ **Student Registration** with ID validation
- ✅ **Real-time Gym Timer** with 2-hour daily limit  
- ✅ **Progress Tracking** with GitHub-style heatmap
- ✅ **Beautiful UI** with Tailwind CSS
- ✅ **Mobile Responsive** design
- ✅ **Admin Interface** for management

## 🔮 Next Steps

After getting familiar with the system:
1. **Customize** the design to match school branding
2. **Add** more features from the roadmap
3. **Deploy** to production environment  
4. **Integrate** with NFC hardware for ID tapping

## 💡 Tips

- Use the **admin panel** to view all data and manage students
- Check the **browser console** for detailed error messages
- The **heatmap** becomes more interesting with more historical data
- **Sample data** helps demonstrate all features

## 🆘 Need Help?

- 📖 Check the full [README.md](README.md) for detailed documentation
- 🐛 Look at browser console for error messages
- 💬 Contact the development team for support

---

**Happy Coding! 🚀**

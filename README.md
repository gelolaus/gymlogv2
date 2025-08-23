# APC Gym Log System

A comprehensive gym management system designed for Asia Pacific College, enabling students to track their gym sessions, monitor progress, and maintain fitness goals through an intuitive web interface.

## 🎯 Project Overview

The APC Gym Log System is a modern web application that allows students to:
- Register for gym access using their student credentials
- Check in/out of the gym with a simple ID-based system
- Track daily gym time with a 2-hour daily limit
- View comprehensive statistics and activity heatmaps
- Monitor progress with GitHub-style contribution graphs

## 🏗️ Architecture

### Backend (Django + Django REST Framework)
- **Python 3.8+** with Django 4.2.7
- **SQLite Database** for data persistence
- **RESTful API** endpoints for all operations
- **Comprehensive data models** for students, gym sessions, and statistics

### Frontend (React + Vite)
- **React 18** with modern hooks and functional components
- **Tailwind CSS** for beautiful, responsive design
- **Vite** for fast development and building
- **React Router** for navigation
- **Axios** for API communication

## 📋 Features

### 🔐 Student Registration
- Student ID validation (format: 20xx-xxxxxx)
- Personal information collection (name, PE course, block/section)
- Automatic data sanitization (removes spaces from block/section)
- Duplicate prevention

### 🚪 Login System
- **Current**: Student ID input (temporary implementation)
- **Future**: NFC ID card tap integration
- Session state management
- Real-time status checking

### ⏱️ Time Tracking
- Automatic timer start on check-in
- Real-time session duration display
- 2-hour daily limit enforcement
- Multiple simultaneous user support
- Session history logging

### 📊 Statistics & Analytics
- **GitHub-style heatmap** showing activity patterns
- Comprehensive statistics (total time, sessions, streaks)
- Achievement system
- Progress tracking over time
- Daily, weekly, and yearly insights

### 🎨 User Interface
- Modern, aesthetically pleasing design
- Mobile-responsive layout
- Intuitive navigation
- Real-time updates
- Toast notifications for user feedback

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn package manager

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd gymlogv2
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start Django development server**
   ```bash
   python manage.py runserver
   ```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. **Install Node.js dependencies**
   ```bash
   npm install
   ```

2. **Start development server**
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173`

## 📁 Project Structure

```
gymlogv2/
├── gymlog_backend/          # Django project settings
│   ├── settings.py         # Main configuration
│   ├── urls.py            # Root URL configuration
│   └── wsgi.py            # WSGI application
├── gym_app/                # Main Django app
│   ├── models.py          # Database models
│   ├── serializers.py     # API serializers
│   ├── views.py           # API views
│   ├── urls.py            # App URL patterns
│   └── admin.py           # Admin interface
├── src/                    # React frontend source
│   ├── components/        # Reusable components
│   │   ├── Layout.jsx     # Main layout wrapper
│   │   └── HeatmapCalendar.jsx  # Activity heatmap
│   ├── pages/             # Page components
│   │   ├── HomePage.jsx   # Main login/dashboard
│   │   ├── RegistrationPage.jsx  # Student registration
│   │   └── StatsPage.jsx  # Statistics and analytics
│   ├── services/          # API communication
│   │   └── api.js         # Axios configuration and endpoints
│   ├── App.jsx            # Main app component
│   ├── main.jsx           # React entry point
│   └── index.css          # Global styles
├── requirements.txt        # Python dependencies
├── package.json           # Node.js dependencies
└── README.md              # This file
```

## 🔌 API Endpoints

### Student Management
- `POST /api/register/` - Register new student
- `POST /api/login/` - Student login
- `GET /api/check-status/{student_id}/` - Check registration status

### Gym Operations
- `POST /api/gym/checkinout/` - Check in/out of gym

### Statistics
- `GET /api/stats/{student_id}/` - Get comprehensive statistics

## 🗄️ Database Models

### Student
- Student ID (unique, validated format)
- Personal information (name, PE course, block)
- Registration date and status
- Computed properties (total sessions, gym time)

### GymSession
- Student reference
- Check-in/check-out timestamps
- Session duration
- Active status
- Date indexing for quick queries

### DailyGymStats
- Aggregated daily statistics
- Optimized for heatmap generation
- Student activity summaries

## 🎨 Design System

### Color Palette
- **Primary**: Blue (#3B82F6) - Main actions and branding
- **Secondary**: Gray (#64748B) - Secondary content
- **Success**: Green (#10B981) - Positive actions
- **Warning**: Yellow (#F59E0B) - Cautions
- **Error**: Red (#EF4444) - Errors and destructive actions

### Typography
- **Font**: Inter (clean, modern sans-serif)
- **Weights**: 300, 400, 500, 600, 700

### Components
- Consistent button styles (`btn-primary`, `btn-secondary`, etc.)
- Standardized form inputs (`input-field`)
- Card containers for content sections
- Responsive grid layouts

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Development vs Production
- Development: SQLite database, debug mode enabled
- Production: Consider PostgreSQL, disable debug, add proper secret keys

## 🚀 Deployment

### Backend (Django)
1. Set `DEBUG=False` in production
2. Configure proper database (PostgreSQL recommended)
3. Set secure `SECRET_KEY`
4. Configure static file serving
5. Use proper WSGI server (Gunicorn, uWSGI)

### Frontend (React)
1. Build production assets: `npm run build`
2. Serve static files through web server (Nginx, Apache)
3. Configure API endpoint URLs for production

## 🔮 Future Enhancements

### Immediate (Post-MVP)
- **NFC Integration**: Hardware support for ID card tapping
- **Admin Dashboard**: Comprehensive gym management interface
- **Reporting**: Advanced analytics and reports
- **Notifications**: Email/SMS notifications for limits

### Medium-term
- **Mobile App**: Native iOS/Android applications
- **Equipment Tracking**: Integration with gym equipment
- **Social Features**: Student leaderboards and challenges
- **API Integration**: Connection with student information systems

### Long-term
- **Multi-gym Support**: Support for multiple gym locations
- **Advanced Analytics**: Machine learning insights
- **Health Integration**: Connection with fitness trackers
- **Booking System**: Equipment and space reservation

## 🐛 Troubleshooting

### Common Issues

**Backend not starting**
- Ensure virtual environment is activated
- Check Python version (3.8+)
- Verify all dependencies are installed: `pip install -r requirements.txt`

**Frontend not loading**
- Check Node.js version (16+)
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall: `rm -rf node_modules && npm install`

**Database errors**
- Run migrations: `python manage.py migrate`
- Check database file permissions
- Recreate database if corrupted: Delete `db.sqlite3` and run migrations

**CORS errors**
- Verify frontend URL in Django CORS settings
- Check that both servers are running
- Ensure API calls use correct backend URL

## 👥 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes with clear, documented code
4. Write/update tests as needed
5. Submit pull request with detailed description

### Code Standards
- **Python**: Follow PEP 8 guidelines
- **JavaScript**: Use ES6+ features, consistent formatting
- **Comments**: Comprehensive documentation for complex logic
- **Git**: Clear, descriptive commit messages

## 📄 License

This project is developed for Asia Pacific College's internal use. All rights reserved.

## 👨‍💻 Development Team

- **Lead Developer**: AI Assistant (Claude)
- **Project Manager**: JPCS-APC Development Team
- **Client**: APC PE Department & Gym Management

## 📞 Support

For technical support or feature requests:
- Create an issue in the repository
- Contact the JPCS-APC Development Team
- Email: [support email]

---

## 🎉 Acknowledgments

Special thanks to:
- Asia Pacific College for the opportunity
- PE Head Coach for project requirements
- JPCS-APC for development support
- All beta testers and early users

---

**Built with ❤️ for Asia Pacific College**

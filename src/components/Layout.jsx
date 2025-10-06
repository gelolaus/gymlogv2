import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { HomeIcon, UserPlusIcon, ChartBarIcon, DocumentArrowDownIcon } from '@heroicons/react/24/outline'

const Layout = ({ children }) => {
  const location = useLocation()
  
  const isActive = (path) => location.pathname === path
  const isHomePage = location.pathname === '/'
  const isFullscreenPage = ['/', '/stats', '/register', '/export', '/feedback'].includes(location.pathname)
  
  if (isFullscreenPage) {
    // Fullscreen layout for homepage and other main pages
    return children
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-lg border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            {/* Logo and Title */}
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-600 to-purple-600 w-10 h-10 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">G</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gradient">APC Gym Log</h1>
                <p className="text-sm text-gray-500">Student Gym Management System</p>
              </div>
            </div>
            
            {/* Navigation */}
            <nav className="flex space-x-6">
              <Link 
                to="/" 
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors duration-200 ${
                  isActive('/') 
                    ? 'bg-blue-100 text-blue-700 font-medium' 
                    : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                }`}
              >
                <HomeIcon className="w-5 h-5" />
                <span>Home</span>
              </Link>
              
              <Link 
                to="/register" 
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors duration-200 ${
                  isActive('/register') 
                    ? 'bg-blue-100 text-blue-700 font-medium' 
                    : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                }`}
              >
                <UserPlusIcon className="w-5 h-5" />
                <span>Register</span>
              </Link>
              
              <Link 
                to="/stats" 
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors duration-200 ${
                  isActive('/stats') 
                    ? 'bg-blue-100 text-blue-700 font-medium' 
                    : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                }`}
              >
                <ChartBarIcon className="w-5 h-5" />
                <span>Check Stats</span>
              </Link>
              
              <Link 
                to="/export" 
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors duration-200 ${
                  isActive('/export') 
                    ? 'bg-blue-100 text-blue-700 font-medium' 
                    : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                }`}
              >
                <DocumentArrowDownIcon className="w-5 h-5" />
                <span>Export Data</span>
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <p className="text-gray-500">
              © 2024 APC Gym Log System. Built for Asia Pacific College.
            </p>
            <p className="text-sm text-gray-400 mt-2">
              Developed by the JPCS-APC Development Team
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Layout

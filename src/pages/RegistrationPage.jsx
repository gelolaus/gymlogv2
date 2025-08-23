import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { 
  UserPlusIcon, 
  AcademicCapIcon,
  IdentificationIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'
import { studentAPI } from '../services/api'

const RegistrationPage = () => {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(false)
  const [formData, setFormData] = useState({
    student_id: '',
    first_name: '',
    last_name: '',
    pe_course: 'N/A',
    block_section: '',
    rfid: ''
  })
  const [errors, setErrors] = useState({})

  const peCoursesOptions = [
    { value: 'PEDUONE', label: 'PEDU ONE' },
    { value: 'PEDUTWO', label: 'PEDU TWO' },
    { value: 'PEDUTRI', label: 'PEDU TRI' },
    { value: 'PEDUFOR', label: 'PEDU FOR' },
    { value: 'N/A', label: 'Not Enrolled in PE' },
  ]

  // Handle input changes
  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }))
    }
  }

  // Validate form
  const validateForm = () => {
    const newErrors = {}

    // Student ID validation
    if (!formData.student_id.trim()) {
      newErrors.student_id = 'Student ID is required'
    } else if (!/^20\d{2}-\d{6}$/.test(formData.student_id.trim())) {
      newErrors.student_id = 'Student ID must be in format 20xx-xxxxxx (e.g., 2023-123456)'
    }

    // First name validation
    if (!formData.first_name.trim()) {
      newErrors.first_name = 'First name is required'
    } else if (formData.first_name.trim().length < 2) {
      newErrors.first_name = 'First name must be at least 2 characters'
    }

    // Last name validation
    if (!formData.last_name.trim()) {
      newErrors.last_name = 'Last name is required'
    } else if (formData.last_name.trim().length < 2) {
      newErrors.last_name = 'Last name must be at least 2 characters'
    }

    // Block section validation
    if (!formData.block_section.trim()) {
      newErrors.block_section = 'Block/Section is required'
    } else if (formData.block_section.trim().length < 3) {
      newErrors.block_section = 'Block/Section must be at least 3 characters'
    }

    // RFID validation
    if (!formData.rfid.trim()) {
      newErrors.rfid = 'RFID is required'
    } else if (formData.rfid.trim().length < 4) {
      newErrors.rfid = 'RFID must be at least 4 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      toast.error('Please fix the errors in the form')
      return
    }

    setIsLoading(true)
    try {
      const response = await studentAPI.register(formData)
      
      if (response.success) {
        toast.success('Registration successful! You can now use the gym.')
        // Navigate to home page after short delay
        setTimeout(() => {
          navigate('/')
        }, 2000)
      }
    } catch (error) {
      // Handle API errors
      if (error.message.includes('already registered')) {
        setErrors({ student_id: 'A student with this ID is already registered' })
      }
      toast.error(error.message || 'Registration failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div 
      className="min-h-screen flex"
      style={{
        background: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)'
      }}
    >
      {/* Left Side - Motivational Content */}
      <div className="flex-1 flex items-center justify-center p-16">
        <div className="max-w-2xl">
          <h1 
            className="text-8xl font-black leading-tight"
            style={{
              color: '#374151',
              fontFamily: 'Arial, sans-serif'
            }}
          >
            Finding strength in every step of the journey.
          </h1>
        </div>
      </div>

      {/* Right Side - Registration Form */}
      <div 
        className="flex-1 flex items-stretch"
        style={{
          backgroundColor: '#E5E7EB'
        }}
      >
        <div 
          className="w-full flex items-center justify-center p-16"
        >
          <div className="w-full max-w-2xl">
            <h2 
              className="text-5xl font-black mb-12 text-center"
              style={{
                color: '#374151',
                fontFamily: 'Arial, sans-serif'
              }}
            >
              Registration
            </h2>

          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Full Name - Combined Field */}
            <div>
              <label 
                className="block text-lg font-medium mb-4"
                style={{ color: '#374151' }}
              >
                Full Name
              </label>
              <div className="grid grid-cols-2 gap-4">
                <input
                  id="first_name"
                  name="first_name"
                  type="text"
                  placeholder="First Name"
                  value={formData.first_name}
                  onChange={handleChange}
                  className={`w-full h-14 rounded-2xl border-none shadow-inner px-4 text-base ${errors.first_name ? 'border-red-300' : ''}`}
                  style={{
                    backgroundColor: '#FFFFFF',
                    color: '#374151'
                  }}
                  disabled={isLoading}
                />
                <input
                  id="last_name"
                  name="last_name"
                  type="text"
                  placeholder="Last Name"
                  value={formData.last_name}
                  onChange={handleChange}
                  className={`w-full h-14 rounded-2xl border-none shadow-inner px-4 text-base ${errors.last_name ? 'border-red-300' : ''}`}
                  style={{
                    backgroundColor: '#FFFFFF',
                    color: '#374151'
                  }}
                  disabled={isLoading}
                />
              </div>
              {(errors.first_name || errors.last_name) && (
                <p className="text-red-600 text-sm mt-2">
                  {errors.first_name || errors.last_name}
                </p>
              )}
            </div>

            {/* Student ID */}
            <div>
              <label 
                className="block text-lg font-medium mb-4"
                style={{ color: '#374151' }}
              >
                Student ID Number
              </label>
              <input
                id="student_id"
                name="student_id"
                type="text"
                placeholder="Student ID Number"
                value={formData.student_id}
                onChange={handleChange}
                className={`w-full h-16 rounded-2xl border-none shadow-inner px-6 text-lg ${errors.student_id ? 'border-red-300' : ''}`}
                style={{
                  backgroundColor: '#FFFFFF',
                  color: '#374151'
                }}
                disabled={isLoading}
              />
              {errors.student_id && (
                <p className="text-red-600 text-sm mt-2">{errors.student_id}</p>
              )}
            </div>

            {/* PE Course and Enrolled Block - Side by Side */}
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label 
                  className="block text-lg font-medium mb-4"
                  style={{ color: '#374151' }}
                >
                  PE Course
                </label>
                <select
                  id="pe_course"
                  name="pe_course"
                  value={formData.pe_course}
                  onChange={handleChange}
                  className="w-full h-16 rounded-2xl border-none shadow-inner px-6 text-lg"
                  style={{
                    backgroundColor: '#FFFFFF',
                    color: '#374151'
                  }}
                  disabled={isLoading}
                >
                  {peCoursesOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label 
                  className="block text-lg font-medium mb-4"
                  style={{ color: '#374151' }}
                >
                  Enrolled Block
                </label>
                <input
                  id="block_section"
                  name="block_section"
                  type="text"
                  placeholder="Enrolled Block"
                  value={formData.block_section}
                  onChange={handleChange}
                  className={`w-full h-16 rounded-2xl border-none shadow-inner px-6 text-lg ${errors.block_section ? 'border-red-300' : ''}`}
                  style={{
                    backgroundColor: '#FFFFFF',
                    color: '#374151'
                  }}
                  disabled={isLoading}
                />
                {errors.block_section && (
                  <p className="text-red-600 text-sm mt-2">{errors.block_section}</p>
                )}
              </div>
            </div>

            {/* RFID */}
            <div>
              <label 
                className="block text-lg font-medium mb-4"
                style={{ color: '#374151' }}
              >
                Tap your APC Identification Card
              </label>
              <input
                id="rfid"
                name="rfid"
                type="text"
                placeholder="APC Identification Card Number"
                value={formData.rfid}
                onChange={handleChange}
                className={`w-full h-16 rounded-2xl border-none shadow-inner px-6 text-lg ${errors.rfid ? 'border-red-300' : ''}`}
                style={{
                  backgroundColor: '#FFFFFF',
                  color: '#374151'
                }}
                disabled={isLoading}
                autoFocus
              />
              {errors.rfid && (
                <p className="text-red-600 text-sm mt-2">{errors.rfid}</p>
              )}
            </div>

            {/* Buttons */}
            <div className="flex gap-6 pt-6">
              <Link 
                to="/" 
                className="flex items-center justify-center space-x-2 px-8 py-4 rounded-2xl font-semibold text-lg transition-all hover:transform hover:scale-105"
                style={{
                  backgroundColor: 'transparent',
                  color: '#374151'
                }}
              >
                <span>← Go back</span>
              </Link>
              
              <button
                type="submit"
                disabled={isLoading}
                className="flex-1 px-8 py-4 rounded-2xl font-semibold text-white text-lg transition-all hover:transform hover:scale-105 flex items-center justify-center space-x-2"
                style={{
                  backgroundColor: '#3b82f6'
                }}
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Registering...</span>
                  </>
                ) : (
                  <span>Register</span>
                )}
              </button>
            </div>
          </form>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RegistrationPage

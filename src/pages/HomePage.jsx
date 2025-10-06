import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { 
  UserIcon, 
  ClockIcon, 
  PlayIcon, 
  StopIcon,
  ExclamationTriangleIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { studentAPI, gymAPI } from '../services/api'



const HomePage = () => {
  const [rfid, setRfid] = useState('')
  const [currentStudent, setCurrentStudent] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [timer, setTimer] = useState(null)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [checkoutData, setCheckoutData] = useState(null)
  const [showCheckInConfirmation, setShowCheckInConfirmation] = useState(false)
  const [currentTime, setCurrentTime] = useState(new Date())
  const [countdown, setCountdown] = useState(5)

  // Update current time every second
  useEffect(() => {
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)
    
    return () => clearInterval(timeInterval)
  }, [])

  // Timer effect for active sessions
  useEffect(() => {
    let interval = null
    
    if (currentStudent?.has_active_session && timer) {
      interval = setInterval(() => {
        const startTime = new Date(currentStudent.active_session.check_in_time)
        const now = new Date()
        const elapsed = Math.floor((now - startTime) / 1000)
        setElapsedTime(elapsed)
      }, 1000)
    }
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [currentStudent, timer])

  // Countdown effect for auto-reset
  useEffect(() => {
    let countdownInterval = null
    
    if ((showCheckInConfirmation || checkoutData) && countdown > 0) {
      countdownInterval = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            // Trigger auto-reset when countdown reaches 0
            setTimeout(() => {
              setCurrentStudent(null)
              setShowCheckInConfirmation(false)
              setTimer(false)
              setElapsedTime(0)
              setCheckoutData(null)
              setRfid('')
              setCountdown(5)
            }, 100)
            return 0
          }
          return prev - 1
        })
      }, 1000)
    }
    
    return () => {
      if (countdownInterval) clearInterval(countdownInterval)
    }
  }, [showCheckInConfirmation, checkoutData, countdown])

  // Fallback effect to ensure reset happens when countdown reaches 0
  useEffect(() => {
    if (countdown === 0 && (showCheckInConfirmation || checkoutData)) {
      const resetTimer = setTimeout(() => {
        setCurrentStudent(null)
        setShowCheckInConfirmation(false)
        setTimer(false)
        setElapsedTime(0)
        setCheckoutData(null)
        setRfid('')
        setCountdown(5)
      }, 100)
      
      return () => clearTimeout(resetTimer)
    }
  }, [countdown, showCheckInConfirmation, checkoutData])

  // Format time display for sessions
  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  // Format current time for display
  const formatCurrentTime = (date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: true 
    })
  }

  // Format current date for display
  const formatCurrentDate = (date) => {
    return date.toLocaleDateString('en-US', { 
      weekday: 'short',
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    })
  }

  // Format minutes to hours and minutes display
  const formatMinutes = (totalMinutes) => {
    const hours = Math.floor(totalMinutes / 60)
    const minutes = totalMinutes % 60
    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
  }

  // Handle automatic login/logout when RFID is tapped
  const handleRfidSubmit = async (e) => {
    e.preventDefault()
    if (!rfid.trim()) {
      toast.error('Please tap your ID card or enter your RFID')
      return
    }

    setIsLoading(true)
    try {
      // RFID tap automatically handles login + check-in/check-out
      const response = await studentAPI.login({ rfid: rfid.trim() })
      
      if (response.success) {
        const { data, message } = response
        
        // Show success message
        toast.success(message)
        
        if (data.action_taken === 'check_in') {
          // Student checked in - show confirmation briefly, then return to home
          setCurrentStudent(data)
          setShowCheckInConfirmation(true)
          setTimer(true)
          setElapsedTime(0)
          setRfid('') // Clear RFID input for next user
          setCountdown(5) // Start countdown for auto-reset
        } else if (data.action_taken === 'check_out') {
          // Student checked out - show completion screen briefly, then auto-reset
          setCurrentStudent(data)
          setCheckoutData(data)
          setTimer(false)
          setElapsedTime(0)
          setRfid('') // Clear RFID input for next user
          setCountdown(5) // Start countdown for auto-reset
        }
      }
      
    } catch (error) {
      toast.error(error.message || 'RFID not recognized. Please check your ID card or register first.')
      setCurrentStudent(null)
      setRfid('')
    } finally {
      setIsLoading(false)
    }
  }

  // Handle gym check-in/check-out
  const handleGymAction = async (action, studentData = null) => {
    const student = studentData || currentStudent
    if (!student) return

    setIsProcessing(true)
    try {
      const response = await gymAPI.checkInOut(student.student.student_id, action)
      
      if (response.success) {
        // Update current student data temporarily to show status
        const updatedData = await studentAPI.login(student.student.student_id)
        setCurrentStudent(updatedData.data)
        
        if (action === 'check_in') {
          setTimer(true)
          setElapsedTime(0)
        } else {
          setTimer(false)
          setElapsedTime(0)
        }
        
        return response
      }
    } catch (error) {
      toast.error(error.message || `Failed to ${action.replace('_', ' ')}`)
      throw error
    } finally {
      setIsProcessing(false)
    }
  }

  // Reset form
  const handleReset = () => {
    setStudentId('')
    setCurrentStudent(null)
    setTimer(false)
    setElapsedTime(0)
    setCheckoutData(null)
  }

  return (
    <div 
      className="min-h-screen flex items-center justify-center p-4"
      style={{
        background: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)'
      }}
    >
      {/* Main Card */}
      <div className="w-full max-w-4xl">
        <div 
          className="rounded-3xl p-12 shadow-2xl"
          style={{
            backgroundColor: '#E5E7EB'
          }}
        >
          {!currentStudent ? (
            /* Main Interface */
            <div className="text-center space-y-8">
              {/* Title */}
              <h1 
                className="text-6xl font-black tracking-wider"
                style={{
                  color: '#374151',
                  fontFamily: 'Arial, sans-serif'
                }}
              >
                APC GYMLOG
              </h1>
              
              {/* Time and Date */}
              <div className="space-y-2">
                <div 
                  className="text-5xl font-bold"
                  style={{
                    color: '#374151'
                  }}
                >
                  {formatCurrentTime(currentTime)}
                </div>
                <div 
                  className="text-xl"
                  style={{
                    color: '#6B7280'
                  }}
                >
                  {formatCurrentDate(currentTime)}
                </div>
              </div>
              
              {/* Instruction Text */}
              <div 
                className="text-2xl font-semibold mt-12 mb-8"
                style={{
                  color: '#374151'
                }}
              >
                Tap your APC Identification Card
              </div>
              
              {/* RFID Input */}
              <form onSubmit={handleRfidSubmit} className="mb-12">
                <input
                  id="rfid"
                  type="text"
                  placeholder=""
                  value={rfid}
                  onChange={(e) => setRfid(e.target.value)}
                  className="w-full max-w-2xl mx-auto h-16 rounded-2xl border-none shadow-inner text-center text-xl font-mono bg-white"
                  disabled={isLoading}
                  autoFocus
                  style={{
                    backgroundColor: '#FFFFFF',
                    color: '#374151'
                  }}
                />
              </form>
              
              {/* Action Buttons */}
              <div className="flex justify-center space-x-6">
                <Link 
                  to="/stats"
                  className="px-8 py-4 rounded-2xl font-semibold text-white text-lg transition-all hover:transform hover:scale-105 shadow-lg"
                  style={{
                    backgroundColor: '#3B82F6'
                  }}
                >
                  Check Stats
                </Link>
                
                <Link 
                  to="/register"
                  className="px-8 py-4 rounded-2xl font-semibold text-white text-lg transition-all hover:transform hover:scale-105 shadow-lg"
                  style={{
                    backgroundColor: '#3B82F6'
                  }}
                >
                  Register today
                </Link>
                
                <Link 
                  to="/export"
                  className="px-8 py-4 rounded-2xl font-semibold text-white text-lg transition-all hover:transform hover:scale-105 shadow-lg"
                  style={{
                    backgroundColor: '#3B82F6'
                  }}
                >
                  Export Data
                </Link>

                <Link 
                  to="/feedback"
                  className="px-8 py-4 rounded-2xl font-semibold text-white text-lg transition-all hover:transform hover:scale-105 shadow-lg"
                  style={{
                    backgroundColor: '#3B82F6'
                  }}
                >
                  Report
                </Link>
              </div>
              
              {isLoading && (
                <div className="mt-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Processing...</p>
                </div>
              )}
            </div>
          ) : (
            /* Student Status Display */
            <div className="space-y-6">
              {/* Student Info */}
              <div className="text-center pb-6 border-b border-gray-400">
                <div className="w-20 h-20 bg-gradient-to-r from-green-500 to-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-white text-2xl font-bold">
                    {currentStudent.student.first_name[0]}{currentStudent.student.last_name[0]}
                  </span>
                </div>
                <h2 className="text-2xl font-bold text-gray-900">
                  {currentStudent.student.full_name}
                </h2>
                <p className="text-gray-600">{currentStudent.student.student_id}</p>
                
                {/* Status Message */}
                <div className="mt-4">
                  {currentStudent.has_active_session ? (
                    <div className="bg-green-100 text-green-800 px-4 py-2 rounded-lg">
                      ✅ Successfully Checked In - Timer Started!
                    </div>
                  ) : (
                    <div className="bg-blue-100 text-blue-800 px-4 py-2 rounded-lg">
                      ✅ Successfully Checked Out - Thank you!
                    </div>
                  )}
                </div>
                
                {/* Check-in Confirmation with Auto-reset */}
                {showCheckInConfirmation && currentStudent.has_active_session && (
                  <div className="mt-4">
                    <div className="bg-green-50 rounded-lg p-4">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2 text-center">
                        ✅ Check-in Successful!
                      </h3>
                      <p className="text-gray-600 text-center mb-2">
                        Your gym session has started. Have a great workout!
                      </p>
                      <div className="text-center">
                        <div className="inline-flex items-center space-x-2 text-green-600">
                          <ClockIcon className="w-4 h-4" />
                          <span>Session timer is now running</span>
                        </div>
                      </div>
                      
                      {/* Countdown to return */}
                      <div className="mt-4 text-center">
                        <div className="inline-flex items-center space-x-2 text-blue-600">
                          <ClockIcon className="w-4 h-4" />
                          <span>Returning to main screen in {countdown} seconds...</span>
                        </div>
                      </div>
                    </div>
                    
                    
                  </div>
                )}
                
                {/* Display Daily and Total Time on Checkout */}
                {!currentStudent.has_active_session && checkoutData && (
                  <div className="mt-6 space-y-4">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3 text-center">
                        Your Gym Time Summary
                      </h3>
                      
                      <div className="grid grid-cols-2 gap-4">
                        {/* Today's Total Time */}
                        <div className="text-center">
                          <div className="bg-blue-100 rounded-lg p-3">
                            <ClockIcon className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                            <div className="text-2xl font-bold text-blue-800">
                              {formatMinutes(checkoutData.daily_gym_minutes || 0)}
                            </div>
                            <div className="text-sm text-blue-600 font-medium">
                              Today's Total
                            </div>
                          </div>
                        </div>
                        
                        {/* Overall Total Time */}
                        <div className="text-center">
                          <div className="bg-green-100 rounded-lg p-3">
                            <ChartBarIcon className="w-8 h-8 text-green-600 mx-auto mb-2" />
                            <div className="text-2xl font-bold text-green-800">
                              {formatMinutes(checkoutData.student?.total_gym_time_minutes || 0)}
                            </div>
                            <div className="text-sm text-green-600 font-medium">
                              Overall Total
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      {/* Session Duration */}
                      <div className="mt-4 text-center">
                        <div className="bg-yellow-50 rounded-lg p-3">
                          <div className="text-lg font-semibold text-yellow-800">
                            This Session: {checkoutData.completed_session?.session_duration_formatted || 'N/A'}
                          </div>
                          <div className="text-sm text-yellow-600">
                            Great workout! 💪
                          </div>
                        </div>
                      </div>
                      
                      {/* Countdown to return */}
                      <div className="mt-4 text-center">
                        <div className="bg-blue-50 rounded-lg p-3">
                          <div className="inline-flex items-center space-x-2 text-blue-600">
                            <ClockIcon className="w-4 h-4" />
                            <span>Returning to main screen in {countdown} seconds...</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                

              </div>

              {/* Session Info for Check-in - Only show if not in confirmation mode */}
              {currentStudent.has_active_session && !showCheckInConfirmation && (
                <div className="text-center">
                  <div className="text-4xl font-mono font-bold text-green-800 mb-2">
                    {formatTime(elapsedTime)}
                  </div>
                  <p className="text-green-600">Gym session active - Tap your ID card again to check out</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default HomePage

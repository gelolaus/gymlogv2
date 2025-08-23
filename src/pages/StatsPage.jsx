import React, { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { 
  ChartBarIcon, 
  UserIcon, 
  ClockIcon, 
  FireIcon,
  CalendarIcon,
  TrophyIcon
} from '@heroicons/react/24/outline'
import { studentAPI } from '../services/api'
import HeatmapCalendar from '../components/HeatmapCalendar'

const StatsPage = () => {
  const [searchParams] = useSearchParams()
  const [rfid, setRfid] = useState('')
  const [studentStats, setStudentStats] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  // Load stats on component mount if student_id is in URL (legacy support)
  useEffect(() => {
    const studentId = searchParams.get('student_id')
    if (studentId) {
      // Legacy support - convert to RFID lookup if needed
      handleLegacyLookup(studentId)
    }
  }, [])

  // Handle legacy lookup by student ID
  const handleLegacyLookup = async (studentId) => {
    setIsLoading(true)
    try {
      const response = await studentAPI.getStats(studentId.trim())
      
      if (response.success) {
        setStudentStats(response.data)
        toast.success(response.message)
      }
    } catch (error) {
      toast.error(error.message || 'Failed to load statistics')
      setStudentStats(null)
    } finally {
      setIsLoading(false)
    }
  }

  // Handle RFID stats lookup
  const handleRFIDLookup = async (e) => {
    if (e) e.preventDefault()
    
    if (!rfid.trim()) {
      toast.error('Please tap your ID card or enter your RFID')
      return
    }

    setIsLoading(true)
    try {
      const response = await studentAPI.getStatsRFID({ rfid: rfid.trim() })
      
      if (response.success) {
        setStudentStats(response.data)
        toast.success(response.message)
      }
    } catch (error) {
      toast.error(error.message || 'RFID not recognized. Please check your ID card or register first.')
      setStudentStats(null)
    } finally {
      setIsLoading(false)
    }
  }

  // Format duration for display
  const formatDuration = (minutes) => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`
  }

  return (
    <div 
      className="min-h-screen flex items-center justify-center p-4"
      style={{
        background: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)'
      }}
    >
      {/* Main Card */}
      <div className="w-full max-w-6xl">
        <div 
          className="rounded-3xl p-12 shadow-2xl"
          style={{
            backgroundColor: '#E5E7EB'
          }}
        >
          {/* Header */}
          <div className="text-center space-y-4 mb-6">
            <h1 
              className="text-6xl font-black tracking-wider"
              style={{
                color: '#374151',
                fontFamily: 'Arial, sans-serif'
              }}
            >
              GYM STATISTICS
            </h1>
          </div>

          {/* Student ID Lookup */}
          {!studentStats && (
            <div className="max-w-lg mx-auto">
              <div 
                className="rounded-2xl p-10 shadow-lg"
                style={{
                  backgroundColor: '#FFFFFF'
                }}
              >
                <div className="text-center mb-8">
                  <ChartBarIcon 
                    className="w-20 h-20 mx-auto mb-6"
                    style={{ color: '#3B82F6' }}
                  />
                  <h2 
                    className="text-3xl font-bold"
                    style={{ color: '#374151' }}
                  >
                    View Your Statistics
                  </h2>
                  <p 
                    className="text-lg mt-2"
                    style={{ color: '#6B7280' }}
                  >
                    Tap your APC student ID card to see your gym activity
                  </p>
                </div>

                <form onSubmit={handleRFIDLookup} className="space-y-4">
                  <div>
                    <label 
                      htmlFor="rfid" 
                      className="flex items-center space-x-2 text-sm font-medium mb-2"
                      style={{ color: '#374151' }}
                    >
                      <UserIcon className="w-4 h-4" />
                      <span>RFID / Student ID Card</span>
                    </label>
                                                       <input
                     id="rfid"
                     type="text"
                     placeholder="Tap your ID card here"
                     value={rfid}
                     onChange={(e) => setRfid(e.target.value)}
                     className="w-full h-16 rounded-2xl border-none shadow-inner text-center text-xl font-mono"
                     style={{
                       backgroundColor: '#F9FAFB',
                       color: '#374151'
                     }}
                     disabled={isLoading}
                     autoFocus
                   />
                                 <p 
                   className="text-base mt-3 text-center"
                   style={{ color: '#6B7280' }}
                 >
                   Tap your APC student ID card on the RFID reader
                 </p>
                  </div>

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full px-8 py-5 rounded-2xl font-semibold text-white text-xl transition-all hover:transform hover:scale-105 shadow-lg flex items-center justify-center space-x-2"
                    style={{
                      backgroundColor: '#3B82F6'
                    }}
                  >
                    {isLoading ? (
                      <>
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                        <span>Loading...</span>
                      </>
                    ) : (
                      <>
                        <ChartBarIcon className="w-6 h-6" />
                        <span>View My Stats</span>
                      </>
                    )}
                  </button>
                </form>

                <div className="pt-6 border-t mt-6" style={{ borderColor: '#D1D5DB' }}>
                  <Link 
                    to="/" 
                    className="w-full block text-center px-8 py-5 rounded-2xl font-semibold text-xl transition-all hover:transform hover:scale-105 shadow-lg"
                    style={{
                      backgroundColor: '#F3F4F6',
                      color: '#374151'
                    }}
                  >
                    Back to Home
                  </Link>
                </div>
              </div>
            </div>
          )}

          {/* Statistics Dashboard */}
          {studentStats && (
            <div className="space-y-8">
              {/* Student Info Header */}
              <div 
                className="rounded-2xl p-8 shadow-lg"
                style={{
                  backgroundColor: '#FFFFFF'
                }}
              >
                <div className="flex items-center space-x-6">
                  <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-2xl font-bold">
                      {studentStats.student_info.first_name[0]}{studentStats.student_info.last_name[0]}
                    </span>
                  </div>
                  <div className="flex-1">
                    <h2 
                      className="text-2xl font-bold"
                      style={{ color: '#374151' }}
                    >
                      {studentStats.student_info.full_name}
                    </h2>
                    <p style={{ color: '#6B7280' }}>{studentStats.student_info.student_id}</p>
                    <p 
                      className="text-sm"
                      style={{ color: '#9CA3AF' }}
                    >
                      {studentStats.student_info.pe_course} • {studentStats.student_info.block_section}
                    </p>
                    <p 
                      className="text-sm"
                      style={{ color: '#9CA3AF' }}
                    >
                      Member since {new Date(studentStats.student_info.registration_date).toLocaleDateString()}
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setStudentStats(null)
                      setRfid('')
                    }}
                    className="px-6 py-3 rounded-2xl font-semibold transition-all hover:transform hover:scale-105 shadow-lg"
                    style={{
                      backgroundColor: '#F3F4F6',
                      color: '#374151'
                    }}
                  >
                    View Different Stats
                  </button>
                </div>
              </div>

              {/* Key Statistics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                                 <div 
                   className="rounded-2xl p-8 shadow-lg text-center"
                   style={{
                     backgroundColor: '#FFFFFF'
                   }}
                 >
                   <div className="w-16 h-16 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                     <CalendarIcon className="w-8 h-8 text-blue-600" />
                   </div>
                   <div 
                     className="text-3xl font-bold mb-2"
                     style={{ color: '#374151' }}
                   >
                     {studentStats.student_info.total_gym_sessions}
                   </div>
                   <div 
                     className="text-base"
                     style={{ color: '#6B7280' }}
                   >
                     Total Sessions
                   </div>
                 </div>

                <div 
                  className="rounded-2xl p-8 shadow-lg text-center"
                  style={{
                    backgroundColor: '#FFFFFF'
                  }}
                >
                  <div className="w-16 h-16 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <ClockIcon className="w-8 h-8 text-green-600" />
                  </div>
                  <div 
                    className="text-3xl font-bold mb-2"
                    style={{ color: '#374151' }}
                  >
                    {formatDuration(studentStats.average_session_duration)}
                  </div>
                  <div 
                    className="text-base"
                    style={{ color: '#6B7280' }}
                  >
                    Avg Session
                  </div>
                </div>

                <div 
                  className="rounded-2xl p-8 shadow-lg text-center"
                  style={{
                    backgroundColor: '#FFFFFF'
                  }}
                >
                  <div className="w-16 h-16 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <TrophyIcon className="w-8 h-8 text-purple-600" />
                  </div>
                  <div 
                    className="text-3xl font-bold mb-2"
                    style={{ color: '#374151' }}
                  >
                    {formatDuration(studentStats.longest_session_minutes)}
                  </div>
                  <div 
                    className="text-base"
                    style={{ color: '#6B7280' }}
                  >
                    Longest Session
                  </div>
                </div>

                <div 
                  className="rounded-2xl p-8 shadow-lg text-center"
                  style={{
                    backgroundColor: '#FFFFFF'
                  }}
                >
                  <div className="w-16 h-16 bg-orange-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <ClockIcon className="w-8 h-8 text-orange-600" />
                  </div>
                  <div 
                    className="text-3xl font-bold mb-2"
                    style={{ color: '#374151' }}
                  >
                    {formatDuration(studentStats.student_info.total_gym_time_minutes)}
                  </div>
                  <div 
                    className="text-base"
                    style={{ color: '#6B7280' }}
                  >
                    Total Time
                  </div>
                </div>
              </div>

              {/* Activity Heatmap */}
              <div 
                className="rounded-2xl p-8 shadow-lg"
                style={{
                  backgroundColor: '#FFFFFF'
                }}
              >
                <div className="mb-4">
                  <h3 
                    className="text-xl font-bold mb-2"
                    style={{ color: '#374151' }}
                  >
                    Activity Heatmap
                  </h3>
                </div>
                
                <HeatmapCalendar data={studentStats.heatmap_data} />
                
                <div 
                  className="mt-6 flex items-center justify-between text-sm"
                  style={{ color: '#9CA3AF' }}
                >
                  <span>Less</span>
                  <div className="flex items-center space-x-1">
                    <div className="heatmap-cell heatmap-level-0"></div>
                    <div className="heatmap-cell heatmap-level-1"></div>
                    <div className="heatmap-cell heatmap-level-2"></div>
                    <div className="heatmap-cell heatmap-level-3"></div>
                    <div className="heatmap-cell heatmap-level-4"></div>
                  </div>
                  <span>More</span>
                </div>
              </div>

              

              {/* Back to Home */}
              <div className="text-center">
                <Link 
                  to="/" 
                  className="px-8 py-4 rounded-2xl font-semibold text-white text-lg transition-all hover:transform hover:scale-105 shadow-lg"
                  style={{
                    backgroundColor: '#3B82F6'
                  }}
                >
                  Back to Home
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default StatsPage

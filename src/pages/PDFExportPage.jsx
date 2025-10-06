import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { 
  DocumentArrowDownIcon,
  UserIcon,
  CalendarDaysIcon,
  BuildingOfficeIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline'
import { pdfAPI, studentAPI } from '../services/api'

const PDFExportPage = () => {
  const [exportType, setExportType] = useState('user')
  const [isLoading, setIsLoading] = useState(false)
  const [availableBlocks, setAvailableBlocks] = useState([])
  
  // Form data
  const [formData, setFormData] = useState({
    studentId: '',
    date: '',
    block: '',
    dateFrom: '',
    dateTo: ''
  })

  // Load available blocks on component mount
  useEffect(() => {
    loadAvailableBlocks()
  }, [])

  const loadAvailableBlocks = async () => {
    try {
      const response = await pdfAPI.getAvailableBlocks()
      if (response.success) {
        setAvailableBlocks(response.data.blocks)
      }
    } catch (error) {
      console.error('Failed to load blocks:', error)
    }
  }

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const validateForm = () => {
    switch (exportType) {
      case 'user':
        if (!formData.studentId.trim()) {
          toast.error('Please enter a Student ID')
          return false
        }
        break
      case 'day':
        if (!formData.date) {
          toast.error('Please select a date')
          return false
        }
        break
      case 'block':
        if (!formData.block) {
          toast.error('Please select a block/section')
          return false
        }
        break
      default:
        return false
    }
    return true
  }

  const handleExport = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setIsLoading(true)
    
    try {
      let downloadPromise
      
      switch (exportType) {
        case 'user':
          downloadPromise = pdfAPI.exportUserReport({
            studentId: formData.studentId.trim(),
            dateFrom: formData.dateFrom || undefined,
            dateTo: formData.dateTo || undefined
          })
          break
        case 'day':
          downloadPromise = pdfAPI.exportDailyReport({
            date: formData.date
          })
          break
        case 'block':
          downloadPromise = pdfAPI.exportBlockReport({
            block: formData.block,
            dateFrom: formData.dateFrom || undefined,
            dateTo: formData.dateTo || undefined
          })
          break
        default:
          throw new Error('Invalid export type')
      }

      await downloadPromise
      toast.success('PDF exported successfully!')
      
    } catch (error) {
      console.error('Export error:', error)
      toast.error(error.message || 'Failed to export PDF')
    } finally {
      setIsLoading(false)
    }
  }

  const resetForm = () => {
    setFormData({
      studentId: '',
      date: '',
      block: '',
      dateFrom: '',
      dateTo: ''
    })
  }

  const handleExportTypeChange = (newType) => {
    setExportType(newType)
    resetForm()
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
          <div className="text-center space-y-4 mb-8">
            <h1 
              className="text-5xl font-black tracking-wider"
              style={{
                color: '#374151',
                fontFamily: 'Arial, sans-serif'
              }}
            >
              PDF EXPORT
            </h1>
            <p 
              className="text-xl max-w-2xl mx-auto"
              style={{
                color: '#6B7280'
              }}
            >
              Export gym data in PDF format by user, day, or block/section
            </p>
          </div>

          {/* Export Type Selection */}
          <div className="max-w-4xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              {/* User Export */}
              <div 
                className={`rounded-2xl p-6 shadow-lg cursor-pointer transition-all ${
                  exportType === 'user' 
                    ? 'ring-2 ring-blue-500' 
                    : 'hover:shadow-lg'
                }`}
                style={{
                  backgroundColor: exportType === 'user' ? '#EFF6FF' : '#FFFFFF'
                }}
                onClick={() => handleExportTypeChange('user')}
              >
                <div className="text-center">
                  <UserIcon className={`w-12 h-12 mx-auto mb-4 ${
                    exportType === 'user' ? 'text-blue-600' : 'text-gray-400'
                  }`} />
                  <h3 
                    className="text-lg font-semibold mb-2"
                    style={{ color: '#374151' }}
                  >
                    Individual User
                  </h3>
                  <p 
                    className="text-sm"
                    style={{ color: '#6B7280' }}
                  >
                    Export data for a specific student with session details and statistics
                  </p>
                </div>
              </div>

              {/* Daily Export */}
              <div 
                className={`rounded-2xl p-6 shadow-lg cursor-pointer transition-all ${
                  exportType === 'day' 
                    ? 'ring-2 ring-green-500' 
                    : 'hover:shadow-lg'
                }`}
                style={{
                  backgroundColor: exportType === 'day' ? '#F0FDF4' : '#FFFFFF'
                }}
                onClick={() => handleExportTypeChange('day')}
              >
                <div className="text-center">
                  <CalendarDaysIcon className={`w-12 h-12 mx-auto mb-4 ${
                    exportType === 'day' ? 'text-green-600' : 'text-gray-400'
                  }`} />
                  <h3 
                    className="text-lg font-semibold mb-2"
                    style={{ color: '#374151' }}
                  >
                    Daily Report
                  </h3>
                  <p 
                    className="text-sm"
                    style={{ color: '#6B7280' }}
                  >
                    Export all gym activity for a specific date with session details
                  </p>
                </div>
              </div>

              {/* Block Export */}
              <div 
                className={`rounded-2xl p-6 shadow-lg cursor-pointer transition-all ${
                  exportType === 'block' 
                    ? 'ring-2 ring-purple-500' 
                    : 'hover:shadow-lg'
                }`}
                style={{
                  backgroundColor: exportType === 'block' ? '#FAF5FF' : '#FFFFFF'
                }}
                onClick={() => handleExportTypeChange('block')}
              >
                <div className="text-center">
                  <BuildingOfficeIcon className={`w-12 h-12 mx-auto mb-4 ${
                    exportType === 'block' ? 'text-purple-600' : 'text-gray-400'
                  }`} />
                  <h3 
                    className="text-lg font-semibold mb-2"
                    style={{ color: '#374151' }}
                  >
                    Block/Section
                  </h3>
                  <p 
                    className="text-sm"
                    style={{ color: '#6B7280' }}
                  >
                    Export data for all students in a specific block or section
                  </p>
                </div>
              </div>
            </div>

            {/* Export Form */}
            <div 
              className="rounded-2xl p-8 shadow-lg"
              style={{
                backgroundColor: '#FFFFFF'
              }}
            >
              <form onSubmit={handleExport} className="space-y-6">
                <div className="flex items-center space-x-4 mb-6">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    exportType === 'user' ? 'bg-blue-500' :
                    exportType === 'day' ? 'bg-green-500' : 'bg-purple-500'
                  }`}>
                    {exportType === 'user' && <UserIcon className="w-4 h-4 text-white" />}
                    {exportType === 'day' && <CalendarDaysIcon className="w-4 h-4 text-white" />}
                    {exportType === 'block' && <BuildingOfficeIcon className="w-4 h-4 text-white" />}
                  </div>
                  <h2 
                    className="text-xl font-bold"
                    style={{ color: '#374151' }}
                  >
                    {exportType === 'user' && 'Individual User Export'}
                    {exportType === 'day' && 'Daily Report Export'}
                    {exportType === 'block' && 'Block/Section Export'}
                  </h2>
                </div>

                {/* User-specific fields */}
                {exportType === 'user' && (
                  <div>
                    <label 
                      htmlFor="studentId" 
                      className="block text-sm font-medium mb-2"
                      style={{ color: '#374151' }}
                    >
                      Student ID <span className="text-red-500">*</span>
                    </label>
                    <input
                      id="studentId"
                      type="text"
                      placeholder="e.g., 2023-123456"
                      value={formData.studentId}
                      onChange={(e) => handleInputChange('studentId', e.target.value)}
                      className="w-full h-12 rounded-2xl border-none shadow-inner px-4"
                      style={{
                        backgroundColor: '#F9FAFB',
                        color: '#374151'
                      }}
                      disabled={isLoading}
                    />
                  </div>
                )}

                {/* Day-specific fields */}
                {exportType === 'day' && (
                  <div>
                    <label 
                      htmlFor="date" 
                      className="block text-sm font-medium mb-2"
                      style={{ color: '#374151' }}
                    >
                      Select Date <span className="text-red-500">*</span>
                    </label>
                    <input
                      id="date"
                      type="date"
                      value={formData.date}
                      onChange={(e) => handleInputChange('date', e.target.value)}
                      className="w-full h-12 rounded-2xl border-none shadow-inner px-4"
                      style={{
                        backgroundColor: '#F9FAFB',
                        color: '#374151'
                      }}
                      disabled={isLoading}
                    />
                  </div>
                )}

                {/* Block-specific fields */}
                {exportType === 'block' && (
                  <div>
                    <label 
                      htmlFor="block" 
                      className="block text-sm font-medium mb-2"
                      style={{ color: '#374151' }}
                    >
                      Block/Section <span className="text-red-500">*</span>
                    </label>
                    <select
                      id="block"
                      value={formData.block}
                      onChange={(e) => handleInputChange('block', e.target.value)}
                      className="w-full h-12 rounded-2xl border-none shadow-inner px-4"
                      style={{
                        backgroundColor: '#F9FAFB',
                        color: '#374151'
                      }}
                      disabled={isLoading}
                    >
                      <option value="">Select a block/section</option>
                      {availableBlocks.map(block => (
                        <option key={block} value={block}>{block}</option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Date range filters (for user and block exports) */}
                {(exportType === 'user' || exportType === 'block') && (
                  <div className="border-t pt-6" style={{ borderColor: '#D1D5DB' }}>
                    <h3 
                      className="text-lg font-medium mb-4"
                      style={{ color: '#374151' }}
                    >
                      Date Range Filter (Optional)
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label 
                          htmlFor="dateFrom" 
                          className="block text-sm font-medium mb-2"
                          style={{ color: '#374151' }}
                        >
                          From Date
                        </label>
                        <input
                          id="dateFrom"
                          type="date"
                          value={formData.dateFrom}
                          onChange={(e) => handleInputChange('dateFrom', e.target.value)}
                          className="w-full h-12 rounded-2xl border-none shadow-inner px-4"
                          style={{
                            backgroundColor: '#F9FAFB',
                            color: '#374151'
                          }}
                          disabled={isLoading}
                        />
                      </div>
                      <div>
                        <label 
                          htmlFor="dateTo" 
                          className="block text-sm font-medium mb-2"
                          style={{ color: '#374151' }}
                        >
                          To Date
                        </label>
                        <input
                          id="dateTo"
                          type="date"
                          value={formData.dateTo}
                          onChange={(e) => handleInputChange('dateTo', e.target.value)}
                          className="w-full h-12 rounded-2xl border-none shadow-inner px-4"
                          style={{
                            backgroundColor: '#F9FAFB',
                            color: '#374151'
                          }}
                          disabled={isLoading}
                        />
                      </div>
                    </div>
                    <p 
                      className="text-sm mt-2"
                      style={{ color: '#6B7280' }}
                    >
                      Leave blank to include all available data
                    </p>
                  </div>
                )}

                {/* Action buttons */}
                <div className="flex flex-col sm:flex-row gap-4 pt-6">
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="flex items-center justify-center space-x-2 flex-1 px-8 py-4 rounded-2xl font-semibold text-white text-lg transition-all hover:transform hover:scale-105 shadow-lg"
                    style={{
                      backgroundColor: '#3B82F6'
                    }}
                  >
                    {isLoading ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        <span>Generating PDF...</span>
                      </>
                    ) : (
                      <>
                        <DocumentArrowDownIcon className="w-5 h-5" />
                        <span>Export PDF</span>
                      </>
                    )}
                  </button>
                  
                  <button
                    type="button"
                    onClick={resetForm}
                    disabled={isLoading}
                    className="flex-1 px-8 py-4 rounded-2xl font-semibold text-lg transition-all hover:transform hover:scale-105 shadow-lg"
                    style={{
                      backgroundColor: '#F3F4F6',
                      color: '#374151'
                    }}
                  >
                    Reset Form
                  </button>
                </div>
              </form>
            </div>

            {/* Back to Home */}
            <div className="text-center pt-6">
              <Link 
                to="/" 
                className="inline-flex items-center space-x-2 px-8 py-4 rounded-2xl font-semibold text-lg transition-all hover:transform hover:scale-105 shadow-lg"
                style={{
                  backgroundColor: '#F3F4F6',
                  color: '#374151'
                }}
              >
                <ArrowLeftIcon className="w-4 h-4" />
                <span>Back to Home</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PDFExportPage

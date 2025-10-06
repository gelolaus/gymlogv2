import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth tokens here if needed in the future
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    // Handle common errors
    if (error.response?.status === 404) {
      throw new Error('Resource not found')
    } else if (error.response?.status >= 500) {
      throw new Error('Server error. Please try again later.')
    } else if (error.response?.data?.message) {
      throw new Error(error.response.data.message)
    } else {
      throw new Error('An unexpected error occurred')
    }
  }
)

// API endpoints
export const studentAPI = {
  // Check if student is registered and get status
  checkStatus: (studentId) => api.get(`/check-status/${studentId}/`),
  
  // Register new student
  register: (studentData) => api.post('/register/', studentData),
  
  // Login student using RFID
  login: (rfidData) => api.post('/login/', rfidData),
  
  // Get student statistics and heatmap data
  getStats: (studentId) => api.get(`/stats/${studentId}/`),
  
  // Get student statistics using RFID
  getStatsRFID: (rfidData) => api.post('/stats/rfid/', rfidData),
}

export const gymAPI = {
  // Check-in or check-out
  checkInOut: (studentId, action) => api.post('/gym/checkinout/', {
    student_id: studentId,
    action: action, // 'check_in' or 'check_out'
  }),
}

// Feedback API
export const feedbackAPI = {
  submit: (payload) => api.post('/feedback/', payload),
}

// PDF export API
export const pdfAPI = {
  // Create a separate axios instance for PDF downloads
  _pdfApi: axios.create({
    baseURL: 'http://localhost:8000/api',
    timeout: 30000, // Longer timeout for PDF generation
    responseType: 'blob', // Important for file downloads
  }),

  // Get available blocks/sections
  getAvailableBlocks: () => api.get('/export/blocks/'),

  // Export user report
  exportUserReport: async ({ studentId, dateFrom, dateTo }) => {
    const params = new URLSearchParams({
      type: 'user',
      student_id: studentId,
    })
    
    if (dateFrom) params.append('date_from', dateFrom)
    if (dateTo) params.append('date_to', dateTo)

    const response = await pdfAPI._pdfApi.get(`/export/pdf/?${params}`)
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `gym_report_${studentId}_${new Date().toISOString().split('T')[0]}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  // Export daily report
  exportDailyReport: async ({ date }) => {
    const params = new URLSearchParams({
      type: 'day',
      date: date,
    })

    const response = await pdfAPI._pdfApi.get(`/export/pdf/?${params}`)
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `daily_gym_report_${date}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  // Export block report
  exportBlockReport: async ({ block, dateFrom, dateTo }) => {
    const params = new URLSearchParams({
      type: 'block',
      block: block,
    })
    
    if (dateFrom) params.append('date_from', dateFrom)
    if (dateTo) params.append('date_to', dateTo)

    const response = await pdfAPI._pdfApi.get(`/export/pdf/?${params}`)
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `block_report_${block}_${new Date().toISOString().split('T')[0]}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },
}

export default api

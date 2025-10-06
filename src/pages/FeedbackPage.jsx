import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { feedbackAPI } from '../services/api'
import { UserIcon, EnvelopeIcon, ChatBubbleLeftRightIcon, HomeIcon } from '@heroicons/react/24/outline'

const FeedbackPage = () => {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    full_name: '',
    block_section: '',
    email: '',
    message: '',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    // Frontend validation for APC student email domain
    if (!form.email.toLowerCase().endsWith('@student.apc.edu.ph')) {
      toast.error('Please use your APC student email (ends with @student.apc.edu.ph).')
      return
    }
    setIsSubmitting(true)
    try {
      const res = await feedbackAPI.submit(form)
      if (res.success) {
        toast.success(res.message)
        setForm({ full_name: '', block_section: '', email: '', message: '' })
        // Optionally navigate back home
        // navigate('/')
      }
    } catch (err) {
      toast.error(err.message || 'Failed to submit feedback')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div 
      className="min-h-screen flex items-center justify-center p-4"
      style={{ background: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)' }}
    >
      <div className="w-full max-w-3xl">
        <div className="rounded-3xl p-12 shadow-2xl" style={{ backgroundColor: '#E5E7EB' }}>
          <div className="text-center space-y-4 mb-8">
            <h1 
              className="text-5xl font-black tracking-wider"
              style={{ color: '#374151', fontFamily: 'Arial, sans-serif' }}
            >
              FEEDBACK
            </h1>
            <p className="text-lg" style={{ color: '#6B7280' }}>
              Report issues or share your suggestions with the team.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="rounded-2xl p-8 shadow-lg" style={{ backgroundColor: '#FFFFFF' }}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="flex items-center space-x-2 text-sm font-medium mb-2" style={{ color: '#374151' }}>
                    <UserIcon className="w-4 h-4" />
                    <span>Full Name</span>
                  </label>
                  <input
                    name="full_name"
                    type="text"
                    value={form.full_name}
                    onChange={handleChange}
                    required
                    className="w-full h-12 rounded-2xl border-none shadow-inner px-4 text-base"
                    style={{ backgroundColor: '#F9FAFB', color: '#374151' }}
                  />
                </div>
                <div>
                  <label className="flex items-center space-x-2 text-sm font-medium mb-2" style={{ color: '#374151' }}>
                    <UserIcon className="w-4 h-4" />
                    <span>Block/Section</span>
                  </label>
                  <input
                    name="block_section"
                    type="text"
                    value={form.block_section}
                    onChange={handleChange}
                    className="w-full h-12 rounded-2xl border-none shadow-inner px-4 text-base"
                    style={{ backgroundColor: '#F9FAFB', color: '#374151' }}
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="flex items-center space-x-2 text-sm font-medium mb-2" style={{ color: '#374151' }}>
                    <EnvelopeIcon className="w-4 h-4" />
                    <span>Email Address</span>
                  </label>
                  <input
                    name="email"
                    type="email"
                    value={form.email}
                    onChange={handleChange}
                    required
                    className="w-full h-12 rounded-2xl border-none shadow-inner px-4 text-base"
                    style={{ backgroundColor: '#F9FAFB', color: '#374151' }}
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="flex items-center space-x-2 text-sm font-medium mb-2" style={{ color: '#374151' }}>
                    <ChatBubbleLeftRightIcon className="w-4 h-4" />
                    <span>Message</span>
                  </label>
                  <textarea
                    name="message"
                    rows="6"
                    value={form.message}
                    onChange={handleChange}
                    required
                    className="w-full rounded-2xl border-none shadow-inner px-4 py-3 text-base"
                    style={{ backgroundColor: '#F9FAFB', color: '#374151' }}
                  />
                </div>
              </div>

              <div className="mt-8 flex justify-between">
                <Link
                  to="/"
                  className="px-6 py-3 rounded-2xl font-semibold transition-all hover:transform hover:scale-105 shadow-lg"
                  style={{ backgroundColor: '#F3F4F6', color: '#374151' }}
                >
                  Back to Home
                </Link>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-8 py-3 rounded-2xl font-semibold text-white transition-all hover:transform hover:scale-105 shadow-lg"
                  style={{ backgroundColor: '#3B82F6' }}
                >
                  {isSubmitting ? 'Submitting...' : 'Submit'}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default FeedbackPage



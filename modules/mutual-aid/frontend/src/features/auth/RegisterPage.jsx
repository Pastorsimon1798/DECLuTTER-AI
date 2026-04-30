import { useState } from 'react'
import { useNavigate, Link, Navigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

// TEMPORARY: Disable auth for testing
const AUTH_DISABLED = true

export function RegisterPage() {
  const navigate = useNavigate()
  const { register, loading, error } = useAuthStore()

  // Redirect to dashboard if auth is disabled
  if (AUTH_DISABLED) {
    return <Navigate to="/" replace />
  }
  const [formData, setFormData] = useState({
    pseudonym: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
  })
  const [formErrors, setFormErrors] = useState({})

  const validate = () => {
    const errors = {}

    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match'
    }

    if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters'
    }

    if (!formData.email && !formData.phone) {
      errors.contact = 'Please provide either email or phone number'
    }

    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    try {
      const { confirmPassword, ...userData } = formData
      // Remove empty fields
      const cleanedData = Object.fromEntries(
        Object.entries(userData).filter(([_, v]) => v !== '')
      )

      await register(cleanedData)
      navigate('/')
    } catch (err) {
      // Error is handled by store
    }
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
    // Clear errors for this field
    if (formErrors[e.target.name]) {
      setFormErrors({
        ...formErrors,
        [e.target.name]: undefined,
      })
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold">🤝</h1>
          <h2 className="mt-6 text-3xl font-bold tracking-tight text-gray-900">
            Join CommunityCircle
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Create your account to start helping your community
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800">
              {error}
            </div>
          )}

          {formErrors.contact && (
            <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800">
              {formErrors.contact}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="pseudonym" className="block text-sm font-medium text-gray-700">
                Pseudonym *
              </label>
              <input
                id="pseudonym"
                name="pseudonym"
                type="text"
                required
                value={formData.pseudonym}
                onChange={handleChange}
                className="input mt-1"
                placeholder="Choose a display name"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                className="input mt-1"
                placeholder="your@email.com"
              />
            </div>

            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700">
                Phone
              </label>
              <input
                id="phone"
                name="phone"
                type="tel"
                value={formData.phone}
                onChange={handleChange}
                className="input mt-1"
                placeholder="+1234567890"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password *
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleChange}
                className={`input mt-1 ${formErrors.password ? 'border-red-500' : ''}`}
                placeholder="Minimum 8 characters"
              />
              {formErrors.password && (
                <p className="mt-1 text-sm text-red-600">{formErrors.password}</p>
              )}
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                Confirm Password *
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                required
                value={formData.confirmPassword}
                onChange={handleChange}
                className={`input mt-1 ${formErrors.confirmPassword ? 'border-red-500' : ''}`}
                placeholder="Re-enter password"
              />
              {formErrors.confirmPassword && (
                <p className="mt-1 text-sm text-red-600">{formErrors.confirmPassword}</p>
              )}
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full"
            >
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </div>

          <p className="text-center text-sm text-gray-600">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-primary-600 hover:text-primary-500">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  )
}

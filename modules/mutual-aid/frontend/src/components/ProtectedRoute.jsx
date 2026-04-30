import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

// TEMPORARY: Disable auth for testing - set to false to re-enable
const AUTH_DISABLED = true

export function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  const authDisabled = AUTH_DISABLED || (
    import.meta.env.VITE_AUTH_DISABLED &&
    import.meta.env.VITE_AUTH_DISABLED.toString().toLowerCase() === 'true'
  )

  if (authDisabled) {
    return children
  }

  if (!isAuthenticated) {
    // Redirect to login if not authenticated
    return <Navigate to="/login" replace />
  }

  return children
}

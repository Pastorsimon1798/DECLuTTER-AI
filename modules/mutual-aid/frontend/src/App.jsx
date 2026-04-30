import { Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/layout/Layout'
import { ProtectedRoute } from './components/ProtectedRoute'
import ErrorBoundary from './components/ErrorBoundary'

// Initialize i18n
import './i18n/config'

// Auth pages
import { LoginPage } from './features/auth/LoginPage'
import { RegisterPage } from './features/auth/RegisterPage'

// Dashboard
import { DashboardPage } from './features/dashboard/DashboardPage'

// Posts pages (Project 1: Needs & Offers Board)
import { PostsListPage } from './features/posts/PostsListPage'
import { CreatePostPage } from './features/posts/CreatePostPage'
import { PostDetailPage } from './features/posts/PostDetailPage'
import { MyPostsPage } from './features/posts/MyPostsPage'
import { MatchesPage } from './features/posts/MatchesPage'

// Shifts pages (Project 3: Volunteer Scheduling - Phase 2)
import ShiftCalendarPage from './features/shifts/ShiftCalendarPage'
import ShiftDetailPage from './features/shifts/ShiftDetailPage'
import MyShiftsPage from './features/shifts/MyShiftsPage'
import CreateShiftPage from './features/shifts/CreateShiftPage'

// Resources pages (Project 10: Pantry Locator - Phase 3)
import ResourceSearchPage from './features/resources/ResourceSearchPage'
import ResourceDetailPage from './features/resources/ResourceDetailPage'

// Pods pages (Project 2: Pods/Micro-Circles - Phase 4)
import PodsListPage from './features/pods/PodsListPage'
import CreatePodPage from './features/pods/CreatePodPage'
import PodDetailPage from './features/pods/PodDetailPage'
import CheckInPage from './features/pods/CheckInPage'
import SOSPage from './features/pods/SOSPage'
import PodPostsPage from './features/pods/PodPostsPage'

// Loading component while translations load
const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p className="text-gray-600">Loading...</p>
    </div>
  </div>
);

function App() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingFallback />}>
        <Router>
        <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected routes with layout */}
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          {/* Dashboard */}
          <Route path="/" element={<DashboardPage />} />
          <Route path="/dashboard" element={<Navigate to="/" replace />} />

          {/* Project 1: Needs & Offers Board */}
          <Route path="/posts" element={<PostsListPage />} />
          <Route path="/posts/create" element={<CreatePostPage />} />
          <Route path="/posts/my" element={<MyPostsPage />} />
          <Route path="/posts/:id" element={<PostDetailPage />} />

          {/* Matches */}
          <Route path="/matches" element={<MatchesPage />} />

          {/* Project 3: Volunteer Scheduling (Phase 2) */}
          <Route path="/shifts" element={<ShiftCalendarPage />} />
          <Route path="/shifts/create" element={<CreateShiftPage />} />
          <Route path="/shifts/my-shifts" element={<MyShiftsPage />} />
          <Route path="/shifts/:id" element={<ShiftDetailPage />} />

          {/* Project 10: Pantry Locator (Phase 3) */}
          <Route path="/resources" element={<ResourceSearchPage />} />
          <Route path="/resources/:id" element={<ResourceDetailPage />} />

          {/* Project 2: Pods/Micro-Circles (Phase 4) */}
          <Route path="/pods" element={<PodsListPage />} />
          <Route path="/pods/create" element={<CreatePodPage />} />
          <Route path="/pods/:id" element={<PodDetailPage />} />
          <Route path="/pods/:id/check-in" element={<CheckInPage />} />
          <Route path="/pods/:id/sos" element={<SOSPage />} />
          <Route path="/pods/:id/posts/:postId" element={<PodPostsPage />} />
        </Route>

        {/* 404 */}
        <Route path="*" element={<div className="p-8"><h1 className="text-2xl">404 - Page Not Found</h1></div>} />
      </Routes>
    </Router>
      </Suspense>
    </ErrorBoundary>
  )
}

export default App

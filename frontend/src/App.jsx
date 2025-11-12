import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/layout/Layout'
import { ProtectedRoute } from './components/ProtectedRoute'

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

// Placeholder pages for future phases
const ShiftsPage = () => <div className="p-8"><h1 className="text-3xl font-bold">Volunteer Shifts</h1><p className="mt-4">Coming soon - Phase 2</p></div>
const PodsPage = () => <div className="p-8"><h1 className="text-3xl font-bold">Pods</h1><p className="mt-4">Coming soon - Phase 4</p></div>
const ResourcesPage = () => <div className="p-8"><h1 className="text-3xl font-bold">Pantry Locator</h1><p className="mt-4">Coming soon - Phase 3</p></div>

function App() {
  return (
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
          <Route path="/shifts" element={<ShiftsPage />} />
          <Route path="/shifts/:id" element={<ShiftsPage />} />

          {/* Project 2: Pods (Phase 4) */}
          <Route path="/pods" element={<PodsPage />} />
          <Route path="/pods/:id" element={<PodsPage />} />

          {/* Project 10: Pantry Locator (Phase 3) */}
          <Route path="/resources" element={<ResourcesPage />} />
          <Route path="/resources/:id" element={<ResourcesPage />} />
        </Route>

        {/* 404 */}
        <Route path="*" element={<div className="p-8"><h1 className="text-2xl">404 - Page Not Found</h1></div>} />
      </Routes>
    </Router>
  )
}

export default App

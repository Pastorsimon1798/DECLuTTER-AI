import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/layout/Layout'
import { LoginPage } from './features/auth/LoginPage'
import { RegisterPage } from './features/auth/RegisterPage'

// Placeholder pages - will be implemented as we progress through Phase 1
const DashboardPage = () => <div className="p-8"><h1 className="text-3xl font-bold">Dashboard</h1><p className="mt-4">Welcome to CommunityCircle!</p></div>
const PostsPage = () => <div className="p-8"><h1 className="text-3xl font-bold">Needs & Offers</h1><p className="mt-4">Posts list coming soon</p></div>
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
        <Route element={<Layout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/dashboard" element={<Navigate to="/" replace />} />

          {/* Project 1: Needs & Offers Board */}
          <Route path="/posts" element={<PostsPage />} />
          <Route path="/posts/:id" element={<PostsPage />} />

          {/* Project 3: Volunteer Scheduling */}
          <Route path="/shifts" element={<ShiftsPage />} />
          <Route path="/shifts/:id" element={<ShiftsPage />} />

          {/* Project 2: Pods */}
          <Route path="/pods" element={<PodsPage />} />
          <Route path="/pods/:id" element={<PodsPage />} />

          {/* Project 10: Pantry Locator */}
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

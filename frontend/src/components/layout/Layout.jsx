import { useState } from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { Home, Search, Users, MessageCircle, LogOut, User as UserIcon, FileText, Calendar, MapPin } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import LanguageSelector from '../LanguageSelector'

export function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const [showUserMenu, setShowUserMenu] = useState(false)

  const navigation = [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Posts', href: '/posts', icon: Search },
    { name: 'Resources', href: '/resources', icon: MapPin },
    { name: 'Shifts', href: '/shifts', icon: Users },
  ]

  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(path)
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen flex-col">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="text-2xl">🤝</div>
              <h1 className="text-xl font-bold text-gray-900">CommunityCircle</h1>
            </div>
            <nav className="hidden md:flex items-center gap-6">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center gap-2 text-sm font-medium transition-colors ${
                    isActive(item.href)
                      ? 'text-primary-600'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <item.icon size={20} />
                  {item.name}
                </Link>
              ))}
            </nav>
            <div className="flex items-center gap-4">
              <Link to="/matches" className="text-gray-600 hover:text-gray-900 relative">
                <span className="sr-only">Matches</span>
                <MessageCircle size={24} />
              </Link>

              {/* Language selector */}
              <LanguageSelector variant="dropdown" />

              {/* User menu */}
              <div className="relative">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-2 rounded-lg p-2 hover:bg-gray-100"
                >
                  <UserIcon size={20} className="text-gray-600" />
                  <span className="hidden md:block text-sm font-medium text-gray-700">
                    {user?.pseudonym}
                  </span>
                </button>

                {/* Dropdown menu */}
                {showUserMenu && (
                  <>
                    {/* Backdrop */}
                    <div
                      className="fixed inset-0 z-10"
                      onClick={() => setShowUserMenu(false)}
                    />

                    {/* Menu */}
                    <div className="absolute right-0 z-20 mt-2 w-48 rounded-lg border border-gray-200 bg-white shadow-lg">
                      <div className="p-3 border-b border-gray-200">
                        <p className="text-sm font-semibold text-gray-900">{user?.pseudonym}</p>
                        <p className="text-xs text-gray-500">{user?.email || 'No email'}</p>
                      </div>

                      <div className="py-1">
                        <Link
                          to="/posts/my"
                          className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          onClick={() => setShowUserMenu(false)}
                        >
                          <FileText size={16} />
                          My Posts
                        </Link>
                        <Link
                          to="/matches"
                          className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          onClick={() => setShowUserMenu(false)}
                        >
                          <MessageCircle size={16} />
                          My Matches
                        </Link>
                        <Link
                          to="/shifts/my-shifts"
                          className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          onClick={() => setShowUserMenu(false)}
                        >
                          <Calendar size={16} />
                          My Shifts
                        </Link>
                      </div>

                      <div className="border-t border-gray-200 py-1">
                        <button
                          onClick={handleLogout}
                          className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-700 hover:bg-red-50"
                        >
                          <LogOut size={16} />
                          Logout
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto bg-gray-50">
        <Outlet />
      </main>

      {/* Mobile bottom navigation */}
      <nav className="border-t border-gray-200 bg-white md:hidden">
        <div className="flex items-center justify-around py-2">
          {navigation.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className={`flex flex-col items-center gap-1 px-3 py-2 text-xs ${
                isActive(item.href)
                  ? 'text-primary-600'
                  : 'text-gray-600'
              }`}
            >
              <item.icon size={24} />
              <span>{item.name}</span>
            </Link>
          ))}
        </div>
      </nav>
    </div>
  )
}

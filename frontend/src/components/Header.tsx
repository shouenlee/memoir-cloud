import { Link, useLocation } from 'react-router-dom'
import ThemeToggle from './ThemeToggle'

interface HeaderProps {
  years: number[]
}

export default function Header({ years }: HeaderProps) {
  const location = useLocation()
  const currentYear = parseInt(location.pathname.slice(1)) || years[0]

  return (
    <header className="sticky top-0 z-40 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-700">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <svg
              className="w-8 h-8 text-blue-500"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect width="18" height="18" x="3" y="3" rx="2" ry="2" />
              <circle cx="9" cy="9" r="2" />
              <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
            </svg>
            <span className="text-xl font-semibold">Memoir Cloud</span>
          </Link>

          {/* Year tabs */}
          <nav className="hidden md:flex items-center space-x-1">
            {years.map((year) => (
              <Link
                key={year}
                to={`/${year}`}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors
                  ${
                    currentYear === year
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
              >
                {year}
              </Link>
            ))}
          </nav>

          {/* Mobile year selector + theme toggle */}
          <div className="flex items-center space-x-2">
            {/* Mobile dropdown */}
            <select
              value={currentYear}
              onChange={(e) => {
                window.location.href = `/${e.target.value}`
              }}
              className="md:hidden px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-sm font-medium"
            >
              {years.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>

            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  )
}

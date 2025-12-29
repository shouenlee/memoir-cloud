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
          {/* Spacer for layout balance */}
          <div className="w-8" />

          {/* Year tabs */}
          <nav className="hidden md:flex items-center space-x-1">
            {years.map((year) => (
              <Link
                key={year}
                to={`/${year}`}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors
                  ${
                    currentYear === year
                      ? 'bg-gray-800 dark:bg-gray-200 text-white dark:text-gray-900'
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

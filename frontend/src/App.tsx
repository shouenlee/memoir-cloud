import { Routes, Route, Navigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import Header from './components/Header'
import Gallery from './pages/Gallery'
import { fetchYears } from './services/api'

function App() {
  const { data: yearsData, isLoading } = useQuery({
    queryKey: ['years'],
    queryFn: fetchYears,
  })

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    )
  }

  const years = yearsData?.years ?? []
  const defaultYear = yearsData?.default ?? new Date().getFullYear()

  return (
    <div className="min-h-screen">
      <Header years={years} />
      <main className="container mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Navigate to={`/${defaultYear}`} replace />} />
          <Route path="/:year" element={<Gallery />} />
        </Routes>
      </main>
    </div>
  )
}

export default App

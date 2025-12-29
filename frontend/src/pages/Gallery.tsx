import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { useInfiniteQuery } from '@tanstack/react-query'
import { fetchPhotos } from '../services/api'
import { trackPageView } from '../services/telemetry'
import { Photo } from '../types'
import QuarterSection from '../components/QuarterSection'
import Lightbox from '../components/Lightbox'
import LoadingSkeleton from '../components/LoadingSkeleton'
import InfiniteScrollTrigger from '../components/InfiniteScrollTrigger'

export default function Gallery() {
  const { year: yearParam } = useParams()
  const year = parseInt(yearParam || '') || new Date().getFullYear()
  
  const [selectedPhoto, setSelectedPhoto] = useState<Photo | null>(null)

  // Track page view on year change
  useEffect(() => {
    trackPageView(year)
  }, [year])

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
  } = useInfiniteQuery({
    queryKey: ['photos', year],
    queryFn: ({ pageParam }) => fetchPhotos(year, pageParam),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) =>
      lastPage.hasMore ? lastPage.nextCursor : undefined,
  })

  const loadMore = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage()
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

  // Collect all photos for lightbox navigation
  const allPhotos: Photo[] = data?.pages.flatMap((page) =>
    page.sections.flatMap((section) => section.photos)
  ) ?? []

  const handlePhotoClick = (photo: Photo) => {
    setSelectedPhoto(photo)
  }

  const handleCloseLightbox = () => {
    setSelectedPhoto(null)
  }

  const handleNavigate = (photo: Photo) => {
    setSelectedPhoto(photo)
  }

  if (isLoading) {
    return <LoadingSkeleton />
  }

  if (isError) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500 mb-4">Failed to load photos</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    )
  }

  const sections = data?.pages.flatMap((page) => page.sections) ?? []

  if (sections.length === 0) {
    return (
      <div className="text-center py-12">
        <svg
          className="w-24 h-24 mx-auto text-gray-300 dark:text-gray-600 mb-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1}
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
        <p className="text-gray-500 dark:text-gray-400">No photos for {year}</p>
      </div>
    )
  }

  return (
    <>
      <div className="space-y-2">
        {sections.map((section, index) => (
          <QuarterSection
            key={`${section.quarter}-${index}`}
            section={section}
            onPhotoClick={handlePhotoClick}
          />
        ))}
      </div>

      <InfiniteScrollTrigger
        onIntersect={loadMore}
        isLoading={isFetchingNextPage}
        hasMore={hasNextPage ?? false}
      />

      {selectedPhoto && (
        <Lightbox
          photo={selectedPhoto}
          photos={allPhotos}
          onClose={handleCloseLightbox}
          onNavigate={handleNavigate}
        />
      )}
    </>
  )
}

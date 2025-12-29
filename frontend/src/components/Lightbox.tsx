import { useEffect, useCallback } from 'react'
import { Photo } from '../types'
import { trackPhotoView } from '../services/telemetry'

interface LightboxProps {
  photo: Photo
  photos: Photo[]
  onClose: () => void
  onNavigate: (photo: Photo) => void
}

export default function Lightbox({
  photo,
  photos,
  onClose,
  onNavigate,
}: LightboxProps) {
  const currentIndex = photos.findIndex((p) => p.id === photo.id)

  const goToPrevious = useCallback(() => {
    if (currentIndex > 0) {
      onNavigate(photos[currentIndex - 1])
    }
  }, [currentIndex, photos, onNavigate])

  const goToNext = useCallback(() => {
    if (currentIndex < photos.length - 1) {
      onNavigate(photos[currentIndex + 1])
    }
  }, [currentIndex, photos, onNavigate])

  // Track photo view
  useEffect(() => {
    trackPhotoView(photo.id)
  }, [photo.id])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'Escape':
          onClose()
          break
        case 'ArrowLeft':
          goToPrevious()
          break
        case 'ArrowRight':
          goToNext()
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose, goToPrevious, goToNext])

  // Prevent body scroll when lightbox is open
  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = ''
    }
  }, [])

  return (
    <div
      className="lightbox-overlay animate-fade-in"
      onClick={onClose}
    >
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 p-2 text-white/80 hover:text-white transition-colors z-10"
        aria-label="Close lightbox"
      >
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      {/* Previous button */}
      {currentIndex > 0 && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            goToPrevious()
          }}
          className="absolute left-4 top-1/2 -translate-y-1/2 p-2 text-white/80 hover:text-white transition-colors"
          aria-label="Previous photo"
        >
          <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      )}

      {/* Next button */}
      {currentIndex < photos.length - 1 && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            goToNext()
          }}
          className="absolute right-4 top-1/2 -translate-y-1/2 p-2 text-white/80 hover:text-white transition-colors"
          aria-label="Next photo"
        >
          <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      )}

      {/* Image */}
      <div
        className="max-w-[90vw] max-h-[90vh] animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <img
          src={photo.originalUrl}
          alt={`Photo from ${new Date(photo.takenAt).toLocaleDateString()}`}
          className="max-w-full max-h-[90vh] object-contain rounded-lg shadow-2xl"
        />
      </div>

      {/* Photo info */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-white/80 text-sm">
        {currentIndex + 1} / {photos.length} • {new Date(photo.takenAt).toLocaleDateString()}
      </div>
    </div>
  )
}

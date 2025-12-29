import { Photo } from '../types'

interface PhotoGridProps {
  photos: Photo[]
  onPhotoClick: (photo: Photo) => void
}

export default function PhotoGrid({ photos, onPhotoClick }: PhotoGridProps) {
  return (
    <div className="photo-grid">
      {photos.map((photo) => (
        <div
          key={photo.id}
          className="photo-item aspect-square"
          onClick={() => onPhotoClick(photo)}
        >
          <img
            src={photo.thumbnailUrl}
            alt={`Photo from ${new Date(photo.takenAt).toLocaleDateString()}`}
            loading="lazy"
            className="w-full h-full object-cover"
          />
        </div>
      ))}
    </div>
  )
}

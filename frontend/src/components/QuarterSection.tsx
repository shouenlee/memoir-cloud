import { QuarterSection as QuarterSectionType } from '../types'
import PhotoGrid from './PhotoGrid'
import { Photo } from '../types'

interface QuarterSectionProps {
  section: QuarterSectionType
  onPhotoClick: (photo: Photo) => void
}

export default function QuarterSection({
  section,
  onPhotoClick,
}: QuarterSectionProps) {
  return (
    <section className="mb-12">
      <div className="flex items-center mb-6">
        <div className="flex items-center space-x-2">
          <span className="text-lg text-gray-500 dark:text-gray-400">
            {section.quarter}
          </span>
          <span className="text-gray-400 dark:text-gray-500">·</span>
          <span className="text-lg text-gray-500 dark:text-gray-400">
            {section.label}
          </span>
        </div>
        <div className="ml-4 flex-1 h-px bg-gradient-to-r from-gray-200 dark:from-gray-700 to-transparent" />
      </div>
      <PhotoGrid photos={section.photos} onPhotoClick={onPhotoClick} />
    </section>
  )
}

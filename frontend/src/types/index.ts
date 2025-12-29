// API Response Types

export interface YearsResponse {
  years: number[]
  default: number | null
}

export interface Photo {
  id: string
  thumbnailUrl: string
  originalUrl: string
  takenAt: string
  width: number
  height: number
  aspectRatio: number
}

export interface QuarterSection {
  quarter: string
  label: string
  photos: Photo[]
}

export interface PhotosResponse {
  year: number
  sections: QuarterSection[]
  nextCursor: string | null
  hasMore: boolean
}

export interface ExifData {
  camera?: string
  focalLength?: string
  aperture?: string
  iso?: number
}

export interface PhotoDetail extends Photo {
  exif?: ExifData
}

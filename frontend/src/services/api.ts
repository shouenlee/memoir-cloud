import { YearsResponse, PhotosResponse } from '../types'

// Use environment variable for API base URL, defaulting to /api for local development
const API_BASE = import.meta.env.VITE_API_URL || 'https://memoir-api.icystone-ff15642b.eastus.azurecontainerapps.io/api'

export async function fetchYears(): Promise<YearsResponse> {
  const response = await fetch(`${API_BASE}/years`)
  if (!response.ok) {
    throw new Error('Failed to fetch years')
  }
  return response.json()
}

export async function fetchPhotos(
  year: number,
  cursor?: string,
  limit: number = 50
): Promise<PhotosResponse> {
  const params = new URLSearchParams({ limit: limit.toString() })
  if (cursor) {
    params.append('cursor', cursor)
  }

  const response = await fetch(`${API_BASE}/photos/${year}?${params}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch photos for year ${year}`)
  }
  return response.json()
}

export async function fetchPhotoDetails(photoId: string) {
  const response = await fetch(`${API_BASE}/photo/${photoId}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch photo ${photoId}`)
  }
  return response.json()
}

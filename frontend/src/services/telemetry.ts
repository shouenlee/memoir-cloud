// Generate or retrieve session ID for telemetry
function getSessionId(): string {
  const key = 'memoir_session_id'
  let sessionId = sessionStorage.getItem(key)
  
  if (!sessionId) {
    sessionId = crypto.randomUUID()
    sessionStorage.setItem(key, sessionId)
  }
  
  return sessionId
}

interface TelemetryEvent {
  event: 'page_view' | 'photo_view'
  photoId?: string
  timestamp: string
  sessionId: string
}

// Use the same API base as the main API service
const API_BASE = import.meta.env.VITE_API_URL || 'https://memoir-api.icystone-ff15642b.eastus.azurecontainerapps.io/api'

async function sendTelemetry(event: TelemetryEvent): Promise<void> {
  try {
    await fetch(`${API_BASE}/telemetry`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(event),
    })
  } catch (error) {
    // Silently fail - telemetry should not break the app
    console.debug('Telemetry failed:', error)
  }
}

export function trackPageView(_year: number): void {
  sendTelemetry({
    event: 'page_view',
    timestamp: new Date().toISOString(),
    sessionId: getSessionId(),
  })
}

export function trackPhotoView(photoId: string): void {
  sendTelemetry({
    event: 'photo_view',
    photoId,
    timestamp: new Date().toISOString(),
    sessionId: getSessionId(),
  })
}

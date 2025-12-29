import { useEffect, useRef } from 'react'

interface InfiniteScrollTriggerProps {
  onIntersect: () => void
  isLoading: boolean
  hasMore: boolean
}

export default function InfiniteScrollTrigger({
  onIntersect,
  isLoading,
  hasMore,
}: InfiniteScrollTriggerProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const element = ref.current
    if (!element || !hasMore) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !isLoading && hasMore) {
          onIntersect()
        }
      },
      { threshold: 0.1 }
    )

    observer.observe(element)
    return () => observer.disconnect()
  }, [onIntersect, isLoading, hasMore])

  if (!hasMore) return null

  return (
    <div ref={ref} className="flex justify-center py-8">
      {isLoading ? (
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      ) : (
        <div className="h-8" />
      )}
    </div>
  )
}

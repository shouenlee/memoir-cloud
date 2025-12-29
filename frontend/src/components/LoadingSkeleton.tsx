export default function LoadingSkeleton() {
  return (
    <div className="space-y-12">
      {[1, 2].map((section) => (
        <div key={section}>
          {/* Section header skeleton */}
          <div className="flex items-center mb-6">
            <div className="skeleton w-16 h-10 mr-3" />
            <div className="skeleton w-40 h-6" />
          </div>
          
          {/* Photo grid skeleton */}
          <div className="photo-grid">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="skeleton aspect-square rounded-lg" />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

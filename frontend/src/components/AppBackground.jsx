import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const AppBackground = () => {
  const videoRef = useRef()
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [currentOpacity, setCurrentOpacity] = useState(0.6)
  const fadeTimeoutRef = useRef(null)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    // Set low volume for background ambiance
    video.volume = 0.05 // Very low volume for background

    const handleTimeUpdate = () => {
      const duration = video.duration
      const currentTime = video.currentTime
      
      // Start cool transition 1.5 seconds before end
      if (duration - currentTime <= 1.5 && !isTransitioning) {
        setIsTransitioning(true)
        
        // Smooth fade out
        setCurrentOpacity(0.2)
        
        // Clear any existing timeout
        if (fadeTimeoutRef.current) {
          clearTimeout(fadeTimeoutRef.current)
        }
        
        // Fade back in after loop restarts
        fadeTimeoutRef.current = setTimeout(() => {
          setCurrentOpacity(0.6)
          setIsTransitioning(false)
        }, 2000) // 2 seconds total transition time
      }
    }

    const handleLoadedData = () => {
      // Smooth initial fade in
      setCurrentOpacity(0.6)
    }

    // Auto-restart the video when it ends for seamless loop
    const handleEnded = () => {
      video.currentTime = 0
      video.play()
    }

    video.addEventListener('ended', handleEnded)
    video.addEventListener('timeupdate', handleTimeUpdate)
    video.addEventListener('loadeddata', handleLoadedData)

    return () => {
      video.removeEventListener('ended', handleEnded)
      video.removeEventListener('timeupdate', handleTimeUpdate)
      video.removeEventListener('loadeddata', handleLoadedData)
      if (fadeTimeoutRef.current) {
        clearTimeout(fadeTimeoutRef.current)
      }
    }
  }, [isTransitioning])

  return (
    <div className="fixed inset-0 -z-10 overflow-hidden">
      {/* Video with Cool Transitions */}
      <motion.video
        ref={videoRef}
        className="absolute inset-0 w-full h-full object-cover"
        autoPlay
        muted
        playsInline
        loop
        initial={{ opacity: 0, scale: 1.02 }}
        animate={{ 
          opacity: currentOpacity,
          scale: isTransitioning ? 1.05 : 1
        }}
        transition={{ 
          opacity: { duration: 1.5, ease: "easeInOut" },
          scale: { duration: 2, ease: "easeInOut" }
        }}
      >
        <source src="/background.mp4" type="video/mp4" />
      </motion.video>
      
      {/* Animated Transition Overlay */}
      <AnimatePresence>
        {isTransitioning && (
          <motion.div
            className="absolute inset-0 bg-gradient-radial from-slate-800/50 via-slate-900/70 to-black/80"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 1.2, ease: "easeInOut" }}
          />
        )}
      </AnimatePresence>
      
      {/* Subtle overlay to ensure text readability */}
      <motion.div 
        className="absolute inset-0 bg-slate-900/30"
        animate={{ opacity: isTransitioning ? 0.5 : 0.3 }}
        transition={{ duration: 1.5 }}
      />
      
      {/* Dynamic gradient overlay for better UI integration */}
      <motion.div 
        className="absolute inset-0"
        animate={{ 
          background: isTransitioning 
            ? "linear-gradient(135deg, rgba(51,65,85,0.5), transparent, rgba(51,65,85,0.6))"
            : "linear-gradient(135deg, rgba(51,65,85,0.4), transparent, rgba(51,65,85,0.4))"
        }}
        transition={{ duration: 1.5, ease: "easeInOut" }}
      />

      {/* Floating Particles During Transitions */}
      <AnimatePresence>
        {isTransitioning && (
          <motion.div
            className="absolute inset-0 pointer-events-none overflow-hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 1 }}
          >
            {/* Elegant floating particles */}
            {[...Array(8)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute w-1 h-1 bg-cyan-400/40 rounded-full"
                style={{
                  left: `${15 + (i * 10)}%`,
                  top: `${25 + (i * 8)}%`,
                }}
                animate={{
                  y: [-30, -80, -30],
                  opacity: [0, 0.8, 0],
                  scale: [0.3, 1.5, 0.3]
                }}
                transition={{
                  duration: 2.5,
                  repeat: 1,
                  delay: i * 0.15,
                  ease: "easeInOut"
                }}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default AppBackground
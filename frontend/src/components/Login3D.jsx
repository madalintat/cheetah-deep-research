import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Eye, EyeOff, Mail, Lock, Zap, Sparkles as SparklesIcon } from 'lucide-react'
import { signIn, signUp } from '../lib/supabase'

// Video Background Component
const VideoBackground = ({ isAnimating }) => {
  const videoRef = useRef()
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [isMuted, setIsMuted] = useState(true) // Start muted for autoplay compliance
  const [isHovered, setIsHovered] = useState(false)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    // Set low volume by default
    video.volume = 0.15 // 15% volume (pretty low)
    
    // Don't auto-unmute - let user choose to avoid browser blocking
    // This prevents the video from being paused by browser autoplay policy
    
    // Force play to ensure autoplay works
    const playVideo = async () => {
      try {
        await video.play()
        console.log('✅ Video playing successfully')
      } catch (error) {
        console.log('❌ Video autoplay failed:', error)
      }
    }
    
    playVideo()

    const handleTimeUpdate = () => {
      // More robust check for video duration and timing
      if (video.duration && !isNaN(video.duration) && video.currentTime) {
        const timeLeft = video.duration - video.currentTime
        if (timeLeft <= 1.0 && timeLeft > 0 && !isTransitioning) {
          console.log('🎬 Starting video transition...')
          setIsTransitioning(true)
        }
      }
    }

    const handleEnded = () => {
      console.log('🔄 Video ended, restarting with transition...')
      setIsTransitioning(true)
      
      // Reset and restart with transition
      setTimeout(async () => {
        try {
          video.currentTime = 0
          await video.play()
          console.log('✅ Video restarted successfully')
        } catch (error) {
          console.log('❌ Video restart failed:', error)
          // Fallback: try again after a short delay
          setTimeout(() => {
            video.currentTime = 0
            video.play().catch(e => console.log('Fallback restart failed:', e))
          }, 1000)
        }
        setIsTransitioning(false)
      }, 800) // Slightly longer black transition for smoother effect
    }

    const handleLoadedData = () => {
      console.log('📹 Video loaded, duration:', video.duration)
    }

    const handleError = (e) => {
      console.log('❌ Video error:', e)
      // Try to reload the video
      setTimeout(() => {
        video.load()
        playVideo()
      }, 2000)
    }

    const handlePause = () => {
      console.log('⏸️ Video paused - attempting to resume...')
      // If video gets paused unexpectedly, try to resume
      setTimeout(() => {
        if (video.paused) {
          video.play().catch(e => console.log('Resume failed:', e))
        }
      }, 500)
    }

    // Add all event listeners
    video.addEventListener('timeupdate', handleTimeUpdate)
    video.addEventListener('ended', handleEnded)
    video.addEventListener('loadeddata', handleLoadedData)
    video.addEventListener('error', handleError)
    video.addEventListener('pause', handlePause)

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate)
      video.removeEventListener('ended', handleEnded)
      video.removeEventListener('loadeddata', handleLoadedData)
      video.removeEventListener('error', handleError)
      video.removeEventListener('pause', handlePause)
    }
  }, [])

  const toggleMute = async () => {
    const video = videoRef.current
    if (video) {
      const wasPlaying = !video.paused
      
      try {
        video.muted = !video.muted
        setIsMuted(!isMuted)
        
        // If video was playing but got paused due to unmuting, restart it
        if (wasPlaying && video.paused) {
          await video.play()
          console.log('✅ Video resumed after unmute')
        }
      } catch (error) {
        console.log('⚠️ Mute toggle error:', error)
        // If unmuting fails, keep it muted but ensure video plays
        video.muted = true
        setIsMuted(true)
        if (video.paused) {
          video.play().catch(e => console.log('Play after mute error failed:', e))
        }
      }
    }
  }

  return (
    <>
      <video
        ref={videoRef}
        className="absolute inset-0 w-full h-full object-cover"
        autoPlay
        muted
        playsInline
      >
        <source src="/login-video.mp4" type="video/mp4" />
      </video>
      
      {/* Audio Control Button - Fixed clickability */}
      <motion.div
        className="absolute bottom-2 md:bottom-4 left-4 md:left-8 z-50"
        onHoverStart={() => setIsHovered(true)}
        onHoverEnd={() => setIsHovered(false)}
        initial={{ opacity: 0, scale: 0 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, delay: 1.0 }}
        style={{ pointerEvents: 'all' }}
      >
        <motion.button
          onClick={toggleMute}
          className={`p-3 md:p-4 rounded-xl backdrop-blur-sm border transition-all duration-300 ${
            isMuted 
              ? 'bg-red-500/20 border-red-400/40 text-red-300' 
              : 'bg-cyan-500/20 border-cyan-400/40 text-cyan-300'
          } hover:scale-110 hover:shadow-lg ${
            isMuted ? 'hover:shadow-red-500/25' : 'hover:shadow-cyan-500/25'
          }`}
          whileTap={{ scale: 0.95 }}
        >
          {isMuted ? (
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="currentColor" viewBox="0 0 24 24">
              <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
            </svg>
          ) : (
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="currentColor" viewBox="0 0 24 24">
              <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
            </svg>
          )}
        </motion.button>
        
        {/* Tooltip - Updated position for bottom placement */}
        <AnimatePresence>
          {isHovered && (
            <motion.div
              className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-black/80 backdrop-blur-sm rounded-lg text-white text-xs whitespace-nowrap"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              transition={{ duration: 0.2 }}
            >
              {isMuted ? 'Unmute Audio' : 'Mute Audio'}
              <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-black/80 rotate-45"></div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
      
      {/* Smooth dark transition overlay */}
      <motion.div
        className="absolute inset-0 bg-black z-10"
        initial={{ opacity: 0 }}
        animate={{ opacity: isTransitioning ? 1 : 0 }}
        transition={{ 
          duration: 0.4,
          ease: "easeInOut"
        }}
      />
      
      {/* Extra transition effect for smoother fade */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-b from-black via-gray-900 to-black z-10"
        initial={{ opacity: 0 }}
        animate={{ opacity: isTransitioning ? 0.8 : 0 }}
        transition={{ 
          duration: 0.6,
          ease: "easeInOut",
          delay: isTransitioning ? 0.2 : 0
        }}
      />
      
      {/* Video overlay for better text readability */}
      <div className="absolute inset-0 bg-gradient-to-br from-black/40 via-transparent to-black/60" />
    </>
  )
}

// Main Login Component
const Login3D = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: ''
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')

    try {
      if (isLogin) {
        const { data, error } = await signIn(formData.email, formData.password)
        if (error) throw error
        
        setSuccess('🐆 Login successful! Welcome back, hunter!')
        // Call onLogin immediately to show loading screen
        setTimeout(() => {
          onLogin(data.user)
        }, 100) // Very short delay just for success message to show
      } else {
        // Password confirmation validation for signup
        if (formData.password !== formData.confirmPassword) {
          throw new Error('Passwords do not match. Please ensure both password fields are identical.')
        }
        
        if (formData.password.length < 6) {
          throw new Error('Password must be at least 6 characters long.')
        }
        
        const { data, error } = await signUp(formData.email, formData.password)
        if (error) throw error
        
        setSuccess('🚀 Account created! Check your email to verify, then you can hunt!')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  return (
    <div className="fixed inset-0 overflow-hidden flex flex-col md:flex-row">
      {/* Left Side - Epic Login Form */}
      <div className="relative z-20 w-full md:w-3/5 lg:w-1/2 xl:w-2/5 flex items-center justify-center min-h-screen p-8 bg-gradient-to-br from-black/30 via-slate-900/50 to-black/40 backdrop-blur-xl">
        {/* Animated background particles */}
        <div className="absolute inset-0 overflow-hidden">
          {Array.from({ length: 20 }, (_, i) => (
            <motion.div
              key={i}
              className="absolute w-1 h-1 bg-cyan-400/30 rounded-full"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
              }}
              animate={{
                y: [0, -20, 0],
                opacity: [0.3, 0.8, 0.3],
              }}
              transition={{
                duration: 3 + Math.random() * 2,
                repeat: Infinity,
                delay: Math.random() * 2,
              }}
            />
          ))}
        </div>
        <motion.div
          className="w-full max-w-lg relative z-10"
          initial={{ opacity: 0, x: -100 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          {/* Logo and Title */}
          <motion.div
            className="text-center mb-8"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-gradient-to-r from-cyan-400 to-cyan-500 rounded-xl flex items-center justify-center shadow-2xl shadow-cyan-500/50">
                <svg viewBox="0 0 2048 2048" className="w-10 h-10" fill="currentColor">
                  <path fill="rgb(20,27,67)" d="M 1528.31 408.535 C 1533.58 411.284 1538.72 415.442 1543.89 418.563 C 1568.3 433.309 1593.2 445.903 1622.33 443.814 C 1639.06 442.615 1655.01 441.411 1671.46 445.545 C 1689.17 449.992 1717.5 464.682 1731.56 476.381 C 1738.77 482.379 1739.62 492.4 1743.27 500.521 C 1745.26 504.955 1748.25 508.814 1751.34 512.524 C 1757.61 520.043 1764.46 527.41 1771.96 533.723 C 1778.76 539.445 1800.28 552.338 1803.88 558.43 C 1804.23 572.331 1792 577.01 1785.52 587.437 C 1779.66 596.86 1777.96 609.963 1773.11 620.298 C 1766.2 635.035 1756.53 654.691 1739.84 660.215 C 1727.99 664.134 1716.48 661.171 1705.66 655.965 C 1704.18 644.379 1701 636.714 1691.64 629.062 C 1678.77 618.542 1660.6 612.894 1644.05 614.544 C 1619.54 616.989 1598.32 633.818 1583.4 652.45 C 1564.03 676.619 1561.99 700.249 1565.45 730.164 C 1557.12 721.608 1549.82 712.182 1541.25 703.807 C 1543.72 694.474 1546.85 685.329 1550.62 676.441 C 1562.81 648.274 1586.62 609.642 1616.61 597.869 C 1647.07 585.905 1677.72 595.711 1697.55 621.25 C 1704.09 629.676 1711.55 647.443 1721.91 651.374 C 1728.4 653.856 1735.63 653.466 1741.81 650.303 C 1755.25 643.565 1761.98 628.972 1766.12 615.339 C 1742.79 614.018 1717.19 614.016 1696.31 602.068 C 1683.33 594.639 1674.29 583.23 1658.79 580.055 C 1644.64 577.156 1630.84 581.104 1616.77 582.023 C 1608.92 582.536 1601.4 581.601 1595.39 576.1 C 1583.16 564.902 1588.88 526.112 1588.02 509.783 C 1582.39 525.085 1576.47 542.007 1574.63 558.204 C 1573.52 567.969 1574.55 579.069 1581.16 586.874 C 1585.74 592.282 1591.13 593.817 1597.88 594.406 L 1599.45 594.536 L 1599.92 595.278 C 1598.45 595.506 1596.93 595.704 1595.49 596.059 C 1577.02 600.611 1550.72 647.079 1541.13 663.037 C 1534.58 653.422 1528.64 643.369 1521.51 634.159 C 1495.73 600.811 1461.36 578.185 1420.91 566.9 C 1432.13 573.032 1443.24 579.927 1453.54 587.491 C 1485.92 611.257 1516.64 646.256 1522.88 687.171 C 1516.92 681.076 1510.89 675.142 1504.46 669.543 C 1462.9 633.328 1410.15 604.038 1354.93 597.254 C 1337.02 595.054 1319.08 595.559 1301.12 596.828 C 1314.05 598.63 1326.94 600.629 1339.81 602.826 C 1400.37 613.463 1456.35 642.059 1500.46 684.903 C 1513.07 697.078 1524.4 710.822 1536.01 723.961 C 1556.22 746.841 1576 769.853 1593.5 794.893 C 1592.8 833.652 1588.79 877.44 1578.05 914.833 C 1573.22 931.683 1566.5 947.973 1559.86 964.173 C 1566.57 975.981 1575.48 986.677 1583.66 997.49 C 1593.39 1010.4 1602.96 1023.43 1612.36 1036.58 C 1646.26 1084.53 1681.4 1131.61 1717.73 1177.75 C 1732.89 1197.07 1747.47 1217.03 1764.11 1235.12 C 1771.69 1243.36 1779.1 1251.15 1789.6 1255.51 C 1797.64 1254.01 1804.73 1250.01 1812.64 1248.55 C 1821.09 1246.99 1829.79 1251.27 1836.59 1255.9 C 1850.31 1265.26 1861.1 1279.87 1863.87 1296.47 C 1864.4 1299.64 1864.58 1302.3 1862.56 1305.01 C 1852.9 1308.96 1782.33 1306.92 1767.25 1307 C 1761.16 1298.98 1755.47 1290.66 1748.84 1283.07 C 1735.26 1267.54 1720.02 1253.05 1705.97 1237.9 C 1645.49 1172.63 1588.96 1118.49 1515.16 1068.07 C 1477.3 1042.2 1443.58 1022.13 1400.09 1006.6 C 1403.49 996.806 1406.96 987.01 1409.61 976.976 C 1422.59 927.776 1412.86 877.392 1387.24 833.926 C 1382.48 825.862 1345.04 772.356 1338.09 770.576 C 1343.25 780.291 1351.16 788.718 1357.16 797.98 C 1373.14 822.654 1386.52 850.192 1395.18 878.317 C 1407.64 918.786 1407.91 960.07 1387.84 998.069 L 1378.1 991.302 C 1313.41 1015.35 1254.94 1006.81 1191.45 986.444 C 1154.49 974.591 1119.07 959.744 1083.66 943.898 C 1064.44 935.297 1045.54 925.99 1026.01 918.102 C 1034.22 941.591 1037.23 965.692 1036.11 990.503 C 1034.07 1035.45 1015.4 1080.89 983.139 1112.59 C 973.52 1122.05 962.157 1129.49 952.241 1138.59 C 947.085 1143.33 938.536 1151.39 938.72 1158.81 C 938.82 1162.85 941.844 1168.86 943.373 1172.66 C 953.935 1198.89 969.54 1226.56 990.796 1245.53 C 1005.21 1258.4 1017.63 1251.88 1034.31 1251.51 C 1044.98 1251.28 1054.55 1255.34 1062.14 1262.78 C 1075.46 1275.84 1080.78 1294.11 1081 1312.31 C 1049.96 1312.26 1018.93 1312.48 987.903 1312.95 C 981.272 1304.5 975.727 1295.23 969.191 1286.69 C 958.652 1272.92 946.845 1260.36 935.026 1247.69 C 908.936 1221.23 883.312 1194.08 856.499 1168.36 C 860.598 1164.35 864.582 1160.23 868.447 1156 C 887.063 1135.44 894.333 1110.56 892.868 1083.04 C 891.728 1061.62 885.622 1038.98 868.784 1024.48 C 857.92 1015.13 847.152 1013.13 833.351 1014.15 C 812.053 1042.93 789.7 1066.95 761.392 1088.91 C 791.718 1050.02 816.092 1009.54 835.93 964.251 C 857.829 914.26 874.916 861.434 906.096 816.095 C 923.444 790.87 945.286 772.952 965.949 751.019 L 966.73 750.179 C 894.46 798.619 867.146 872.453 833.324 948.193 C 824.858 967.153 815.226 985.769 805.444 1004.08 C 790.758 1031.56 772.598 1060.31 749.338 1081.42 C 691.585 1133.84 625.06 1108.02 569.244 1149.21 C 559.996 1156.03 551.524 1163.84 543.98 1172.51 C 527.644 1191.31 498.234 1235.96 494.543 1260.22 C 499.333 1268.08 522.075 1262.6 534.435 1275.58 C 545.127 1286.81 545.068 1301.6 544.967 1316.05 L 439.25 1316.38 C 439.13 1300.52 436.62 1264.08 440.659 1250.6 C 443.717 1240.39 454.175 1231.93 460.168 1223.18 C 485.708 1185.9 507.596 1141.42 514.054 1096.57 C 538.322 1093.38 561.095 1088.16 581.454 1073.83 C 639.63 1032.9 665.97 921.605 690.675 856.075 C 700.525 829.947 711.88 804.195 726.845 780.555 C 741.481 757.436 759.118 736.54 780.606 719.458 C 789.021 712.769 798.237 707.086 806.427 700.131 L 807.255 699.416 C 765.638 716.493 737.739 746.823 707.359 778.377 C 678.107 808.759 646.898 837.275 620.188 870.074 C 596.538 899.115 575.884 930.518 553.141 960.23 C 509.457 1017.3 455.142 1069.4 385.338 1091.81 C 319.967 1112.52 249.058 1106.52 188.1 1075.11 C 152.717 1056.68 96.7853 1015.02 85.4564 975.784 C 82.5272 965.641 83.6252 956.092 89.0806 947.037 C 93.4645 939.707 100.655 934.489 108.982 932.594 C 139.091 926.027 152.538 962.471 168.67 980.775 C 179.631 993.213 193.471 1004.24 207.44 1013.12 C 262.873 1048.34 335.317 1049.3 394.535 1023.44 C 488.867 982.229 539.133 885.935 604.789 812.418 C 633.227 780.237 666.273 752.444 702.851 729.943 C 771.355 688.045 848.296 670.206 928.003 670.415 C 953.186 670.481 978.3 672.863 1003.46 673.731 C 1062.03 675.752 1118.31 670.273 1174.06 651.694 C 1261.11 622.688 1327.84 559.325 1404.43 511.916 C 1446.75 485.242 1493.33 465.985 1542.13 454.973 L 1541.71 453.865 L 1541.05 452.009 C 1535.83 437.77 1533.41 422.836 1528.31 408.535 z"/>
                </svg>
              </div>
            </div>
            <h1 className="text-3xl lg:text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-cyan-300 to-blue-400 mb-2">
              Ready to Hunt?
            </h1>
            <p className="text-gray-300 text-base lg:text-lg">
              Elite research awaits →
            </p>
          </motion.div>

          {/* Epic Form Card */}
          <motion.div
            className="bg-black/60 backdrop-blur-3xl rounded-3xl border border-cyan-400/50 p-10 shadow-2xl shadow-cyan-500/40 relative overflow-hidden"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            whileHover={{ scale: 1.02 }}
          >
            {/* Epic glowing background effects */}
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/15 via-blue-500/10 to-purple-500/15 rounded-3xl"></div>
            <motion.div 
              className="absolute inset-0 bg-gradient-to-tr from-transparent via-cyan-400/5 to-transparent rounded-3xl"
              animate={{ rotate: 360 }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            />
            {/* Animated border glow */}
            <motion.div 
              className="absolute inset-0 rounded-3xl border border-cyan-400/30"
              animate={{ 
                boxShadow: [
                  "0 0 20px rgba(34, 211, 238, 0.3)",
                  "0 0 40px rgba(34, 211, 238, 0.6)", 
                  "0 0 20px rgba(34, 211, 238, 0.3)"
                ] 
              }}
              transition={{ duration: 3, repeat: Infinity }}
            />
            <div className="relative z-10">
            {/* Toggle Buttons */}
            <div className="flex bg-gray-800 rounded-lg p-1 mb-6">
              <button
                type="button"
                onClick={() => setIsLogin(true)}
                className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                  isLogin
                    ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Log In
              </button>
              <button
                type="button"
                onClick={() => setIsLogin(false)}
                className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                  !isLogin
                    ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Sign Up
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Email Input */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className="w-full pl-10 pr-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 transition-all"
                    placeholder="hunter@cheetah.ai"
                    required
                  />
                </div>
              </div>

              {/* Password Input */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    className="w-full pl-10 pr-12 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 transition-all"
                    placeholder="••••••••"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              {/* Confirm Password Input - Only show during signup */}
              {!isLogin && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Confirm Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                    <input
                      type={showConfirmPassword ? 'text' : 'password'}
                      name="confirmPassword"
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      className={`w-full pl-10 pr-12 py-3 bg-gray-800 border rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-cyan-500/20 transition-all ${
                        formData.confirmPassword && formData.password !== formData.confirmPassword
                          ? 'border-red-500 focus:border-red-500'
                          : formData.confirmPassword && formData.password === formData.confirmPassword
                          ? 'border-green-500 focus:border-green-500'
                          : 'border-gray-600 focus:border-cyan-500'
                      }`}
                      placeholder="••••••••"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                    >
                      {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                  {/* Password match indicator */}
                  {formData.confirmPassword && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="mt-2 flex items-center space-x-2"
                    >
                      {formData.password === formData.confirmPassword ? (
                        <>
                          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                          <span className="text-xs text-green-400">Passwords match</span>
                        </>
                      ) : (
                        <>
                          <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                          <span className="text-xs text-red-400">Passwords do not match</span>
                        </>
                      )}
                    </motion.div>
                  )}
                </motion.div>
              )}

              {/* Error/Success Messages */}
              <AnimatePresence>
                {error && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="bg-red-500/10 border border-red-500/50 rounded-lg p-3 text-red-400 text-sm"
                  >
                    {error}
                  </motion.div>
                )}
                {success && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="bg-green-500/10 border border-green-500/50 rounded-lg p-3 text-green-400 text-sm"
                  >
                    {success}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Submit Button */}
              <motion.button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 disabled:from-gray-600 disabled:to-gray-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 flex items-center justify-center space-x-2 shadow-lg hover:shadow-cyan-500/25"
                whileHover={!loading ? { scale: 1.02 } : {}}
                whileTap={!loading ? { scale: 0.98 } : {}}
              >
                {loading ? (
                  <>
                    <Zap className="w-5 h-5 animate-spin" />
                    <span>Hunting...</span>
                  </>
                ) : (
                  <>
                    <SparklesIcon className="w-5 h-5" />
                    <span>{isLogin ? 'Log In' : 'Sign Up'}</span>
                  </>
                )}
              </motion.button>
            </form>

            {/* Footer */}
            <div className="mt-6 text-center text-sm text-gray-400">
              <p>
                {isLogin ? "New to the pack? " : "Already hunting? "}
                <button
                  type="button"
                  onClick={() => {
                    setIsLogin(!isLogin)
                    setFormData({
                      email: '',
                      password: '',
                      confirmPassword: ''
                    })
                    setError('')
                    setSuccess('')
                  }}
                  className="text-cyan-400 hover:text-cyan-300 transition-colors underline"
                >
                  {isLogin ? 'Start your journey' : 'Welcome back'}
                </button>
              </p>
            </div>
            </div>
          </motion.div>
        </motion.div>
      </div>

      {/* Right Side - Epic Video Display */}
      <div className="relative w-full md:w-2/5 lg:w-1/2 xl:w-3/5 overflow-hidden min-h-screen md:min-h-0">
        <VideoBackground isAnimating={loading} />
        
        {/* Video Enhancement Overlay - Better blending */}
        <div className="absolute inset-0 bg-gradient-to-l from-transparent via-transparent to-black/30" />
        
        {/* Connection glow effect to login */}
        <motion.div
          className="absolute top-0 left-0 w-8 h-full bg-gradient-to-r from-cyan-400/20 to-transparent hidden md:block"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 2, delay: 1.2 }}
        />
        
        {/* Badass Video Title */}
        <motion.div
          className="absolute top-4 md:top-8 right-4 md:right-8 text-right"
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 1, delay: 0.8 }}
        >
          <div className="bg-black/30 backdrop-blur-sm rounded-xl p-3 md:p-4 border border-cyan-400/30">
            <h3 className="text-lg md:text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-white mb-1">
              Elite Hunters
            </h3>
            <p className="text-cyan-300 text-xs md:text-sm font-medium">
              Advanced AI Research Pack
            </p>
          </div>
        </motion.div>

        {/* Badass Bottom Info */}
        <motion.div
          className="absolute bottom-1 md:bottom-2 right-4 md:right-8 text-right"
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 1.2 }}
        >
          <div className="bg-black/40 backdrop-blur-sm rounded-xl p-3 md:p-4 border border-cyan-400/20">
            <div className="flex items-center justify-end space-x-2 mb-2">
              <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
              <span className="text-cyan-300 text-xs md:text-sm font-medium">LIVE HUNT</span>
            </div>
            <p className="text-white/80 text-xs">
              Next-generation research intelligence
            </p>
          </div>
        </motion.div>

        {/* EPIC glowing separator system */}
        <motion.div
          className="absolute top-0 left-0 w-3 h-full bg-gradient-to-b from-cyan-400 via-blue-500 to-purple-600 hidden md:block"
          initial={{ scaleY: 0 }}
          animate={{ scaleY: 1 }}
          transition={{ duration: 1.5, delay: 0.5 }}
          style={{
            boxShadow: "0 0 30px rgba(34, 211, 238, 0.8), 0 0 60px rgba(59, 130, 246, 0.6)"
          }}
        />
        
        {/* Pulsing energy waves */}
        <motion.div
          className="absolute top-0 left-0 w-8 h-full bg-gradient-to-r from-cyan-400/40 to-transparent hidden md:block"
          animate={{ 
            opacity: [0.2, 0.8, 0.2],
            scaleX: [1, 1.5, 1]
          }}
          transition={{ duration: 2, repeat: Infinity }}
        />
        
        {/* Secondary glow layer */}
        <motion.div
          className="absolute top-0 left-0 w-12 h-full bg-gradient-to-r from-cyan-400/20 via-blue-500/15 to-transparent hidden md:block"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 2, delay: 1 }}
        />
        
        {/* Mobile horizontal border with glow */}
        <motion.div
          className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 md:hidden shadow-lg shadow-cyan-500/50"
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 1.5, delay: 0.5 }}
        />
        
        {/* Mobile glow effect */}
        <motion.div
          className="absolute top-0 left-0 w-full h-6 bg-gradient-to-b from-cyan-400/30 to-transparent md:hidden"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 2, delay: 1 }}
        />
      </div>
    </div>
  )
}

export default Login3D
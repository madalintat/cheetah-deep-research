import { motion } from 'framer-motion'
import { Clock, CheckCircle2, XCircle, Loader2, Cpu } from 'lucide-react'
import { useRef, useEffect } from 'react'

// Running Cheetah Video Component for each hunter
const CheetahVideoIcon = ({ isRunning, hunterColor, size = 48 }) => {
  const videoRef = useRef()
  
  // Color filters for each hunter
  const getColorFilter = (color) => {
    switch (color) {
      case '#06b6d4': // cyan - Hunter 1
        return 'hue-rotate(190deg) saturate(1.4) brightness(1.1) contrast(1.2)'
      case '#10b981': // emerald - Hunter 2
        return 'hue-rotate(100deg) saturate(1.3) brightness(1.0) contrast(1.1)'
      case '#8b5cf6': // violet - Hunter 3
        return 'hue-rotate(280deg) saturate(1.5) brightness(1.2) contrast(1.3)'
      case '#f59e0b': // amber - Hunter 4
        return 'hue-rotate(30deg) saturate(1.6) brightness(1.1) contrast(1.2)'
      default:
        return 'grayscale(1) brightness(0.6) contrast(0.8)'
    }
  }

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    video.muted = true
    video.volume = 0
    video.playbackRate = isRunning ? 1.2 : 0.8 // Faster when running
    
    if (isRunning) {
      video.play().catch(e => console.log('Video play failed:', e))
    } else {
      video.pause()
      // Don't reset time for completed state - with safety checks
      if (video.currentTime === 0 && video.duration && isFinite(video.duration) && video.duration > 0) {
        const targetTime = video.duration * 0.3
        if (isFinite(targetTime) && targetTime >= 0) {
          video.currentTime = targetTime // Show a nice frame when paused
        }
      }
    }
  }, [isRunning])

  return (
    <div 
      className="relative overflow-hidden rounded-lg bg-white"
      style={{ width: 48, height: 48 }}
    >
      <video
        ref={videoRef}
        className="absolute inset-0 w-full h-full object-contain"
        style={{ 
          filter: getColorFilter(hunterColor),
          transform: isRunning ? 'scale(1.0)' : 'scale(0.95)',
          transition: 'all 0.4s ease-out',
          opacity: isRunning ? 1 : 0.8
        }}
        autoPlay={false}
        muted
        loop
        playsInline
        preload="metadata"
      >
        <source src="/loader-cheetah.mp4" type="video/mp4" />
      </video>
      
      {/* Epic glow effect when running */}
      {isRunning && (
        <motion.div 
          className="absolute inset-0 rounded-lg pointer-events-none"
          style={{
            background: `radial-gradient(circle at center, ${hunterColor}30 0%, ${hunterColor}10 50%, transparent 80%)`,
            boxShadow: `inset 0 0 20px ${hunterColor}40, 0 0 25px ${hunterColor}30`
          }}
          animate={{
            opacity: [0.5, 1, 0.5],
            scale: [0.95, 1.05, 0.95]
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      )}
    </div>
  )
}

const AgentCard = ({ agent }) => {
  // Debug logging
  console.log('🔧 AgentCard received agent:', agent);
  
  // Defensive checks for missing agent data
  if (!agent) {
    console.log('❌ Agent is null/undefined');
    return (
      <motion.div className="agent-card border-gray-700 shadow-lg p-6">
        <p className="text-gray-400">Loading agent...</p>
      </motion.div>
    )
  }
  
  const steps = agent.steps || [];
  const agentId = agent.id || 0;
  const agentStatus = agent.status || 'UNKNOWN';
  const agentProgress = agent.progress || 0;
  const agentSubtask = agent.subtask || 'No subtask assigned';
  const agentExecutionTime = agent.executionTime || 0;
  
  console.log('🔧 AgentCard processed data:', {
    agentId,
    agentStatus,
    agentProgress,
    agentSubtask,
    agentExecutionTime
  });
  
  // Define unique colors for each hunter based on their ID
  const getHunterColor = () => {
    const colors = [
      '#06b6d4', // cyan-500 - Hunter 1
      '#10b981', // emerald-500 - Hunter 2  
      '#8b5cf6', // violet-500 - Hunter 3
      '#f59e0b', // amber-500 - Hunter 4
    ];
    return colors[agentId % colors.length];
  };
  
  const getStatusIcon = () => {
    const hunterColor = getHunterColor();
    const status = agentStatus || 'UNKNOWN';
    const isRunning = status === 'INITIALIZING...' || status === 'PROCESSING...';
    
    switch (status) {
      case 'QUEUED':
        return <CheetahVideoIcon isRunning={false} hunterColor="#9ca3af" size={48} />
      case 'INITIALIZING...':
        return <CheetahVideoIcon isRunning={true} hunterColor={hunterColor} size={48} />
      case 'PROCESSING...':
        return <CheetahVideoIcon isRunning={true} hunterColor={hunterColor} size={48} />
      case 'COMPLETED':
        return <CheetahVideoIcon isRunning={true} hunterColor={hunterColor} size={48} />
      default:
        return status.includes('FAILED') 
          ? <XCircle className="w-12 h-12 text-red-500" />
          : <CheetahVideoIcon isRunning={true} hunterColor={hunterColor} size={48} />
    }
  }

  const getStatusColor = () => {
    const status = agentStatus || 'UNKNOWN';
    switch (status) {
      case 'QUEUED': return 'border-gray-700'
      case 'INITIALIZING...': return 'border-neon-blue shadow-neon-blue/20'
      case 'PROCESSING...': return 'border-neon-green shadow-neon-green/20'
      case 'COMPLETED': return 'border-neon-green shadow-neon-green/30'
      default: return status.includes('FAILED') 
        ? 'border-red-500 shadow-red-500/20' 
        : 'border-neon-purple shadow-neon-purple/20'
    }
  }

  const getProgressColor = () => {
    const status = agentStatus || 'UNKNOWN';
    switch (status) {
      case 'COMPLETED': return 'from-neon-green to-green-400'
      case 'PROCESSING...': return 'from-neon-blue to-blue-400'
      default: return status.includes('FAILED') 
        ? 'from-red-500 to-red-400' 
        : 'from-neon-purple to-purple-400'
    }
  }

  return (
    <motion.div
      className={`agent-card ${getStatusColor()} shadow-lg`}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay: agentId * 0.1 }}
      whileHover={{ scale: 1.02 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <motion.div
            className="w-14 h-14 bg-gradient-to-r from-gray-800 to-gray-700 rounded-xl flex items-center justify-center border border-gray-600 overflow-hidden"
            whileHover={{ rotate: 5, scale: 1.05 }}
            transition={{ duration: 0.3 }}
            style={{ backgroundColor: `${getHunterColor()}10` }}
          >
            {getStatusIcon()}
          </motion.div>
          <div>
            <h3 className="font-semibold text-lg">
              {agent.hunter_type ? 
                `${agent.hunter_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} Hunter` : 
                `Hunter ${agentId + 1}`
              }
            </h3>
            <p className="text-sm text-gray-400">{agentStatus}</p>
            {agent.message && (
              <p className="text-xs text-neon-green animate-pulse">
                {agent.message}
              </p>
            )}
            {agent.hunter_type && (
              <p className="text-xs text-cyan-400">
                {agent.hunter_type.replace('_', ' ')}
              </p>
            )}
          </div>
        </div>
        
        {agentExecutionTime > 0 && (
          <div className="text-right">
            <p className="text-sm text-gray-400">Time</p>
            <p className="text-sm font-mono text-neon-green">
              {agentExecutionTime.toFixed(1)}s
            </p>
          </div>
        )}
      </div>

      {/* Subtask */}
      <div className="mb-4">
        <p className="text-sm text-gray-300 mb-2">Hunt Target:</p>
        <p className="text-sm bg-gray-800 rounded-lg p-3 border-l-4 border-neon-blue">
          {agentSubtask}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Progress</span>
          <span>{agentProgress}%</span>
        </div>
        <div className="progress-bar">
          <motion.div
            className={`progress-fill bg-gradient-to-r ${getProgressColor()}`}
            initial={{ width: 0 }}
            animate={{ width: `${agentProgress}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
        </div>
        {agent.current_step && (
          <p className="text-xs text-neon-blue mt-1 animate-pulse">
            🔄 {agent.current_step}
          </p>
        )}
      </div>

      {/* Hunt Steps */}
      {steps.length > 0 && (
        <motion.div
          className="mt-4 p-3 bg-gray-900 rounded-lg border border-gray-700"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          transition={{ duration: 0.5 }}
        >
          <p className="text-xs text-gray-400 mb-2">Hunt Steps:</p>
          <div className="max-h-32 overflow-y-auto space-y-1">
            {steps.map((step, index) => (
              <motion.div
                key={`${agentId}-step-${index}`}
                className="text-xs bg-gray-800 rounded px-2 py-1 border-l-2 border-blue-400"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <span className="text-blue-400">{step.step_type || 'Step'}:</span>{' '}
                <span className="text-gray-300">
                  {step.step_data?.tool && `${step.step_data.tool} - `}
                  {step.step_data?.query || step.step_data?.status || 'Processing...'}
                </span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Catch Preview */}
      {agent.result && agentStatus === 'COMPLETED' && (
        <motion.div
          className="mt-4 p-3 bg-gray-900 rounded-lg border border-gray-700"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          transition={{ duration: 0.5 }}
        >
          <p className="text-xs text-gray-400 mb-2">Catch Preview:</p>
          <p className="text-sm text-gray-300 line-clamp-3">
            {agent.result.length > 150 
              ? `${agent.result.substring(0, 150)}...` 
              : agent.result
            }
          </p>
        </motion.div>
      )}

      {/* Parallel Execution Indicator */}
      {agent.parallel_execution && agentStatus === 'PROCESSING...' && (
        <div className="absolute top-2 right-2">
          <div className="bg-neon-purple/20 text-neon-purple text-xs px-2 py-1 rounded-full border border-neon-purple/30">
            🚀 Parallel
          </div>
        </div>
      )}

      {/* Animated Background Effect */}
      {agentStatus === 'PROCESSING...' && (
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-neon-green/5 to-neon-blue/5 rounded-lg"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          style={{ zIndex: -1 }}
        />
      )}
    </motion.div>
  )
}

export default AgentCard
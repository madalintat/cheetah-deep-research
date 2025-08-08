import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Clock, Search, Trash2, FileText, PlayCircle, Activity, CheckCircle } from 'lucide-react'

const Sidebar = ({ 
  isOpen, 
  onClose, 
  researchHistory, 
  onSelectResearch, 
  onClearHistory,
  activeSessions = [],
  onReconnectSession,
  currentSessionId
}) => {
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const truncateQuery = (query, maxLength = 50) => {
    return query.length > maxLength ? `${query.substring(0, maxLength)}...` : query
  }

  const formatSessionTime = (startTime) => {
    let date
    if (!startTime) return ''
    if (typeof startTime === 'string') {
      // ISO timestamp from Supabase
      date = new Date(startTime)
    } else if (typeof startTime === 'number') {
      // Epoch seconds from local sessions
      date = new Date(startTime * 1000)
    } else {
      date = new Date(startTime)
    }
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getSessionStatusIcon = (session) => {
    if (session.session_id === currentSessionId) {
      return <Activity className="w-4 h-4 text-green-400 animate-pulse" />
    }
    switch (session.status) {
      case 'ongoing':
        return <PlayCircle className="w-4 h-4 text-blue-400" />
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-400" />
      default:
        return <Clock className="w-4 h-4 text-gray-400" />
    }
  }

  const getSessionStatusText = (session) => {
    if (session.session_id === currentSessionId) {
      return 'Connected'
    }
    return session.current_phase === 'executing' ? 
      `${Math.round(session.progress || 0)}% complete` : 
      session.current_phase || session.status
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* Sidebar */}
          <motion.div
            className="fixed left-0 top-0 h-full w-80 bg-gray-900 border-r border-gray-700 z-50 flex flex-col"
            initial={{ x: -320 }}
            animate={{ x: 0 }}
            exit={{ x: -320 }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <div className="flex items-center space-x-2">
                <Search className="w-5 h-5 text-cyan-400" />
                <h2 className="text-lg font-semibold text-white">Trail</h2>
              </div>
              
              <div className="flex items-center space-x-2">
                {/* Clear History Button */}
                {researchHistory.length > 0 && (
                  <motion.button
                    onClick={onClearHistory}
                    className="p-2 text-red-400 hover:text-red-300 hover:bg-red-400/10 rounded-lg transition-colors"
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    title="Clear all history"
                  >
                    <Trash2 className="w-4 h-4" />
                  </motion.button>
                )}
                
                {/* Close Button */}
                <motion.button
                  onClick={onClose}
                  className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <X className="w-4 h-4" />
                </motion.button>
              </div>
            </div>

            {/* Active Sessions */}
            {activeSessions.length > 0 && (
              <div className="border-b border-gray-700">
                <div className="p-4">
                  <h3 className="text-sm font-medium text-gray-300 mb-3 flex items-center">
                    <Activity className="w-4 h-4 mr-2 text-green-400" />
                    Active Research
                  </h3>
                  <div className="space-y-2">
                    {activeSessions.map((session) => (
                      <motion.div
                        key={session.session_id}
                        className={`bg-gray-800 rounded-lg border cursor-pointer transition-all duration-200 ${
                          session.session_id === currentSessionId 
                            ? 'border-green-400/50 bg-green-400/10' 
                            : 'border-gray-700 hover:border-blue-400/50'
                        }`}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => onReconnectSession(session.session_id)}
                      >
                        <div className="p-3">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center space-x-2">
                              {getSessionStatusIcon(session)}
                              <span className="text-xs text-gray-400">
                                {formatSessionTime(session.start_time)}
                              </span>
                            </div>
                            <span className="text-xs text-blue-400">
                              {getSessionStatusText(session)}
                            </span>
                          </div>
                          <p className="text-sm text-white font-medium">
                            {truncateQuery(session.query, 35)}
                          </p>
                          {session.current_phase === 'executing' && session.progress > 0 && (
                            <div className="mt-2">
                              <div className="w-full bg-gray-700 rounded-full h-1">
                                <div 
                                  className="bg-blue-400 h-1 rounded-full transition-all duration-300"
                                  style={{ width: `${session.progress}%` }}
                                />
                              </div>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Trail List */}
            <div className="flex-1 overflow-y-auto min-h-0">
              {researchHistory.length === 0 && activeSessions.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                  <FileText className="w-12 h-12 mb-4 opacity-50" />
                  <p className="text-center">No tracks yet</p>
                  <p className="text-sm text-center">Start hunting to see your trail</p>
                </div>
              ) : (
                <div className="p-4 space-y-3">
                  {researchHistory.map((research) => (
                    <motion.div
                      key={research.id}
                      className="bg-gray-800 rounded-lg border border-gray-700 hover:border-cyan-400/50 cursor-pointer transition-all duration-200"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => onSelectResearch(research)}
                    >
                      <div className="p-4">
                        {/* Query */}
                        <h3 className="text-white font-medium mb-2 leading-tight">
                          {truncateQuery(research.query)}
                        </h3>
                        
                        {/* Stats */}
                        <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
                          <div className="flex items-center space-x-3">
                            <span className="flex items-center space-x-1">
                              <Clock className="w-3 h-3" />
                              <span>{research.totalTime?.toFixed(1)}s</span>
                            </span>
                            <span>{research.agentResults?.length || 0} agents</span>
                          </div>
                          <span>{formatTimestamp(research.timestamp)}</span>
                        </div>

                        {/* Agent Status */}
                        <div className="flex space-x-1">
                          {(research.agentResults || []).map((agent, index) => (
                            <div
                              key={index}
                              className={`w-2 h-2 rounded-full ${
                                agent.status === 'success' 
                                  ? 'bg-green-400' 
                                  : agent.status === 'error' 
                                  ? 'bg-red-400' 
                                  : 'bg-yellow-400'
                              }`}
                            />
                          ))}
                        </div>

                        {/* Result Preview */}
                        {research.finalResult && (
                          <p className="text-xs text-gray-500 mt-2 line-clamp-2">
                            {research.finalResult.substring(0, 100)}...
                          </p>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-gray-700 text-xs text-gray-500 text-center">
              {researchHistory.length} research{researchHistory.length !== 1 ? 'es' : ''} saved locally
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export default Sidebar
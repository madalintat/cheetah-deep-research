import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Brain, Zap, Activity, CheckCircle2, XCircle, Loader2, Menu, LogOut, User } from 'lucide-react'
import AgentCard from './components/AgentCard'
import SearchInput from './components/SearchInput'
import ResultsPanel from './components/ResultsPanel'
import Sidebar from './components/Sidebar'
import Login3D from './components/Login3D'
import AppBackground from './components/AppBackground'
import LoadingScreen from './components/LoadingScreen'
import CheetahLoader from './components/CheetahLoader'
import { supabase, getCurrentUser, signOut, saveResearchToDatabase, getUserResearchHistory } from './lib/supabase'
import './App.css'

function App() {
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [agents, setAgents] = useState([])
  const [currentPhase, setCurrentPhase] = useState('idle') // idle, decomposing, executing, synthesizing, complete
  const [finalResult, setFinalResult] = useState('')
  const [websocket, setWebsocket] = useState(null)
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [researchHistory, setResearchHistory] = useState([])
  const [selectedResearch, setSelectedResearch] = useState(null)
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showLoadingScreen, setShowLoadingScreen] = useState(false)
  const [showLoginLoader, setShowLoginLoader] = useState(false)
  
  // Persistent session state
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const [activeSessions, setActiveSessions] = useState([])
  const [pendingReconnection, setPendingReconnection] = useState(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const wsRef = useRef(null)

  // Check authentication status on mount
  useEffect(() => {
    checkUser()
    
    // Check for ongoing session on page load
    const ongoingSession = sessionStorage.getItem('ongoingSession')
    if (ongoingSession) {
      const sessionData = JSON.parse(ongoingSession)
      setCurrentSessionId(sessionData.sessionId)
      setQuery(sessionData.query)
      setCurrentPhase(sessionData.phase)
      setAgents(sessionData.agents || [])
      setIsSearching(sessionData.isSearching || false)
    }
    
    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN') {
        setUser(session?.user || null)
        if (session?.user) {
          loadUserResearchHistory()
        }
      } else if (event === 'SIGNED_OUT') {
        setUser(null)
        setResearchHistory([])
      }
    })

    return () => subscription.unsubscribe()
  }, [])

  // Handle page refresh
  useEffect(() => {
    const handleBeforeUnload = () => {
      // Save session state before page refresh
      saveSessionState()
    }

    const handlePageShow = (event) => {
      // Check if page was restored from cache (refresh)
      if (event.persisted) {
        setIsRefreshing(true)
        setTimeout(() => {
          setIsRefreshing(false)
          // Reload data after refresh
          loadActiveSessions()
          loadUserResearchHistory()
        }, 2000)
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    window.addEventListener('pageshow', handlePageShow)

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
      window.removeEventListener('pageshow', handlePageShow)
    }
  }, [])

  const checkUser = async () => {
    try {
      const currentUser = await getCurrentUser()
      setUser(currentUser)
      if (currentUser) {
        await loadUserResearchHistory()
      }
    } catch (error) {
      console.error('Error checking user:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLoadingComplete = () => {
    setShowLoadingScreen(false)
  }

  const handleLoginLoadingComplete = () => {
    console.log('🎬 Transition complete - Welcome to the app!')
    setShowLoginLoader(false)
    
    // Now set the user and load history AFTER loading screen completes
    const pendingUser = sessionStorage.getItem('pendingUser')
    if (pendingUser) {
      const userData = JSON.parse(pendingUser)
      setUser(userData)
      loadUserResearchHistory()
      sessionStorage.removeItem('pendingUser')
    }
  }

  const handleUserLogin = (user) => {
    console.log('🎯 Login successful, starting transition to app...', user)
    
    // Store user data temporarily 
    sessionStorage.setItem('pendingUser', JSON.stringify(user))
    
    // Show transition loading screen immediately
    setShowLoginLoader(true)
    
    // User will be set AFTER loading screen completes in handleLoginLoadingComplete
  }

  const loadUserResearchHistory = async () => {
    try {
      const { data, error } = await getUserResearchHistory()
      if (error) throw error
      
      // Transform Supabase data to match local format
      const transformedData = data.map(item => ({
        id: item.id,
        timestamp: new Date(item.created_at).getTime(),
        query: item.query,
        finalResult: item.final_result,
        agentResults: item.agent_results,
        totalTime: item.total_time,
        agents: item.agents
      }))
      
      setResearchHistory(transformedData)
    } catch (error) {
      console.error('Error loading research history:', error)
      // Fallback to localStorage if Supabase fails
      const savedHistory = localStorage.getItem('researchHistory')
      if (savedHistory) {
        try {
          setResearchHistory(JSON.parse(savedHistory))
        } catch (e) {
          console.error('Failed to load research history from localStorage:', e)
        }
      }
    }
  }

  const loadActiveSessions = async () => {
    if (websocket && user && websocket.readyState === WebSocket.OPEN) {
      try {
        websocket.send(JSON.stringify({
          type: "get_active_sessions",
          data: { user_id: user.id }
        }))
      } catch (error) {
        console.error('Error loading active sessions:', error)
      }
    } else {
      console.log('WebSocket not ready or user not authenticated')
    }
  }

  // Initialize WebSocket connection
  useEffect(() => {
    if (!user) return // Only connect WebSocket if user is authenticated
    
    // Prevent multiple connections
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return
    }
    
    const connectWebSocket = () => {
      try {
        // Generate a unique client ID for this session
        const clientId = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
        const ws = new WebSocket(`ws://localhost:8000/ws/${clientId}`)
        
        ws.onopen = () => {
          console.log('WebSocket connected')
          setConnectionStatus('connected')
          setWebsocket(ws)
          wsRef.current = ws
          
          // Load active sessions after connection
          setTimeout(() => {
            loadActiveSessions()
          }, 100)
        }

        ws.onmessage = (event) => {
          const message = JSON.parse(event.data)
          handleWebSocketMessage(message)
        }

        ws.onclose = () => {
          console.log('WebSocket disconnected')
          setConnectionStatus('disconnected')
          setWebsocket(null)
          wsRef.current = null
          
          // Reconnect after delay only if user is still authenticated
          if (user) {
            setTimeout(connectWebSocket, 3000)
          }
        }

        ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          setConnectionStatus('error')
        }
      } catch (error) {
        console.error('Failed to connect WebSocket:', error)
        setConnectionStatus('error')
      }
    }

    connectWebSocket()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [user])

  // Save research to both Supabase and localStorage
  const saveResearchToHistory = async (researchData) => {
    const newResearch = {
      id: Date.now().toString(),
      timestamp: Date.now(),
      query: researchData.query,
      finalResult: researchData.finalResult,
      agentResults: researchData.agentResults,
      totalTime: researchData.totalTime,
      agents: researchData.agents
    }

    // Always save to localStorage as backup
    const updatedHistory = [newResearch, ...researchHistory].slice(0, 50)
    setResearchHistory(updatedHistory)
    localStorage.setItem('researchHistory', JSON.stringify(updatedHistory))

    // Save to Supabase if user is authenticated
    if (user) {
      try {
        await saveResearchToDatabase(researchData)
        console.log('Research saved to Supabase successfully')
      } catch (error) {
        console.error('Failed to save research to Supabase:', error)
        // Already saved to localStorage, so continue
      }
    }
  }

  const handleSelectResearch = (research) => {
    setSelectedResearch(research)
    setQuery(research.query || '')
    setFinalResult(research.final_result || research.finalResult || '')
    setAgents(research.agents || [])
    setCurrentPhase('complete')
    setIsSidebarOpen(false)
    setIsSearching(false) // Reset search state when selecting history
  }

  const handleClearHistory = () => {
    setResearchHistory([])
    localStorage.removeItem('researchHistory')
    // TODO: Clear Supabase history as well
  }

  const handleLogout = async () => {
    try {
      await signOut()
      // WebSocket will be cleaned up by useEffect dependency
    } catch (error) {
      console.error('Error signing out:', error)
    }
  }

  // Reset to clean home screen
  const handleGoHome = () => {
    setQuery('')
    setIsSearching(false)
    setAgents([])
    setCurrentPhase('idle')
    setFinalResult('')
    setSelectedResearch(null)
    setIsSidebarOpen(false)
    // Clear ongoing session
    sessionStorage.removeItem('ongoingSession')
    setCurrentSessionId(null)
  }

  const saveSessionState = () => {
    if (currentSessionId && isSearching) {
      const sessionData = {
        sessionId: currentSessionId,
        query: query,
        phase: currentPhase,
        agents: agents,
        isSearching: isSearching
      }
      sessionStorage.setItem('ongoingSession', JSON.stringify(sessionData))
    }
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    
    // Save current session state
    saveSessionState()
    
    // Reload active sessions and history
    await loadActiveSessions()
    await loadUserResearchHistory()
    
    // Add a small delay for the refresh animation
    setTimeout(() => {
      setIsRefreshing(false)
    }, 1000)
  }

  const handleWebSocketMessage = (message) => {
    console.log('WebSocket message:', message)

    switch (message.type) {
      case 'session_created':
        console.log('🔄 Session created:', message.data.session_id)
        setCurrentSessionId(message.data.session_id)
        // Save session state for persistence
        setTimeout(() => saveSessionState(), 100)
        break

      case 'session_reconnected':
        console.log('🔌 Reconnected to session:', message.data.session_id)
        setCurrentSessionId(message.data.session_id)
        setQuery(message.data.query)
        setCurrentPhase(message.data.current_phase)
        setAgents(message.data.agents || [])
        setIsSearching(message.data.status === 'ongoing')
        break

      case 'active_sessions':
        console.log('📋 Active sessions loaded:', message.data.sessions)
        setActiveSessions(message.data.sessions)
        break

      case 'reconnect_failed':
        console.log('❌ Failed to reconnect to session:', message.data.session_id)
        setPendingReconnection(null)
        break
      case 'task_decomposed':
        console.log('🎯 Task decomposed received, setting up agents:', message.data.subtasks)
        setCurrentPhase('executing')
        
        // Initialize agents with subtasks and hunter types (for deep research)
        const initialAgents = message.data.subtasks.map((subtask, index) => ({
          id: index,
          subtask: subtask,
          status: 'QUEUED',
          progress: 0,
          result: null,
          executionTime: 0,
          hunter_type: message.data.hunter_types ? message.data.hunter_types[index] : null,
          research_complexity: message.data.research_complexity || 'standard',
          deep_research: message.data.deep_research || false
        }))
        
        console.log('🃏 Setting agents:', initialAgents)
        console.log('🧠 Deep research enabled:', message.data.deep_research)
        setAgents(initialAgents)
        setIsSearching(true)
        break

      case 'agent_progress':
        console.log('Agent progress update:', message.data) // Debug log
        setAgents(prevAgents => 
          prevAgents.map(agent => 
            agent.id === message.data.agent_id 
              ? { 
                  ...agent, 
                  status: message.data.status,
                  progress: message.data.progress !== undefined ? message.data.progress : getProgressFromStatus(message.data.status),
                  result: message.data.result || agent.result,
                  executionTime: message.data.execution_time || agent.executionTime,
                  hunter_type: message.data.hunter_type || agent.hunter_type,
                  findings_count: message.data.findings_count || agent.findings_count,
                  current_step: message.data.current_step || agent.current_step,
                  message: message.data.message || agent.message,
                  parallel_execution: message.data.parallel_execution || false
                }
              : agent
          )
        )
        // Save session state for persistence
        setTimeout(() => saveSessionState(), 100)
        break

      case 'agent_step':
        console.log('Agent step update:', message.data) // Debug log
        setAgents(prevAgents => 
          prevAgents.map(agent => 
            agent.id === message.data.agent_id 
              ? { 
                  ...agent, 
                  steps: [...(agent.steps || []), {
                    step_type: message.data.step_type,
                    step_data: message.data.step_data,
                    timestamp: message.data.timestamp
                  }]
                }
              : agent
          )
        )
        break

      case 'deep_research_init':
        console.log('🧠 Deep research systems initializing...')
        setCurrentPhase('initializing')
        break

      case 'research_plan_created':
        console.log('📋 Research plan created:', message.data.plan_summary)
        setCurrentPhase('planning')
        break

      case 'parallel_research_start':
        console.log('🚀 Parallel research starting:', message.data)
        setCurrentPhase('parallel_executing')
        break

      case 'agents_launched':
        console.log('🎯 All agents launched simultaneously:', message.data)
        setCurrentPhase('parallel_executing')
        break

      case 'research_phase_start':
        console.log(`🐆 Phase ${message.data.phase} starting: ${message.data.phase_name}`)
        setCurrentPhase(`phase_${message.data.phase}`)
        break

      case 'research_phase_complete':
        console.log(`✅ Phase ${message.data.phase} completed with ${message.data.results_count} results`)
        break

      case 'synthesis_starting':
        setCurrentPhase('synthesizing')
        break

      case 'orchestration_complete':
        setCurrentPhase('complete')
        setFinalResult(message.data.final_result)
        setIsSearching(false)
        setCurrentSessionId(null) // Clear current session as it's completed
        
        // Update agents with final data and save to history
        setAgents(prevAgents => {
          const updatedAgents = prevAgents.map(agent => ({
            ...agent,
            status: agent.result ? 'COMPLETED' : agent.status,
            executionTime: agent.executionTime || 0
          }))
          
          // Save to research history with updated agents
          const completedAgents = updatedAgents.filter(agent => agent.status === 'COMPLETED')
          const totalTime = updatedAgents.reduce((acc, agent) => acc + agent.executionTime, 0)
          
          saveResearchToHistory({
            query: query,
            finalResult: message.data.final_result,
            agentResults: message.data.agent_results,
            totalTime: totalTime > 0 ? totalTime : 5.0,
            agents: updatedAgents,
            completedCount: completedAgents.length,
            huntedMinute: (completedAgents.length / (totalTime > 0 ? totalTime : 5.0) * 60).toFixed(0),
            sessionId: currentSessionId
          })
          
          return updatedAgents
        })
        
        // Refresh active sessions list
        loadActiveSessions()
        break

      case 'research_error':
        setCurrentPhase('error')
        setIsSearching(false)
        console.error('Research error:', message.data.error)
        break
    }
  }

  const getProgressFromStatus = (status) => {
    switch (status) {
      case 'QUEUED': return 0
      case 'INITIALIZING...': return 25
      case 'PROCESSING...': return 50
      case 'COMPLETED': return 100
      default: return status.includes('FAILED') ? 0 : 75
    }
  }

  const handleSearch = async () => {
    if (!query.trim() || !websocket || connectionStatus !== 'connected') return

    console.log('🔍 Starting research for:', query)
    
    // CRITICAL: Set isSearching to true to disable input
    setIsSearching(true)
    setFinalResult('')
    setAgents([])
    setCurrentPhase('decomposing')
    setCurrentSessionId(null) // Reset current session

    const message = {
      type: 'start_research',
      data: { 
        query: query.trim(),
        user_id: user?.id
      }
    }

    websocket.send(JSON.stringify(message))
  }

  const reconnectToSession = (sessionId) => {
    if (websocket) {
      console.log('🔌 Reconnecting to session:', sessionId)
      setPendingReconnection(sessionId)
      
      websocket.send(JSON.stringify({
        type: "reconnect_session",
        data: { session_id: sessionId }
      }))
    }
  }

  const getPhaseIcon = () => {
    switch (currentPhase) {
      case 'decomposing':
        return <Brain className="w-6 h-6 text-neon-blue animate-pulse" />
      case 'executing':
        return <Activity className="w-6 h-6 text-neon-green animate-pulse" />
      case 'synthesizing':
        return <Zap className="w-6 h-6 text-neon-purple animate-pulse" />
      case 'complete':
        return <CheckCircle2 className="w-6 h-6 text-neon-green" />
      case 'error':
        return <XCircle className="w-6 h-6 text-red-500" />
      default:
        return <Search className="w-6 h-6 text-gray-400" />
    }
  }

  const getPhaseText = () => {
    switch (currentPhase) {
      case 'decomposing': return 'Analyzing prey and planning hunt strategy...'
      case 'executing': return 'Pack is hunting in parallel...'
      case 'parallel_executing': return '🚀 All hunters unleashed simultaneously!'
      case 'synthesizing': return 'Gathering the catch from all hunters...'
      case 'complete': return 'Hunt complete!'
      case 'error': return 'Hunt encountered an obstacle'
      default: return 'What are you hunting for?'
    }
  }

  // Show loading screen while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-cyan-400 to-cyan-500 rounded-xl flex items-center justify-center mb-4 mx-auto">
            <svg viewBox="0 0 2048 2048" className="w-10 h-10" fill="currentColor">
              <path fill="rgb(20,27,67)" d="M 1528.31 408.535 C 1533.58 411.284 1538.72 415.442 1543.89 418.563 C 1568.3 433.309 1593.2 445.903 1622.33 443.814 C 1639.06 442.615 1655.01 441.411 1671.46 445.545 C 1689.17 449.992 1717.5 464.682 1731.56 476.381 C 1738.77 482.379 1739.62 492.4 1743.27 500.521 C 1745.26 504.955 1748.25 508.814 1751.34 512.524 C 1757.61 520.043 1764.46 527.41 1771.96 533.723 C 1778.76 539.445 1800.28 552.338 1803.88 558.43 C 1804.23 572.331 1792 577.01 1785.52 587.437 C 1779.66 596.86 1777.96 609.963 1773.11 620.298 C 1766.2 635.035 1756.53 654.691 1739.84 660.215 C 1727.99 664.134 1716.48 661.171 1705.66 655.965 C 1704.18 644.379 1701 636.714 1691.64 629.062 C 1678.77 618.542 1660.6 612.894 1644.05 614.544 C 1619.54 616.989 1598.32 633.818 1583.4 652.45 C 1564.03 676.619 1561.99 700.249 1565.45 730.164 C 1557.12 721.608 1549.82 712.182 1541.25 703.807 C 1543.72 694.474 1546.85 685.329 1550.62 676.441 C 1562.81 648.274 1586.62 609.642 1616.61 597.869 C 1647.07 585.905 1677.72 595.711 1697.55 621.25 C 1704.09 629.676 1711.55 647.443 1721.91 651.374 C 1728.4 653.856 1735.63 653.466 1741.81 650.303 C 1755.25 643.565 1761.98 628.972 1766.12 615.339 C 1742.79 614.018 1717.19 614.016 1696.31 602.068 C 1683.33 594.639 1674.29 583.23 1658.79 580.055 C 1644.64 577.156 1630.84 581.104 1616.77 582.023 C 1608.92 582.536 1601.4 581.601 1595.39 576.1 C 1583.16 564.902 1588.88 526.112 1588.02 509.783 C 1582.39 525.085 1576.47 542.007 1574.63 558.204 C 1573.52 567.969 1574.55 579.069 1581.16 586.874 C 1585.74 592.282 1591.13 593.817 1597.88 594.406 L 1599.45 594.536 L 1599.92 595.278 C 1598.45 595.506 1596.93 595.704 1595.49 596.059 C 1577.02 600.611 1550.72 647.079 1541.13 663.037 C 1534.58 653.422 1528.64 643.369 1521.51 634.159 C 1495.73 600.811 1461.36 578.185 1420.91 566.9 C 1432.13 573.032 1443.24 579.927 1453.54 587.491 C 1485.92 611.257 1516.64 646.256 1522.88 687.171 C 1516.92 681.076 1510.89 675.142 1504.46 669.543 C 1462.9 633.328 1410.15 604.038 1354.93 597.254 C 1337.02 595.054 1319.08 595.559 1301.12 596.828 C 1314.05 598.63 1326.94 600.629 1339.81 602.826 C 1400.37 613.463 1456.35 642.059 1500.46 684.903 C 1513.07 697.078 1524.4 710.822 1536.01 723.961 C 1556.22 746.841 1576 769.853 1593.5 794.893 C 1592.8 833.652 1588.79 877.44 1578.05 914.833 C 1573.22 931.683 1566.5 947.973 1559.86 964.173 C 1566.57 975.981 1575.48 986.677 1583.66 997.49 C 1593.39 1010.4 1602.96 1023.43 1612.36 1036.58 C 1646.26 1084.53 1681.4 1131.61 1717.73 1177.75 C 1732.89 1197.07 1747.47 1217.03 1764.11 1235.12 C 1771.69 1243.36 1779.1 1251.15 1789.6 1255.51 C 1797.64 1254.01 1804.73 1250.01 1812.64 1248.55 C 1821.09 1246.99 1829.79 1251.27 1836.59 1255.9 C 1850.31 1265.26 1861.1 1279.87 1863.87 1296.47 C 1864.4 1299.64 1864.58 1302.3 1862.56 1305.01 C 1852.9 1308.96 1782.33 1306.92 1767.25 1307 C 1761.16 1298.98 1755.47 1290.66 1748.84 1283.07 C 1735.26 1267.54 1720.02 1253.05 1705.97 1237.9 C 1645.49 1172.63 1588.96 1118.49 1515.16 1068.07 C 1477.3 1042.2 1443.58 1022.13 1400.09 1006.6 C 1403.49 996.806 1406.96 987.01 1409.61 976.976 C 1422.59 927.776 1412.86 877.392 1387.24 833.926 C 1382.48 825.862 1345.04 772.356 1338.09 770.576 C 1343.25 780.291 1351.16 788.718 1357.16 797.98 C 1373.14 822.654 1386.52 850.192 1395.18 878.317 C 1407.64 918.786 1407.91 960.07 1387.84 998.069 L 1378.1 991.302 C 1313.41 1015.35 1254.94 1006.81 1191.45 986.444 C 1154.49 974.591 1119.07 959.744 1083.66 943.898 C 1064.44 935.297 1045.54 925.99 1026.01 918.102 C 1034.22 941.591 1037.23 965.692 1036.11 990.503 C 1034.07 1035.45 1015.4 1080.89 983.139 1112.59 C 973.52 1122.05 962.157 1129.49 952.241 1138.59 C 947.085 1143.33 938.536 1151.39 938.72 1158.81 C 938.82 1162.85 941.844 1168.86 943.373 1172.66 C 953.935 1198.89 969.54 1226.56 990.796 1245.53 C 1005.21 1258.4 1017.63 1251.88 1034.31 1251.51 C 1044.98 1251.28 1054.55 1255.34 1062.14 1262.78 C 1075.46 1275.84 1080.78 1294.11 1081 1312.31 C 1049.96 1312.26 1018.93 1312.48 987.903 1312.95 C 981.272 1304.5 975.727 1295.23 969.191 1286.69 C 958.652 1272.92 946.845 1260.36 935.026 1247.69 C 908.936 1221.23 883.312 1194.08 856.499 1168.36 C 860.598 1164.35 864.582 1160.23 868.447 1156 C 887.063 1135.44 894.333 1110.56 892.868 1083.04 C 891.728 1061.62 885.622 1038.98 868.784 1024.48 C 857.92 1015.13 847.152 1013.13 833.351 1014.15 C 812.053 1042.93 789.7 1066.95 761.392 1088.91 C 791.718 1050.02 816.092 1009.54 835.93 964.251 C 857.829 914.26 874.916 861.434 906.096 816.095 C 923.444 790.87 945.286 772.952 965.949 751.019 L 966.73 750.179 C 894.46 798.619 867.146 872.453 833.324 948.193 C 824.858 967.153 815.226 985.769 805.444 1004.08 C 790.758 1031.56 772.598 1060.31 749.338 1081.42 C 691.585 1133.84 625.06 1108.02 569.244 1149.21 C 559.996 1156.03 551.524 1163.84 543.98 1172.51 C 527.644 1191.31 498.234 1235.96 494.543 1260.22 C 499.333 1268.08 522.075 1262.6 534.435 1275.58 C 545.127 1286.81 545.068 1301.6 544.967 1316.05 L 439.25 1316.38 C 439.13 1300.52 436.62 1264.08 440.659 1250.6 C 443.717 1240.39 454.175 1231.93 460.168 1223.18 C 485.708 1185.9 507.596 1141.42 514.054 1096.57 C 538.322 1093.38 561.095 1088.16 581.454 1073.83 C 639.63 1032.9 665.97 921.605 690.675 856.075 C 700.525 829.947 711.88 804.195 726.845 780.555 C 741.481 757.436 759.118 736.54 780.606 719.458 C 789.021 712.769 798.237 707.086 806.427 700.131 L 807.255 699.416 C 765.638 716.493 737.739 746.823 707.359 778.377 C 678.107 808.759 646.898 837.275 620.188 870.074 C 596.538 899.115 575.884 930.518 553.141 960.23 C 509.457 1017.3 455.142 1069.4 385.338 1091.81 C 319.967 1112.52 249.058 1106.52 188.1 1075.11 C 152.717 1056.68 96.7853 1015.02 85.4564 975.784 C 82.5272 965.641 83.6252 956.092 89.0806 947.037 C 93.4645 939.707 100.655 934.489 108.982 932.594 C 139.091 926.027 152.538 962.471 168.67 980.775 C 179.631 993.213 193.471 1004.24 207.44 1013.12 C 262.873 1048.34 335.317 1049.3 394.535 1023.44 C 488.867 982.229 539.133 885.935 604.789 812.418 C 633.227 780.237 666.273 752.444 702.851 729.943 C 771.355 688.045 848.296 670.206 928.003 670.415 C 953.186 670.481 978.3 672.863 1003.46 673.731 C 1062.03 675.752 1118.31 670.273 1174.06 651.694 C 1261.11 622.688 1327.84 559.325 1404.43 511.916 C 1446.75 485.242 1493.33 465.985 1542.13 454.973 L 1541.71 453.865 L 1541.05 452.009 C 1535.83 437.77 1533.41 422.836 1528.31 408.535 z"/>
            </svg>
          </div>
          <Loader2 className="w-8 h-8 text-cyan-400 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Initializing the hunt...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen text-white relative">
      <AppBackground />
      
      {/* Epic Transition Loading Screen - Login to App */}
      <LoadingScreen 
        isVisible={showLoginLoader} 
        onComplete={handleLoginLoadingComplete}
      />
      

      
      {/* Show login screen if not authenticated and not loading */}
      {!showLoginLoader && !user && <Login3D onLogin={handleUserLogin} />}
      
      {/* Cheetah Loader for Refresh */}
      <CheetahLoader isVisible={isRefreshing} />
      
      {/* Main App Content - Only show when user exists and loading is completely done */}
      {!showLoginLoader && user && (
        <div>
      {/* Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        researchHistory={researchHistory}
        onSelectResearch={handleSelectResearch}
        onClearHistory={handleClearHistory}
        activeSessions={activeSessions}
        onReconnectSession={reconnectToSession}
        currentSessionId={currentSessionId}
      />
      
      {/* Top Navigation Bar - Fixed Position */}
      <motion.header 
        className="fixed top-0 left-0 right-0 z-40 bg-gray-900/50 backdrop-blur-sm border-b border-gray-800"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="flex items-center justify-between px-6 py-4">
          {/* Left Side Controls */}
          <div className="flex items-center space-x-4">
            {/* Hamburger Menu Button */}
            <motion.button
              onClick={() => setIsSidebarOpen(true)}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              title="Trail"
            >
              <Menu className="w-6 h-6" />
            </motion.button>
            
            {/* Connection Status */}
            <div className="flex items-center space-x-2 px-3 py-1 bg-gray-800/50 rounded-lg">
              <div className={`w-3 h-3 rounded-full ${
                connectionStatus === 'connected' ? 'bg-green-400 animate-pulse' :
                connectionStatus === 'error' ? 'bg-red-500' : 'bg-gray-500'
              }`} />
              <span className="text-sm text-gray-400">
                {connectionStatus === 'connected' ? 'Connected' : 
                 connectionStatus === 'error' ? 'Error' : 'Offline'}
              </span>
            </div>
            
            {/* Refresh Button */}
            <motion.button
              onClick={handleRefresh}
              className="p-2 text-cyan-400 hover:text-cyan-300 hover:bg-cyan-400/10 rounded-lg transition-colors"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              title="Refresh trail"
              disabled={isRefreshing}
            >
              <motion.svg 
                className="w-4 h-4" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
                animate={isRefreshing ? { rotate: 360 } : {}}
                transition={isRefreshing ? { duration: 1, repeat: Infinity, ease: "linear" } : {}}
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </motion.svg>
            </motion.button>
          </div>

          {/* Center Title */}
          <div className="flex items-center space-x-3">
            <motion.div
              className="w-10 h-10 bg-gradient-to-r from-cyan-400 to-cyan-500 rounded-lg flex items-center justify-center cursor-pointer"
              whileHover={{ scale: 1.05, rotate: 5 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleGoHome}
              title="Home - Clean Reset"
            >
              <svg viewBox="0 0 2048 2048" className="w-7 h-7" fill="currentColor">
                <path fill="rgb(20,27,67)" d="M 1528.31 408.535 C 1533.58 411.284 1538.72 415.442 1543.89 418.563 C 1568.3 433.309 1593.2 445.903 1622.33 443.814 C 1639.06 442.615 1655.01 441.411 1671.46 445.545 C 1689.17 449.992 1717.5 464.682 1731.56 476.381 C 1738.77 482.379 1739.62 492.4 1743.27 500.521 C 1745.26 504.955 1748.25 508.814 1751.34 512.524 C 1757.61 520.043 1764.46 527.41 1771.96 533.723 C 1778.76 539.445 1800.28 552.338 1803.88 558.43 C 1804.23 572.331 1792 577.01 1785.52 587.437 C 1779.66 596.86 1777.96 609.963 1773.11 620.298 C 1766.2 635.035 1756.53 654.691 1739.84 660.215 C 1727.99 664.134 1716.48 661.171 1705.66 655.965 C 1704.18 644.379 1701 636.714 1691.64 629.062 C 1678.77 618.542 1660.6 612.894 1644.05 614.544 C 1619.54 616.989 1598.32 633.818 1583.4 652.45 C 1564.03 676.619 1561.99 700.249 1565.45 730.164 C 1557.12 721.608 1549.82 712.182 1541.25 703.807 C 1543.72 694.474 1546.85 685.329 1550.62 676.441 C 1562.81 648.274 1586.62 609.642 1616.61 597.869 C 1647.07 585.905 1677.72 595.711 1697.55 621.25 C 1704.09 629.676 1711.55 647.443 1721.91 651.374 C 1728.4 653.856 1735.63 653.466 1741.81 650.303 C 1755.25 643.565 1761.98 628.972 1766.12 615.339 C 1742.79 614.018 1717.19 614.016 1696.31 602.068 C 1683.33 594.639 1674.29 583.23 1658.79 580.055 C 1644.64 577.156 1630.84 581.104 1616.77 582.023 C 1608.92 582.536 1601.4 581.601 1595.39 576.1 C 1583.16 564.902 1588.88 526.112 1588.02 509.783 C 1582.39 525.085 1576.47 542.007 1574.63 558.204 C 1573.52 567.969 1574.55 579.069 1581.16 586.874 C 1585.74 592.282 1591.13 593.817 1597.88 594.406 L 1599.45 594.536 L 1599.92 595.278 C 1598.45 595.506 1596.93 595.704 1595.49 596.059 C 1577.02 600.611 1550.72 647.079 1541.13 663.037 C 1534.58 653.422 1528.64 643.369 1521.51 634.159 C 1495.73 600.811 1461.36 578.185 1420.91 566.9 C 1432.13 573.032 1443.24 579.927 1453.54 587.491 C 1485.92 611.257 1516.64 646.256 1522.88 687.171 C 1516.92 681.076 1510.89 675.142 1504.46 669.543 C 1462.9 633.328 1410.15 604.038 1354.93 597.254 C 1337.02 595.054 1319.08 595.559 1301.12 596.828 C 1314.05 598.63 1326.94 600.629 1339.81 602.826 C 1400.37 613.463 1456.35 642.059 1500.46 684.903 C 1513.07 697.078 1524.4 710.822 1536.01 723.961 C 1556.22 746.841 1576 769.853 1593.5 794.893 C 1592.8 833.652 1588.79 877.44 1578.05 914.833 C 1573.22 931.683 1566.5 947.973 1559.86 964.173 C 1566.57 975.981 1575.48 986.677 1583.66 997.49 C 1593.39 1010.4 1602.96 1023.43 1612.36 1036.58 C 1646.26 1084.53 1681.4 1131.61 1717.73 1177.75 C 1732.89 1197.07 1747.47 1217.03 1764.11 1235.12 C 1771.69 1243.36 1779.1 1251.15 1789.6 1255.51 C 1797.64 1254.01 1804.73 1250.01 1812.64 1248.55 C 1821.09 1246.99 1829.79 1251.27 1836.59 1255.9 C 1850.31 1265.26 1861.1 1279.87 1863.87 1296.47 C 1864.4 1299.64 1864.58 1302.3 1862.56 1305.01 C 1852.9 1308.96 1782.33 1306.92 1767.25 1307 C 1761.16 1298.98 1755.47 1290.66 1748.84 1283.07 C 1735.26 1267.54 1720.02 1253.05 1705.97 1237.9 C 1645.49 1172.63 1588.96 1118.49 1515.16 1068.07 C 1477.3 1042.2 1443.58 1022.13 1400.09 1006.6 C 1403.49 996.806 1406.96 987.01 1409.61 976.976 C 1422.59 927.776 1412.86 877.392 1387.24 833.926 C 1382.48 825.862 1345.04 772.356 1338.09 770.576 C 1343.25 780.291 1351.16 788.718 1357.16 797.98 C 1373.14 822.654 1386.52 850.192 1395.18 878.317 C 1407.64 918.786 1407.91 960.07 1387.84 998.069 L 1378.1 991.302 C 1313.41 1015.35 1254.94 1006.81 1191.45 986.444 C 1154.49 974.591 1119.07 959.744 1083.66 943.898 C 1064.44 935.297 1045.54 925.99 1026.01 918.102 C 1034.22 941.591 1037.23 965.692 1036.11 990.503 C 1034.07 1035.45 1015.4 1080.89 983.139 1112.59 C 973.52 1122.05 962.157 1129.49 952.241 1138.59 C 947.085 1143.33 938.536 1151.39 938.72 1158.81 C 938.82 1162.85 941.844 1168.86 943.373 1172.66 C 953.935 1198.89 969.54 1226.56 990.796 1245.53 C 1005.21 1258.4 1017.63 1251.88 1034.31 1251.51 C 1044.98 1251.28 1054.55 1255.34 1062.14 1262.78 C 1075.46 1275.84 1080.78 1294.11 1081 1312.31 C 1049.96 1312.26 1018.93 1312.48 987.903 1312.95 C 981.272 1304.5 975.727 1295.23 969.191 1286.69 C 958.652 1272.92 946.845 1260.36 935.026 1247.69 C 908.936 1221.23 883.312 1194.08 856.499 1168.36 C 860.598 1164.35 864.582 1160.23 868.447 1156 C 887.063 1135.44 894.333 1110.56 892.868 1083.04 C 891.728 1061.62 885.622 1038.98 868.784 1024.48 C 857.92 1015.13 847.152 1013.13 833.351 1014.15 C 812.053 1042.93 789.7 1066.95 761.392 1088.91 C 791.718 1050.02 816.092 1009.54 835.93 964.251 C 857.829 914.26 874.916 861.434 906.096 816.095 C 923.444 790.87 945.286 772.952 965.949 751.019 L 966.73 750.179 C 894.46 798.619 867.146 872.453 833.324 948.193 C 824.858 967.153 815.226 985.769 805.444 1004.08 C 790.758 1031.56 772.598 1060.31 749.338 1081.42 C 691.585 1133.84 625.06 1108.02 569.244 1149.21 C 559.996 1156.03 551.524 1163.84 543.98 1172.51 C 527.644 1191.31 498.234 1235.96 494.543 1260.22 C 499.333 1268.08 522.075 1262.6 534.435 1275.58 C 545.127 1286.81 545.068 1301.6 544.967 1316.05 L 439.25 1316.38 C 439.13 1300.52 436.62 1264.08 440.659 1250.6 C 443.717 1240.39 454.175 1231.93 460.168 1223.18 C 485.708 1185.9 507.596 1141.42 514.054 1096.57 C 538.322 1093.38 561.095 1088.16 581.454 1073.83 C 639.63 1032.9 665.97 921.605 690.675 856.075 C 700.525 829.947 711.88 804.195 726.845 780.555 C 741.481 757.436 759.118 736.54 780.606 719.458 C 789.021 712.769 798.237 707.086 806.427 700.131 L 807.255 699.416 C 765.638 716.493 737.739 746.823 707.359 778.377 C 678.107 808.759 646.898 837.275 620.188 870.074 C 596.538 899.115 575.884 930.518 553.141 960.23 C 509.457 1017.3 455.142 1069.4 385.338 1091.81 C 319.967 1112.52 249.058 1106.52 188.1 1075.11 C 152.717 1056.68 96.7853 1015.02 85.4564 975.784 C 82.5272 965.641 83.6252 956.092 89.0806 947.037 C 93.4645 939.707 100.655 934.489 108.982 932.594 C 139.091 926.027 152.538 962.471 168.67 980.775 C 179.631 993.213 193.471 1004.24 207.44 1013.12 C 262.873 1048.34 335.317 1049.3 394.535 1023.44 C 488.867 982.229 539.133 885.935 604.789 812.418 C 633.227 780.237 666.273 752.444 702.851 729.943 C 771.355 688.045 848.296 670.206 928.003 670.415 C 953.186 670.481 978.3 672.863 1003.46 673.731 C 1062.03 675.752 1118.31 670.273 1174.06 651.694 C 1261.11 622.688 1327.84 559.325 1404.43 511.916 C 1446.75 485.242 1493.33 465.985 1542.13 454.973 L 1541.71 453.865 L 1541.05 452.009 C 1535.83 437.77 1533.41 422.836 1528.31 408.535 z"/>
              </svg>
            </motion.div>
            <div>
              <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-cyan-300">Cheetah</h1>
              <p className="text-sm text-gray-400">Speed-first AI research</p>
            </div>
          </div>
          
          {/* Right Side User Controls */}
          <div className="flex items-center space-x-4">
            {/* User Info */}
            <div className="flex items-center space-x-2">
              <User className="w-5 h-5 text-gray-400" />
              <span className="text-sm text-gray-400">{user?.email}</span>
            </div>
            
            {/* Logout Button */}
            <motion.button
              onClick={handleLogout}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              title="Sign Out"
            >
              <LogOut className="w-5 h-5" />
            </motion.button>
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto p-6 pt-32">
        {/* Search Section */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <SearchInput
            value={query}
            onChange={setQuery}
            onSearch={handleSearch}
            isSearching={isSearching}
            disabled={connectionStatus !== 'connected' || isSearching}
          />
        </motion.div>

        {/* Status Section */}
        <AnimatePresence>
          {(isSearching || finalResult || currentPhase !== 'idle') && (
            <motion.div
              className="mb-8 agent-card"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className="flex items-center space-x-3 mb-4">
                {getPhaseIcon()}
                <div>
                  <h3 className="text-lg font-semibold">Hunt Status</h3>
                  <p className="text-gray-400">{getPhaseText()}</p>
                </div>
              </div>

              {/* Overall Progress */}
              {agents.length > 0 && (
                <div className="progress-bar">
                  <motion.div
                    className="progress-fill bg-gradient-to-r from-neon-green to-neon-blue"
                    initial={{ width: 0 }}
                    animate={{ 
                      width: `${agents.reduce((acc, agent) => acc + agent.progress, 0) / agents.length}%` 
                    }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Agents Grid */}
        <AnimatePresence>
          {agents.length > 0 && (
            <motion.div
              className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.5 }}
            >
              {console.log('🃏 Rendering agent cards, agents count:', agents.length, agents)}
              {agents.map((agent, index) => {
                console.log(`🔍 Agent ${index}:`, agent);
                return <AgentCard key={agent.id || `agent-${index}`} agent={agent} />
              })}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results Panel */}
        <AnimatePresence>
          {finalResult && (
            <ResultsPanel 
              result={finalResult}
              agents={agents}
              researchData={selectedResearch}
            />
          )}
        </AnimatePresence>
      </main>
        </div>
      )}
    </div>
  )
}

export default App
import { motion } from 'framer-motion'
import { CheckCircle2, Clock, FileText, TrendingUp, ExternalLink, Shield, Globe, Award, Download, Copy, Check } from 'lucide-react'
import { useMemo, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const ResultsPanel = ({ result, agents, researchData }) => {
  const [copySuccess, setCopySuccess] = useState(false)
  const [downloadingPdf, setDownloadingPdf] = useState(false)
  const [showResults, setShowResults] = useState(true)
  const [showSources, setShowSources] = useState(true)
  const [showContributions, setShowContributions] = useState(true)
  
  const completedAgents = agents.filter(agent => agent.status === 'COMPLETED')
  const totalTime = agents.reduce((acc, agent) => acc + (agent.executionTime || 0), 0)
  const effectiveTime = totalTime > 0 ? totalTime : 5.0 // Fallback for display
  
  // Use stored statistics if available (from database)
  const displayCompletedCount = researchData?.completed_count || researchData?.completedCount || completedAgents.length
  const displayTotalTime = researchData?.total_time || researchData?.totalTime || effectiveTime
  const displayHuntersPerMinute = researchData?.hunters_per_minute || researchData?.huntedMinute || (displayCompletedCount / displayTotalTime * 60).toFixed(0)

  // Extract sources from the result text and agent results
  const extractSources = () => {
    const sources = new Set()
    const urlRegex = /https?:\/\/[^\s)]+/g
    
    // Extract from main result
    const resultUrls = result.match(urlRegex) || []
    resultUrls.forEach(url => sources.add(url))
    
    // Extract from agent results
    completedAgents.forEach(agent => {
      if (agent.result) {
        const agentUrls = agent.result.match(urlRegex) || []
        agentUrls.forEach(url => sources.add(url))
      }
    })
    
    return Array.from(sources).map(url => ({
      url,
      domain: new URL(url).hostname,
      authority: assessUrlAuthority(url)
    }))
  }

  const assessUrlAuthority = (url) => {
    const domain = url.toLowerCase()
    if (domain.includes('tripadvisor') || domain.includes('booking.com') || domain.includes('expedia')) {
      return { level: 'high', label: 'High Authority', icon: Award, color: 'text-green-400' }
    } else if (domain.includes('gov.') || domain.includes('.edu') || domain.includes('bbc.') || domain.includes('reuters')) {
      return { level: 'verified', label: 'Verified Source', icon: Shield, color: 'text-blue-400' }
    } else if (domain.includes('local') || domain.includes('greece') || domain.includes('crete')) {
      return { level: 'local', label: 'Local Source', icon: Globe, color: 'text-purple-400' }
    }
    return { level: 'standard', label: 'Standard Source', icon: ExternalLink, color: 'text-gray-400' }
  }

  const sources = extractSources()

  // Build compact contribution summary under Sources section
  const contributionsSummary = useMemo(() => {
    if (!completedAgents.length) return []
    return completedAgents.map((agent) => {
      const text = (agent.result || '').slice(0, 400)
      const snippet = text.length === 400 ? text + '…' : text
      return {
        id: agent.id,
        time: agent.executionTime || 0,
        subtask: agent.subtask || '',
        snippet
      }
    })
  }, [completedAgents])

  // Copy research results to clipboard
  const handleCopyToClipboard = async () => {
    const timestamp = new Date().toLocaleString()
    const copyText = `
🐆 CHEETAH RESEARCH REPORT
Generated on: ${timestamp}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 RESEARCH SUMMARY:
• Hunters Completed: ${displayCompletedCount}
• Total Time: ${displayTotalTime.toFixed(1)}s
• Hunters/Minute: ${displayHuntersPerMinute}

🎯 HUNT RESULTS:
${result}

🔗 VERIFIED SOURCES (${sources.length}):
${sources.map(source => `• ${source.domain} - ${source.url}`).join('\n')}

🛡️ HUNTER CONTRIBUTIONS:
${completedAgents.map((agent, index) => 
  `Hunter ${index + 1} (${agent.executionTime?.toFixed(1) || 'N/A'}s):\n${agent.subtask}\nResult: ${agent.result || 'No result available'}\n`
).join('\n')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🐆 Powered by Cheetah - Speed-first AI Research
⚡ Visit: cheetah.ai
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`

    try {
      await navigator.clipboard.writeText(copyText)
      setCopySuccess(true)
      setTimeout(() => setCopySuccess(false), 3000)
    } catch (err) {
      console.error('Failed to copy to clipboard:', err)
    }
  }

  // Download research results as PDF
  const handleDownloadPDF = async () => {
    setDownloadingPdf(true)
    const timestamp = new Date().toLocaleString() // Move timestamp outside try block
    
    try {
      // Use html2pdf library for PDF generation
      const element = document.createElement('div')
      
      element.innerHTML = `
        <div style="font-family: Arial, sans-serif; padding: 40px; background: rgb(26, 26, 26); color: rgb(229, 229, 229); line-height: 1.6;">
          <!-- Header with Cheetah Branding -->
          <div style="text-align: center; border-bottom: 3px solid rgb(6, 182, 212); padding-bottom: 20px; margin-bottom: 30px;">
            <div style="text-align: center; margin-bottom: 10px;">
              <div style="width: 50px; height: 50px; background: rgb(6, 182, 212); border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; margin-right: 15px;">
                <span style="font-size: 24px;">🐆</span>
              </div>
              <h1 style="font-size: 28px; font-weight: bold; color: rgb(6, 182, 212); margin: 0; display: inline;">CHEETAH</h1>
            </div>
            <h2 style="color: rgb(6, 182, 212); font-size: 18px; margin: 0;">AI Research Intelligence Report</h2>
            <p style="color: rgb(156, 163, 175); font-size: 14px; margin: 10px 0 0 0;">Generated on: ${timestamp}</p>
          </div>

          <!-- Research Summary -->
          <div style="background: rgb(45, 45, 45); border-radius: 12px; padding: 20px; margin-bottom: 25px; border-left: 4px solid rgb(6, 182, 212);">
            <h3 style="color: rgb(6, 182, 212); font-size: 18px; margin-bottom: 15px;">
              📊 Research Summary
            </h3>
            <table style="width: 100%; border-collapse: collapse;">
              <tr>
                <td style="width: 33.33%; text-align: center; padding: 15px; background: rgb(26, 26, 26); border-radius: 8px; vertical-align: top;">
                  <div style="color: rgb(16, 185, 129); font-size: 24px; font-weight: bold;">${displayCompletedCount}</div>
                  <div style="color: rgb(156, 163, 175); font-size: 12px;">Hunters Completed</div>
                </td>
                <td style="width: 33.33%; text-align: center; padding: 15px; background: rgb(26, 26, 26); border-radius: 8px; vertical-align: top;">
                  <div style="color: rgb(6, 182, 212); font-size: 24px; font-weight: bold;">${displayTotalTime.toFixed(1)}s</div>
                  <div style="color: rgb(156, 163, 175); font-size: 12px;">Total Time</div>
                </td>
                <td style="width: 33.33%; text-align: center; padding: 15px; background: rgb(26, 26, 26); border-radius: 8px; vertical-align: top;">
                  <div style="color: rgb(139, 92, 246); font-size: 24px; font-weight: bold;">${displayHuntersPerMinute}</div>
                  <div style="color: rgb(156, 163, 175); font-size: 12px;">Hunters/Minute</div>
                </td>
              </tr>
            </table>
          </div>

          <!-- Hunt Results -->
          <div style="background: rgb(45, 45, 45); border-radius: 12px; padding: 20px; margin-bottom: 25px; border-left: 4px solid rgb(16, 185, 129);">
            <h3 style="color: rgb(16, 185, 129); font-size: 18px; margin-bottom: 15px;">🎯 Hunt Results</h3>
            <div style="background: rgb(26, 26, 26); border-radius: 8px; padding: 20px; white-space: pre-wrap; font-size: 14px; line-height: 1.7;">
              ${result.replace(/'/g, '&#39;').replace(/"/g, '&quot;')}
            </div>
          </div>

          <!-- Sources -->
          <div style="background: rgb(45, 45, 45); border-radius: 12px; padding: 20px; margin-bottom: 25px; border-left: 4px solid rgb(245, 158, 11);">
            <h3 style="color: rgb(245, 158, 11); font-size: 18px; margin-bottom: 15px;">🔗 Verified Sources (${sources.length})</h3>
            <div>
              ${sources.map(source => 
                `<div style="background: rgb(26, 26, 26); border-radius: 6px; padding: 12px; margin-bottom: 8px;">
                  <div style="font-weight: bold; color: rgb(229, 229, 229); font-size: 14px;">${source.domain}</div>
                  <div style="color: rgb(156, 163, 175); font-size: 12px; word-break: break-all;">${source.url}</div>
                </div>`
              ).join('')}
            </div>
          </div>

          <!-- Hunter Contributions -->
          <div style="background: rgb(45, 45, 45); border-radius: 12px; padding: 20px; margin-bottom: 25px; border-left: 4px solid rgb(139, 92, 246);">
            <h3 style="color: rgb(139, 92, 246); font-size: 18px; margin-bottom: 15px;">🛡️ Hunter Contributions</h3>
            ${completedAgents.map((agent, index) => 
              `<div style="background: rgb(26, 26, 26); border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                <div style="margin-bottom: 10px;">
                  <h4 style="color: rgb(6, 182, 212); font-size: 16px; margin: 0; display: inline;">Hunter ${index + 1}</h4>
                  <span style="color: rgb(16, 185, 129); font-size: 12px; background: rgba(16, 185, 129, 0.1); padding: 4px 8px; border-radius: 4px; float: right;">${agent.executionTime?.toFixed(1) || 'N/A'}s</span>
                </div>
                <div style="clear: both; color: rgb(156, 163, 175); font-size: 13px; margin-bottom: 8px; font-style: italic;">${agent.subtask.replace(/'/g, '&#39;').replace(/"/g, '&quot;')}</div>
                <div style="color: rgb(229, 229, 229); font-size: 13px; line-height: 1.6;">${(agent.result || 'No result available').replace(/'/g, '&#39;').replace(/"/g, '&quot;')}</div>
              </div>`
            ).join('')}
          </div>

          <!-- Footer -->
          <div style="text-align: center; border-top: 1px solid rgb(55, 65, 81); padding-top: 20px; margin-top: 30px;">
            <div style="color: rgb(6, 182, 212); font-weight: bold; font-size: 16px; margin-bottom: 5px;">🐆 Powered by Cheetah</div>
            <div style="color: rgb(156, 163, 175); font-size: 12px;">Speed-first AI Research Intelligence • cheetah.ai</div>
          </div>
        </div>
      `

      // Dynamically import html2pdf
      const html2pdf = (await import('html2pdf.js')).default
      
      const opt = {
        margin: [10, 10, 10, 10],
        filename: `cheetah-research-${Date.now()}.pdf`,
        image: { type: 'jpeg', quality: 0.9 },
        html2canvas: { 
          scale: 1.5, 
          useCORS: true, 
          backgroundColor: '#1a1a1a',
          allowTaint: true,
          foreignObjectRendering: false,
          logging: false
        },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
      }

      await html2pdf().set(opt).from(element).save()
    } catch (err) {
      console.error('Failed to generate PDF:', err)
      
      // Try fallback with simplified styling
      try {
        console.log('Attempting fallback PDF generation...')
        const simpleElement = document.createElement('div')
        simpleElement.innerHTML = `
          <div style="font-family: Arial, sans-serif; padding: 20px; background: white; color: black;">
            <div style="text-align: center; border-bottom: 2px solid rgb(51, 51, 51); padding-bottom: 20px; margin-bottom: 20px;">
              <h1 style="color: rgb(51, 51, 51); margin: 0;">🐆 CHEETAH RESEARCH REPORT</h1>
              <p style="color: rgb(102, 102, 102); margin: 10px 0;">Generated on: ${timestamp}</p>
            </div>
            
            <div style="margin-bottom: 20px;">
              <h3 style="color: rgb(51, 51, 51);">📊 Research Summary</h3>
              <p>Hunters Completed: ${displayCompletedCount} | Total Time: ${displayTotalTime.toFixed(1)}s | Hunters/Minute: ${displayHuntersPerMinute}</p>
            </div>
            
            <div style="margin-bottom: 20px;">
              <h3 style="color: rgb(51, 51, 51);">🎯 Hunt Results</h3>
              <div style="border: 1px solid rgb(204, 204, 204); padding: 15px; background: rgb(249, 249, 249);">
                ${result.replace(/\n/g, '<br>').replace(/'/g, '&#39;').replace(/"/g, '&quot;')}
              </div>
            </div>
            
            <div style="margin-bottom: 20px;">
              <h3 style="color: rgb(51, 51, 51);">🔗 Sources (${sources.length})</h3>
              ${sources.map(source => 
                `<div style="margin-bottom: 5px; padding: 5px; border-left: 3px solid rgb(204, 204, 204);">
                  <strong>${source.domain}</strong><br><small>${source.url}</small>
                </div>`
              ).join('')}
            </div>
            
            <div style="margin-bottom: 20px;">
              <h3 style="color: rgb(51, 51, 51);">🛡️ Hunter Contributions</h3>
              ${completedAgents.map((agent, index) => 
                `<div style="margin-bottom: 15px; padding: 10px; border: 1px solid rgb(204, 204, 204);">
                  <h4 style="color: rgb(51, 51, 51); margin: 0;">Hunter ${index + 1} (${agent.executionTime?.toFixed(1) || 'N/A'}s)</h4>
                  <p style="font-style: italic; color: rgb(102, 102, 102);">${agent.subtask.replace(/'/g, '&#39;').replace(/"/g, '&quot;')}</p>
                  <p>${(agent.result || 'No result available').replace(/'/g, '&#39;').replace(/"/g, '&quot;')}</p>
                </div>`
              ).join('')}
            </div>
            
            <div style="text-align: center; border-top: 1px solid rgb(204, 204, 204); padding-top: 15px;">
              <p style="color: rgb(102, 102, 102);"><strong>🐆 Powered by Cheetah</strong><br>Speed-first AI Research Intelligence</p>
            </div>
          </div>
        `
        
        const simpleOpt = {
          margin: [10, 10, 10, 10],
          filename: `cheetah-research-simple-${Date.now()}.pdf`,
          image: { type: 'jpeg', quality: 0.8 },
          html2canvas: { scale: 1, backgroundColor: 'white' },
          jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
        }
        
        await html2pdf().set(simpleOpt).from(simpleElement).save()
        console.log('✅ Fallback PDF generated successfully')
      } catch (fallbackErr) {
        console.error('Fallback PDF also failed:', fallbackErr)
        alert('PDF generation failed. Please try copying the results instead.')
      }
    } finally {
      setDownloadingPdf(false)
    }
  }

  // Download compact summary-only PDF
  const handleDownloadSummaryPDF = async () => {
    setDownloadingPdf(true)
    try {
      const element = document.createElement('div')
      const summaryText = (result || '').slice(0, 1200)
      const quickStats = `Hunters Completed: ${displayCompletedCount} | Total Time: ${displayTotalTime.toFixed(1)}s | Hunters/Minute: ${displayHuntersPerMinute}`

      element.innerHTML = `
        <div style="font-family: Arial, sans-serif; padding: 28px; background: #111827; color: #e5e7eb;">
          <h1 style="margin:0 0 6px 0; color:#67e8f9; font-size:22px;">🐆 Cheetah Research Summary</h1>
          <p style="margin:0 0 16px 0; color:#9ca3af; font-size:12px;">${new Date().toLocaleString()}</p>
          <div style="border-left:4px solid #67e8f9; background:#0b1220; padding:12px 14px; border-radius:8px; margin-bottom:14px;">
            <strong style="color:#e5e7eb;">Quick Stats</strong>
            <div style="color:#9ca3af; font-size:12px;">${quickStats}</div>
          </div>
          <div style="border-left:4px solid #22c55e; background:#0b1220; padding:12px 14px; border-radius:8px;">
            <strong style="color:#e5e7eb;">Key Findings (excerpt)</strong>
            <div style="white-space:pre-wrap; color:#d1d5db; font-size:13px; line-height:1.6; margin-top:6px;">${summaryText.replace(/</g, '&lt;')}</div>
          </div>
        </div>
      `

      const html2pdf = (await import('html2pdf.js')).default
      const opt = { margin: [10,10,10,10], filename: `cheetah-summary-${Date.now()}.pdf`, image: { type: 'jpeg', quality: 0.9 }, html2canvas: { scale: 1.2, backgroundColor: '#111827' }, jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' } }
      await html2pdf().set(opt).from(element).save()
    } catch (e) {
      console.error('Summary PDF failed:', e)
    } finally {
      setDownloadingPdf(false)
    }
  }

  return (
    <motion.div
      className="space-y-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      {/* Summary Stats */}
      <motion.div
        className="grid grid-cols-1 md:grid-cols-3 gap-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <div className="agent-card text-center">
          <CheckCircle2 className="w-8 h-8 text-neon-green mx-auto mb-2" />
          <p className="text-2xl font-bold text-neon-green">{displayCompletedCount}</p>
          <p className="text-sm text-gray-400">Hunters Completed</p>
        </div>
        
        <div className="agent-card text-center">
          <Clock className="w-8 h-8 text-neon-blue mx-auto mb-2" />
          <p className="text-2xl font-bold text-neon-blue">{displayTotalTime.toFixed(1)}s</p>
          <p className="text-sm text-gray-400">Total Time</p>
        </div>
        
        <div className="agent-card text-center">
          <TrendingUp className="w-8 h-8 text-neon-purple mx-auto mb-2" />
          <p className="text-2xl font-bold text-neon-purple">
            {displayHuntersPerMinute}
          </p>
          <p className="text-sm text-gray-400">Hunters/Minute</p>
        </div>
      </motion.div>

      {/* Final Result */}
      <motion.div
        className="agent-card border-neon-green shadow-neon-green/20"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.4, duration: 0.6 }}
      >
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <motion.div
              className="w-12 h-12 bg-gradient-to-r from-neon-green to-neon-blue rounded-xl flex items-center justify-center"
              whileHover={{ rotate: 180 }}
              transition={{ duration: 0.5 }}
            >
              <FileText className="w-6 h-6 text-black" />
            </motion.div>
            <div>
              <div className="flex items-center space-x-3">
                <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-cyan-300">Hunt Results</h2>
                <button onClick={() => setShowResults(v => !v)} className="text-xs px-2 py-1 rounded border border-gray-600 text-gray-300 hover:border-cyan-400 hover:text-cyan-400">{showResults ? 'Hide' : 'Show'}</button>
              </div>
              <p className="text-gray-400">Synthesized from {displayCompletedCount} hunter perspectives</p>
            </div>
          </div>
          
          {/* Download & Copy Actions */}
          <div className="flex items-center space-x-3">
            {/* Copy Button */}
            <motion.button
              onClick={handleCopyToClipboard}
              className={`p-3 rounded-lg border transition-all duration-300 ${
                copySuccess 
                  ? 'bg-green-500/20 border-green-400 text-green-400' 
                  : 'bg-gray-800/50 border-gray-600 text-gray-300 hover:border-cyan-400 hover:text-cyan-400 hover:bg-cyan-400/10'
              }`}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              title={copySuccess ? "Copied!" : "Copy to Clipboard"}
            >
              {copySuccess ? (
                <Check className="w-5 h-5" />
              ) : (
                <Copy className="w-5 h-5" />
              )}
            </motion.button>

            {/* PDF Download Button */}
            <motion.button
              onClick={handleDownloadPDF}
              disabled={downloadingPdf}
              className={`p-3 rounded-lg border transition-all duration-300 ${
                downloadingPdf
                  ? 'bg-orange-500/20 border-orange-400 text-orange-400 cursor-not-allowed'
                  : 'bg-gray-800/50 border-gray-600 text-gray-300 hover:border-orange-400 hover:text-orange-400 hover:bg-orange-400/10'
              }`}
              whileHover={!downloadingPdf ? { scale: 1.05 } : {}}
              whileTap={!downloadingPdf ? { scale: 0.95 } : {}}
              title={downloadingPdf ? "Generating PDF..." : "Download as PDF"}
            >
              <Download className={`w-5 h-5 ${downloadingPdf ? 'animate-bounce' : ''}`} />
            </motion.button>

            {/* Summary PDF Button */}
            <motion.button
              onClick={handleDownloadSummaryPDF}
              disabled={downloadingPdf}
              className={`p-3 rounded-lg border transition-all duration-300 ${
                downloadingPdf
                  ? 'bg-green-500/20 border-green-400 text-green-400 cursor-not-allowed'
                  : 'bg-gray-800/50 border-gray-600 text-gray-300 hover:border-green-400 hover:text-green-400 hover:bg-green-400/10'
              }`}
              whileHover={!downloadingPdf ? { scale: 1.05 } : {}}
              whileTap={!downloadingPdf ? { scale: 0.95 } : {}}
              title={downloadingPdf ? 'Generating...' : 'Download Summary PDF'}
            >
              <FileText className={`w-5 h-5 ${downloadingPdf ? 'animate-pulse' : ''}`} />
            </motion.button>
          </div>
        </div>

        {showResults && (
        <motion.div
          className="prose prose-invert max-w-none"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
        >
          <div className="bg-gray-900 rounded-lg p-6 border border-gray-700 prose prose-invert max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{result}</ReactMarkdown>
          </div>
        </motion.div>
        )}

        {/* Sources Section */}
        {sources.length > 0 && (
          <motion.div
            className="mt-6 pt-6 border-t border-gray-700"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
          >
            <div className="flex items-center mb-4 space-x-3">
              <h3 className="text-lg font-semibold flex items-center space-x-2">
                <ExternalLink className="w-5 h-5 text-cyan-400" />
                <span>Sources Used ({sources.length})</span>
              </h3>
              <span className="text-xs bg-cyan-400/10 text-cyan-400 px-2 py-1 rounded-full">All Current & Verified</span>
              <button onClick={() => setShowSources(v => !v)} className="text-xs px-2 py-1 rounded border border-gray-600 text-gray-300 hover:border-cyan-400 hover:text-cyan-400">{showSources ? 'Hide' : 'Show'}</button>
            </div>
            
            {showSources && (
            <div className="grid grid-cols-1 gap-3 mb-6">
              {sources.map((source, index) => {
                const AuthorityIcon = source.authority.icon
                return (
                  <motion.a
                    key={index}
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-3 p-3 bg-gray-900 rounded-lg border border-gray-700 hover:border-cyan-400/50 transition-all group"
                    whileHover={{ scale: 1.01 }}
                    transition={{ duration: 0.2 }}
                  >
                    <AuthorityIcon className={`w-4 h-4 ${source.authority.color}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <p className="font-medium text-white truncate">{source.domain}</p>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          source.authority.level === 'high' ? 'bg-green-400/10 text-green-400' :
                          source.authority.level === 'verified' ? 'bg-blue-400/10 text-blue-400' :
                          source.authority.level === 'local' ? 'bg-purple-400/10 text-purple-400' :
                          'bg-gray-400/10 text-gray-400'
                        }`}>
                          {source.authority.label}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 truncate">{source.url}</p>
                    </div>
                    <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-cyan-400 transition-colors" />
                  </motion.a>
                )
              })}
            </div>
            )}

            {contributionsSummary.length > 0 && (
              <div className="mt-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm text-gray-300">Agent contributions (highlights)</h4>
                  <button onClick={() => setShowContributions(v => !v)} className="text-xs px-2 py-1 rounded border border-gray-600 text-gray-300 hover:border-purple-400 hover:text-purple-400">{showContributions ? 'Hide' : 'Show'}</button>
                </div>
                {showContributions && (
                <div className="space-y-2">
                  {contributionsSummary.map((c) => (
                    <div key={c.id} className="p-3 bg-gray-900 rounded border border-gray-700">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-neon-green font-medium">Hunter {c.id + 1}</span>
                        <span className="text-xs text-gray-400">{c.time?.toFixed(1)}s</span>
                      </div>
                      <p className="text-xs text-gray-400 italic mb-1 line-clamp-1">{c.subtask}</p>
                      <p className="text-sm text-gray-300 line-clamp-3">{c.snippet}</p>
                    </div>
                  ))}
                </div>
                )}
              </div>
            )}
          </motion.div>
        )}

        {/* Agent Contributions */}
        <motion.div
          className="mt-6 pt-6 border-t border-gray-700"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.0 }}
        >
          <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-neon-purple" />
            <span>Hunter Contributions</span>
            <span className="text-xs bg-purple-400/10 text-purple-400 px-2 py-1 rounded-full">
              Deep Research
            </span>
          </h3>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {completedAgents.map((agent) => {
              // Extract URLs from this agent's result
              const agentUrls = (agent.result || '').match(/https?:\/\/[^\s)]+/g) || []
              
              return (
                <motion.div
                  key={agent.id}
                  className="bg-gray-900 rounded-lg p-4 border border-gray-700 hover:border-purple-400/50 transition-all"
                  whileHover={{ scale: 1.01 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <h4 className="font-semibold text-neon-green">Hunter {agent.id + 1}</h4>
                  {agent.hunter_type && (
                    <span className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded-full border border-gray-600 capitalize">{agent.hunter_type.replace(/_/g, ' ')}</span>
                  )}
                      {agentUrls.length > 0 && (
                        <span className="text-xs bg-cyan-400/10 text-cyan-400 px-2 py-1 rounded-full">
                          {agentUrls.length} sources
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-gray-400 font-mono">
                      {agent.executionTime?.toFixed(1) || '0.0'}s
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mb-3 italic">{agent.subtask}</p>
                  <div className="text-sm text-gray-300 max-h-64 overflow-y-auto bg-gray-800 rounded p-3 border border-gray-600">
                    <div className="whitespace-pre-wrap leading-relaxed">
                      {agent.result || "No result available"}
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        </motion.div>
      </motion.div>
    </motion.div>
  )
}

export default ResultsPanel
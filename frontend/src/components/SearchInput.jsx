import { motion } from 'framer-motion'
import { Search, Loader2, Zap } from 'lucide-react'

const SearchInput = ({ value, onChange, onSearch, isSearching, disabled }) => {
  // Check if text is multiline or long enough to warrant bottom positioning
  const isExpandedText = value && (value.split('\n').length > 1 || value.length > 60);
  
  // Calculate dynamic height based on content
  const getTextareaHeight = () => {
    if (!value) return '60px' // Base height
    const lines = value.split('\n').length
    const estimatedLines = Math.max(lines, Math.ceil(value.length / 60)) // Estimate line breaks
    const height = Math.min(Math.max(estimatedLines * 24 + 32, 60), 160) // Min 60px, max 160px
    return `${height}px`
  };
  const handleSubmit = (e) => {
    e.preventDefault()
    if (!disabled && !isSearching && value.trim()) {
      onSearch()
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSubmit(e)
    }
  }

  return (
    <motion.div
      className="w-full max-w-4xl mx-auto"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <form onSubmit={handleSubmit} className="relative research-input">
        <div className="relative">
          {/* Input Field */}
          <motion.textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyPress={handleKeyPress}
                              placeholder="What are you hunting for?"
            disabled={disabled || isSearching}
            rows={1}
            className={`
              w-full px-6 py-4 pl-14 text-lg leading-6
              bg-gray-800 border-2 rounded-xl
              text-white placeholder-gray-400
              focus:outline-none focus:ring-0 focus:shadow-none
              transition-all duration-300 ease-out resize-none
              overflow-hidden smooth-textarea
              ${disabled ? 'border-gray-700 opacity-50' : 
                'border-gray-700 hover:border-gray-600 focus:border-gray-600'}
            `}
            style={{
              height: getTextareaHeight(),
              paddingRight: '4rem', // Reduced padding since button is now below
              paddingBottom: '16px',
              lineHeight: '1.5',
              wordWrap: 'break-word',
              whiteSpace: 'pre-wrap'
            }}
            animate={{
              height: getTextareaHeight()
            }}
            transition={{ duration: 0.2, ease: "easeOut" }}

          />



          {/* Search Icon */}
          <motion.div
            className={`absolute left-4 transition-all duration-300 ${
              isExpandedText ? 'top-4' : 'top-1/2 -translate-y-1/2'
            }`}
            animate={isSearching ? { rotate: 360 } : { rotate: 0 }}
            transition={{ duration: 0.5 }}
          >
            {isSearching ? (
              <Loader2 className="w-6 h-6 text-green-400 animate-spin" />
            ) : (
              <Search className="w-6 h-6 text-gray-400" />
            )}
          </motion.div>


        </div>

        {/* Centered Hunt Button */}
        <div className="flex justify-center mt-4">
          <motion.button
            type="submit"
            disabled={disabled || isSearching || !value.trim()}
            className={`
              px-8 py-3 rounded-xl font-medium text-lg
              flex items-center space-x-2 research-button
              transition-all duration-300
              ${disabled || !value.trim() ? 
                'bg-gray-700 text-gray-500 cursor-not-allowed' :
                isSearching ?
                'bg-green-400 text-black cursor-wait shadow-lg shadow-green-400/30' :
                'bg-gradient-to-r from-cyan-400 to-cyan-500 text-black hover:shadow-lg'}
            `}
            whileHover={!disabled && !isSearching && value.trim() ? { scale: 1.05 } : {}}
            whileTap={!disabled && !isSearching && value.trim() ? { scale: 0.95 } : {}}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
          >
            {isSearching ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Hunting...</span>
              </>
            ) : (
              <>
                <Zap className="w-5 h-5" />
                <span>Hunt</span>
              </>
            )}
          </motion.button>
        </div>

        {/* Hint Text */}
        {disabled && (
          <motion.p
            className="mt-3 text-sm text-gray-400 text-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
          >
            Connecting to Cheetah...
          </motion.p>
        )}
      </form>


    </motion.div>
  )
}

export default SearchInput
# Make It Heavy - AI Research Platform

![Make It Heavy Banner](./readme-cheetah.png)

## 🚀 **The Ultimate AI Research Orchestrator**

**Make It Heavy** is a cutting-edge AI research platform that deploys multiple specialized AI agents to conduct deep, comprehensive research on any topic. Like a pack of digital cheetahs hunting for information across the web, our AI agents work in parallel to deliver lightning-fast, thorough research results.

### ⚡ **Why It's Absolutely Amazing**

- 🐆 **Multi-Agent Orchestration**: Deploy 4+ specialized AI "hunters" that work simultaneously
- 🧠 **Deep Research Mode**: Advanced agents with memory, planning, and collaboration capabilities  
- ⚡ **Real-Time Updates**: Watch your research unfold live with WebSocket connections
- 🔍 **Smart Task Decomposition**: Automatically breaks complex queries into optimal research angles
- 💾 **Persistent Sessions**: Continue research across browser refreshes and disconnections
- 🎯 **Specialized Hunters**: Source scouts, deep analysts, fact checkers, and insight synthesizers
- 🌐 **Multiple Search Engines**: DuckDuckGo, Tavily, and web crawling capabilities
- 🔒 **User Isolation**: Each user's research is private and secured with RLS policies

## 🏗️ **Architecture**

```
Frontend (React + Vite)  ←→  Backend (FastAPI + WebSockets)  ←→  Supabase Database
                  ↓                        ↓
              Research UI           AI Orchestrator
                                         ↓
                              4x Specialized AI Agents
                                    ↓
                              Ollama (Local LLM)
                                    ↓  
                           Web Search Tools + Crawling
```

## 🛠️ **Technologies Used**

### Backend
- **FastAPI** - High-performance async web framework
- **Ollama** - Local LLM inference (llama3.1:8b)
- **WebSockets** - Real-time bidirectional communication
- **Supabase** - PostgreSQL database with real-time features
- **Tavily API** - Advanced web search capabilities
- **Crawl4AI** - Web page content extraction

### Frontend  
- **React 18** - Modern UI framework
- **Vite** - Lightning-fast build tool
- **TailwindCSS** - Utility-first CSS framework
- **Supabase Client** - Real-time database integration

### AI & Research
- **Multi-Agent System** - Parallel AI research orchestration
- **Deep Research Agents** - Memory, planning, and collaboration
- **Hunter Role System** - Specialized agent personalities
- **Research Memory** - Persistent context across sessions
- **Smart Task Decomposition** - Query optimization

## 📋 **Prerequisites**

Before you begin, ensure you have:

- **Python 3.11+** installed
- **Node.js 18+** and npm installed  
- **Ollama** installed and running locally
- **Supabase** account with a project created
- **Tavily API** account (for advanced search)

## 🚀 **Quick Setup Guide**

### 1. **Clone & Install**

```bash
git clone <your-repo-url>
cd make-it-heavy

# Create Python virtual environment
python3 -m venv deep-env
source deep-env/bin/activate  # On Windows: deep-env\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. **Setup Ollama**

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull the required model (in another terminal)
ollama pull llama3.1:8b
```

### 3. **Configure Environment Variables**

```bash
# Create environment file with your API keys
python3 create_env_file.py
```

This creates a `.env` file. Update it with your actual keys:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key_here
SUPABASE_ANON_KEY=your_anon_key_here

# Tavily API Configuration  
TAVILY_API_KEY=tvly-your-api-key-here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

### 4. **Setup Supabase Database**

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Navigate to **SQL Editor** → **New Query**
3. Copy the entire content from `fix_supabase_database.sql`
4. Click **Run** and wait for completion
5. Verify tables are created in **Table Editor**

### 5. **Test Database Connection**

```bash
# Test that everything is working
python3 test_without_auth.py
```

You should see: `🎉 DATABASE IS READY!`

## 🎯 **Launch The Application**

```bash
# Start both backend and frontend
./launch.sh
```

This will:
- ✅ Check that Ollama is running
- 🚀 Start FastAPI backend on `http://localhost:8000`
- 🎨 Start React frontend on `http://localhost:5173`
- 🔗 Connect WebSocket endpoints

## 📱 **How To Use**

### 1. **Access The App**
Open your browser to: http://localhost:5173

### 2. **Authentication**
- Login with Supabase Auth (email/password or OAuth)
- Your research will be private and saved to your account

### 3. **Start Research**
- Enter any research query in the search box
- Example: "Latest trends in AI development 2025"
- Click **Start Research**

### 4. **Watch The Magic**
- See 4 specialized AI agents work in parallel
- Real-time updates as each agent finds information
- Deep research mode with memory and collaboration
- Progress tracking and live results

### 5. **Review Results**
- Comprehensive final report combining all agent findings
- Source citations and verification
- Saved to your research history
- Export or share results

## 🐆 **Meet Your AI Hunters**

### **Source Scout** 🔍
- **Specialty**: Rapid source discovery and evaluation
- **Skills**: Finding authoritative sources, price discovery, availability checks
- **Collaboration**: Shares verified sources with other hunters

### **Deep Analyst** 🧠  
- **Specialty**: Thorough content analysis and detailed information extraction
- **Skills**: In-depth research, technical analysis, expert insights
- **Collaboration**: Builds on scout findings for comprehensive analysis

### **Fact Checker** ✅
- **Specialty**: Verifying claims and cross-referencing information  
- **Skills**: Accuracy verification, bias detection, source credibility
- **Collaboration**: Validates findings from other hunters

### **Insight Synthesizer** 💡
- **Specialty**: Combining findings into actionable insights
- **Skills**: Pattern recognition, trend analysis, strategic recommendations
- **Collaboration**: Creates final synthesis from all hunter inputs

## ⚙️ **Configuration**

### **Research Settings** (`config.yaml`)
```yaml
orchestrator:
  parallel_agents: 4        # Number of AI hunters
  task_timeout: 120         # Max time per agent (seconds)
  deep_research: true       # Enable advanced capabilities

research:
  depth: 6                  # Search iterations per agent
  breadth: 10              # Results per search
  min_sources_per_agent: 6  # Minimum sources required
```

### **Advanced Features**
- **Persistent Sessions**: Research continues across disconnections
- **Research Memory**: Agents remember context across tasks
- **Smart Caching**: Avoid duplicate searches
- **Progress Tracking**: Real-time completion status
- **User Isolation**: RLS policies ensure data privacy

## 🔧 **API Endpoints**

### **WebSocket**
- `ws://localhost:8000/ws/{client_id}` - Real-time research updates

### **REST API**
- `GET /health` - Health check
- `GET /` - API status

### **WebSocket Messages**
```json
// Start research
{"type": "start_research", "data": {"query": "your query", "user_id": "uuid"}}

// Reconnect to session  
{"type": "reconnect_session", "data": {"session_id": "uuid"}}

// Get active sessions
{"type": "get_active_sessions", "data": {"user_id": "uuid"}}
```

## 🚨 **Troubleshooting**

### **Common Issues**

**Ollama Not Running**
```bash
# Start Ollama
ollama serve

# Check if model is available
ollama list
```

**Database Connection Failed**
```bash
# Test database connection
python3 test_without_auth.py

# Check environment variables
cat .env
```

**RLS Policy Violations**
- Ensure you're using the **service role key** in backend
- Verify database schema was executed properly
- Check that user authentication is working

**Frontend Won't Connect**
- Verify backend is running on port 8000
- Check browser console for WebSocket errors
- Ensure CORS is properly configured

### **Performance Optimization**

**For Faster Research:**
- Increase `parallel_agents` in config.yaml
- Use SSD storage for better Ollama performance
- Ensure stable internet for web searches
- Consider upgrading to larger Ollama models

**For Resource Management:**
- Reduce `depth` and `breadth` settings
- Lower `task_timeout` for quicker results
- Monitor system resources during research

## 📈 **Monitoring & Logs**

- **Backend logs**: Console output shows agent progress
- **Frontend**: Browser DevTools for WebSocket messages  
- **Database**: Supabase Dashboard for session data
- **Ollama**: Check `ollama ps` for model status

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋 **Support**

Having issues? Check out:
- **Database Setup**: `fix_supabase_database.sql`
- **Environment Config**: `.env.example` 
- **Test Scripts**: `test_without_auth.py`
- **Configuration**: `config.yaml`

---

## 🎉 **Ready to Hunt for Knowledge?**

Launch your AI research platform and experience the power of coordinated artificial intelligence!

```bash
./launch.sh
```

**Happy Researching!** 🐆⚡🧠
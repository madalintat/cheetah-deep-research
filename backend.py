import json
import asyncio
import time
import threading
import uuid
import requests
import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from orchestrator import TaskOrchestrator
from deep_orchestrator import DeepResearchOrchestrator
from agent import OllamaAgent
from enhanced_agent import EnhancedOllamaAgent
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Make It Heavy API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except (RuntimeError, ConnectionResetError, ConnectionAbortedError):
                # Silent cleanup for normal disconnections
                self.disconnect(client_id)
            except Exception as e:
                # Only log unexpected errors
                if "connection is closing" not in str(e).lower():
                    print(f"⚠️ WebSocket error for {client_id}: {e}")
                self.disconnect(client_id)

manager = ConnectionManager()

# Supabase configuration from environment variables (optional)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)
if SUPABASE_ENABLED:
    print(f"🔌 Supabase configured: {SUPABASE_URL}")
    print(f"🔑 Service key loaded: {'✅' if SUPABASE_SERVICE_KEY else '❌'}")
    print(f"🔑 Anon key loaded: {'✅' if SUPABASE_ANON_KEY else '❌'}")
else:
    print("⚠️  Supabase disabled (no env). Running with local in-memory persistence only.")

class SupabaseClient:
    """Simple Supabase client for backend operations"""
    
    def __init__(self, url: str, key: str):
        self.url = url
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
    
    async def create_session(self, session_data: dict):
        """Create a research session in Supabase"""
        try:
            response = requests.post(
                f"{self.url}/rest/v1/research_sessions",
                headers=self.headers,
                json=session_data
            )
            if response.status_code in [200, 201]:
                # Handle empty response body from Supabase
                try:
                    response_data = response.json() if response.text.strip() else {}
                    return {"data": response_data, "error": None}
                except json.JSONDecodeError as e:
                    print(f"⚠️  Supabase returned non-JSON response: {response.text}")
                    return {"data": {}, "error": None}  # Treat as success if status is good
            else:
                return {"data": None, "error": response.text}
        except Exception as e:
            return {"data": None, "error": str(e)}
    
    async def update_session(self, session_id: str, updates: dict):
        """Update a research session in Supabase"""
        try:
            response = requests.patch(
                f"{self.url}/rest/v1/research_sessions?session_id=eq.{session_id}",
                headers=self.headers,
                json=updates
            )
            if response.status_code in [200, 204]:
                return {"error": None}
            else:
                return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_active_sessions(self, user_id: str):
        """Get active sessions for a user"""
        try:
            response = requests.get(
                f"{self.url}/rest/v1/research_sessions?user_id=eq.{user_id}&status=eq.ongoing&select=*",
                headers=self.headers
            )
            if response.status_code == 200:
                return {"data": response.json(), "error": None}
            else:
                return {"data": [], "error": response.text}
        except Exception as e:
            return {"data": [], "error": str(e)}
    
    async def save_to_research_history(self, user_id: str, session_data: dict):
        """Save completed research to research_history table"""
        try:
            history_data = {
                "user_id": user_id,
                "query": session_data.get("query", ""),
                "final_result": session_data.get("final_result", ""),
                "agent_results": session_data.get("agent_results", []),
                "total_time": session_data.get("total_time", 0),
                "agents": session_data.get("agents", []),
                "status": "completed"
            }
            
            response = requests.post(
                f"{self.url}/rest/v1/research_history",
                headers=self.headers,
                json=history_data
            )
            if response.status_code in [200, 201]:
                return {"data": response.json(), "error": None}
            else:
                return {"data": None, "error": response.text}
        except Exception as e:
            return {"data": None, "error": str(e)}
    
    async def get_research_history(self, user_id: str):
        """Get research history for a user"""
        try:
            response = requests.get(
                f"{self.url}/rest/v1/research_history",
                headers=self.headers,
                params={"user_id": f"eq.{user_id}", "order": "created_at.desc"}
            )
            if response.status_code == 200:
                return {"data": response.json(), "error": None}
            else:
                return {"data": None, "error": response.text}
        except Exception as e:
            return {"data": None, "error": str(e)}

supabase_client = SupabaseClient(SUPABASE_URL or "", SUPABASE_SERVICE_KEY or "")

# In-memory persistence for local/guest mode
LOCAL_SESSIONS: Dict[str, dict] = {}
LOCAL_HISTORY: Dict[str, list] = {}

class PersistentResearchSession:
    """Represents a research session that can survive disconnections"""
    def __init__(self, session_id: str, query: str, user_id: str = None):
        self.session_id = session_id
        self.query = query
        self.user_id = user_id
        self.status = "ongoing"
        self.current_phase = "initializing"
        self.agents = []
        self.progress = 0
        self.start_time = time.time()
        self.last_updated = time.time()
        self.final_result = None
        self.task = None  # AsyncIO task
        self.connected_clients = set()  # Track connected WebSocket clients

    def add_client(self, client_id: str):
        """Add a connected client"""
        self.connected_clients.add(client_id)

    def remove_client(self, client_id: str):
        """Remove a disconnected client"""
        self.connected_clients.discard(client_id)

    async def broadcast_update(self, message_type: str, data: dict):
        """Send updates to all connected clients and update Supabase"""
        self.last_updated = time.time()
        message = {
            "type": message_type,
            "data": {
                **data,
                "session_id": self.session_id
            },
            "timestamp": time.time()
        }
        
        # Update progress in Supabase for certain message types
        if message_type == "agent_progress" and self.user_id and SUPABASE_ENABLED:
            session_progress = data.get("session_progress", self.progress)
            if session_progress != self.progress:
                self.progress = session_progress
                from datetime import datetime
                updates = {
                    "progress": self.progress,
                    "current_phase": self.current_phase,
                    "last_updated": datetime.now().isoformat()
                }
                # Fire and forget - don't wait for Supabase update
                asyncio.create_task(supabase_client.update_session(self.session_id, updates))
        
        for client_id in self.connected_clients.copy():
            try:
                await manager.send_personal_message(message, client_id)
            except Exception:
                # Remove dead connections
                self.connected_clients.discard(client_id)

class PersistentSessionManager:
    """Manages persistent research sessions"""
    def __init__(self):
        self.sessions: Dict[str, PersistentResearchSession] = {}
        self.lock = threading.Lock()

    async def create_session(self, query: str, user_id: str = None) -> str:
        """Create a new research session and save to Supabase"""
        session_id = str(uuid.uuid4())
        
        with self.lock:
            session = PersistentResearchSession(session_id, query, user_id)
            self.sessions[session_id] = session
        
        # Save to Supabase if enabled; otherwise keep local only
        if user_id and SUPABASE_ENABLED:
            from datetime import datetime
            current_time = datetime.now().isoformat()
            session_data = {
                "user_id": user_id,
                "session_id": session_id,
                "query": query,
                "status": "ongoing",
                "current_phase": "initializing",
                "agents": [],
                "progress": 0,
                "start_time": current_time,
                "last_updated": current_time
            }
            
            result = await supabase_client.create_session(session_data)
            if result["error"]:
                print(f"❌ Failed to save session to Supabase: {result['error']}")
            else:
                print(f"✅ Session saved to Supabase: {session_id[:8]}")
        else:
            # Local store
            LOCAL_SESSIONS[session_id] = {
                "session_id": session_id,
                "query": query,
                "status": "ongoing",
                "current_phase": "initializing",
                "progress": 0,
                "agents": [],
                "start_time": session.start_time,
                "last_updated": session.last_updated,
                "user_id": user_id,
            }
            
        print(f"🔄 Created persistent session {session_id[:8]} for query: '{query[:50]}...'")
        return session_id

    def get_session(self, session_id: str) -> Optional[PersistentResearchSession]:
        """Get an existing session"""
        with self.lock:
            return self.sessions.get(session_id)

    def add_client_to_session(self, session_id: str, client_id: str) -> bool:
        """Connect a client to an existing session"""
        session = self.get_session(session_id)
        if session:
            session.add_client(client_id)
            print(f"🔌 Client {client_id[:8]} connected to session {session_id[:8]}")
            return True
        return False

    def remove_client_from_session(self, session_id: str, client_id: str):
        """Disconnect a client from a session"""
        session = self.get_session(session_id)
        if session:
            session.remove_client(client_id)
            print(f"🔌 Client {client_id[:8]} disconnected from session {session_id[:8]}")

    async def complete_session(self, session_id: str, final_result: str, agent_results: list = None):
        """Mark a session as completed and save to both Supabase tables"""
        session = self.get_session(session_id)
        if session:
            session.status = "completed"
            session.final_result = final_result
            session.last_updated = time.time()
            
            # Calculate total time
            total_time = time.time() - session.start_time
            
            # Update session in research_sessions table
            if session.user_id and SUPABASE_ENABLED:
                from datetime import datetime
                
                # Update the session status
                updates = {
                    "status": "completed",
                    "final_result": final_result,
                    "total_time": total_time,
                    "last_updated": datetime.now().isoformat()
                }
                result = await supabase_client.update_session(session_id, updates)
                if result["error"]:
                    print(f"❌ Failed to update session in Supabase: {result['error']}")
                else:
                    print(f"✅ Session {session_id[:8]} completed and updated in research_sessions")
                
                # Save completed research to research_history table
                history_data = {
                    "query": session.query,
                    "final_result": final_result,
                    "agent_results": agent_results or [],
                    "total_time": total_time,
                    "agents": session.agents
                }
                
                history_result = await supabase_client.save_to_research_history(session.user_id, history_data)
                if history_result["error"]:
                    print(f"❌ Failed to save to research_history: {history_result['error']}")
                else:
                    print(f"✅ Research saved to history for session {session_id[:8]}")
            else:
                print(f"✅ Session {session_id[:8]} completed")
                # Save to local history if user exists
                if session.user_id:
                    LOCAL_HISTORY.setdefault(session.user_id, []).insert(0, {
                        "id": str(uuid.uuid4()),
                        "created_at": time.time(),
                        "query": session.query,
                        "final_result": final_result,
                        "agent_results": agent_results or [],
                        "total_time": total_time,
                        "agents": session.agents
                    })

    def get_active_sessions(self) -> Dict[str, PersistentResearchSession]:
        """Get all active sessions"""
        with self.lock:
            return {sid: s for sid, s in self.sessions.items() if s.status == "ongoing"}

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old sessions"""
        current_time = time.time()
        cutoff = current_time - (max_age_hours * 3600)
        
        with self.lock:
            to_remove = []
            for session_id, session in self.sessions.items():
                if session.last_updated < cutoff:
                    to_remove.append(session_id)
            
            for session_id in to_remove:
                print(f"🗑️ Cleaning up old session {session_id[:8]}")
                del self.sessions[session_id]

session_manager = PersistentSessionManager()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({"status": "healthy", "timestamp": time.time()})

@app.get("/api/active_sessions")
async def get_active_sessions():
    """Get all active research sessions"""
    active = session_manager.get_active_sessions()
    sessions_data = []
    
    for session_id, session in active.items():
        sessions_data.append({
            "session_id": session_id,
            "query": session.query,
            "status": session.status,
            "current_phase": session.current_phase,
            "progress": session.progress,
            "start_time": session.start_time,
            "last_updated": session.last_updated,
            "connected_clients": len(session.connected_clients)
        })
    
    return JSONResponse({"sessions": sessions_data})

@app.get("/api/research_history/{user_id}")
async def get_research_history(user_id: str):
    """Get research history for a user"""
    try:
        if SUPABASE_ENABLED:
            result = await supabase_client.get_research_history(user_id)
            if result["error"]:
                return JSONResponse({"error": result["error"]}, status_code=500)
            else:
                return JSONResponse({"data": result["data"]})
        else:
            data = LOCAL_HISTORY.get(user_id, [])
            return JSONResponse({"data": data})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

class PersistentWebSocketOrchestrator(DeepResearchOrchestrator):
    def __init__(self, session: PersistentResearchSession):
        super().__init__(silent=False)  # Enable debugging output with deep research
        self.session = session

    async def send_update(self, message_type: str, data: dict):
        """Send real-time updates via session broadcast"""
        await self.session.broadcast_update(message_type, data)

    def update_agent_progress(self, agent_id: int, status: str, result: str = None):
        """Override to send WebSocket updates and update session"""
        super().update_agent_progress(agent_id, status, result)
        
        # Update session state
        self.session.current_phase = "executing"
        if hasattr(self, 'agent_progress'):
            completed = sum(1 for s in self.agent_progress.values() if s == "COMPLETED")
            total = len(self.agent_progress)
            self.session.progress = (completed / total * 100) if total > 0 else 0
        
        # Send real-time update
        asyncio.create_task(self.send_update("agent_progress", {
            "agent_id": agent_id,
            "status": status,
            "result": result,
            "session_progress": self.session.progress
        }))

    async def async_orchestrate(self, user_input: str):
        """Deep research orchestration with real-time updates"""
        
        # Check if deep research is enabled
        if self.use_deep_research:
            await self.send_update("orchestration_start", {
                "query": user_input,
                "num_agents": self.num_agents,
                "research_type": "deep_research"
            })
            
            # Execute deep research with real-time updates
            deep_result = await self.orchestrate_deep_research_with_updates(user_input)
            
            return deep_result
        else:
            # Fall back to standard orchestration
            return await self._execute_standard_orchestration(user_input)
    
    async def orchestrate_deep_research_with_updates(self, user_input: str):
        """Deep research orchestration with WebSocket updates"""
        
        # Step 1: Initialize systems and send updates
        await self.send_update("deep_research_init", {
            "status": "initializing_deep_systems"
        })
        
        # Create research memory and plan
        from research_memory import ResearchMemory
        from research_planning import ResearchPlan
        
        self.research_memory = ResearchMemory(user_input)
        
        # Step 2: Deep task decomposition
        await self.send_update("decomposing_task", {"status": "deep_task_analysis"})
        decomposition = self.decompose_task_deep(user_input, self.num_agents)
        
        await self.send_update("task_decomposed", {
            "subtasks": decomposition["subtasks"],
            "hunter_types": decomposition["hunter_types"],
            "research_complexity": decomposition.get("complexity", "standard"),
            "deep_research": decomposition["deep_research"]
        })
        
        # Create research plan
        self.research_plan = ResearchPlan(user_input, decomposition["hunter_types"])
        
        await self.send_update("research_plan_created", {
            "plan_summary": self.research_plan.get_progress(),
            "hunter_assignments": decomposition["hunter_types"]
        })
        
        # Step 3: Execute deep research phases
        if decomposition["deep_research"]:
            result = await self._execute_deep_research_phases(
                decomposition["subtasks"], 
                decomposition["hunter_types"], 
                user_input
            )
        else:
            result = await self._execute_standard_orchestration(user_input)
        
        # Add deep research metadata
        if decomposition["deep_research"]:
            result["deep_research_data"] = {
                "memory_export": self.research_memory.export_memory(),
                "research_plan": self.research_plan.to_dict(),
                "hunter_types": decomposition["hunter_types"]
            }
        
        return result
    
    async def _execute_deep_research_phases(self, subtasks, hunter_types, user_input):
        """Execute research with TRUE PARALLELIZATION - all agents work simultaneously"""
        
        # Initialize tracking
        self.agent_progress = {}
        self.agent_results = {}
        results = []
        
        # 🚀 TRUE PARALLELIZATION: All agents start simultaneously
        await self.send_update("parallel_research_start", {
            "status": "all_agents_starting_simultaneously",
            "total_agents": len(hunter_types),
            "hunter_types": hunter_types
        })
        
        # Create all hunter tasks simultaneously
        all_hunter_tasks = []
        for agent_id, (hunter_type, subtask) in enumerate(zip(hunter_types, subtasks)):
            task = self._run_deep_research_hunter_parallel(agent_id, hunter_type, subtask)
            all_hunter_tasks.append(task)
        
        # 🎯 Execute ALL agents in parallel - no waiting!
        await self.send_update("agents_launched", {
            "message": f"🚀 Launched {len(all_hunter_tasks)} agents simultaneously",
            "agents": [{"id": i, "type": ht} for i, ht in enumerate(hunter_types)]
        })
        
        # Wait for all agents to complete (they work independently)
        all_results = await asyncio.gather(*all_hunter_tasks, return_exceptions=True)
        
        # Process results
        successful_results = []
        for result in all_results:
            if isinstance(result, Exception):
                print(f"❌ Agent failed: {result}")
            else:
                successful_results.append(result)
                results.append(result)
        
        # 🧠 Final synthesis with all findings
        await self.send_update("synthesis_starting", {
            "status": "deep_synthesis",
            "successful_agents": len(successful_results),
            "total_agents": len(all_hunter_tasks)
        })
        
        final_result = await self._synthesize_deep_research_results(results, user_input)
        
        await self.send_update("orchestration_complete", {
            "final_result": final_result,
            "agent_results": results,
            "total_time": time.time() - self.session.start_time,
            "research_type": "parallel_deep_research",
            "parallel_execution": True
        })
        
        return {
            "final_result": final_result,
            "agent_results": results,
            "total_time": time.time(),
            "parallel_execution": True
        }
    
    async def _run_deep_research_hunter_parallel(self, agent_id, hunter_type, subtask):
        """Run a single deep research hunter with ENHANCED real-time updates for parallel execution"""
        
        try:
            # 🚀 Initialize agent with enhanced progress tracking
            await self.send_update("agent_progress", {
                "agent_id": agent_id,
                "status": "INITIALIZING...",
                "subtask": subtask,
                "hunter_type": hunter_type,
                "progress": 0,
                "parallel_execution": True
            })
            
            # Create enhanced step update function with progress tracking
            progress_counter = 0
            async def send_agent_step(step_type: str, step_data: dict):
                nonlocal progress_counter
                progress_counter += 1
                
                # Calculate progress based on step type
                progress = min(95, progress_counter * 10)  # Cap at 95% until completion
                
                await self.send_update("agent_step", {
                    "agent_id": agent_id,
                    "step_type": step_type,
                    "step_data": step_data,
                    "hunter_type": hunter_type,
                    "timestamp": time.time(),
                    "progress": progress,
                    "parallel_execution": True
                })
                
                # Also send progress update
                await self.send_update("agent_progress", {
                    "agent_id": agent_id,
                    "status": "PROCESSING...",
                    "subtask": subtask,
                    "hunter_type": hunter_type,
                    "progress": progress,
                    "current_step": step_type,
                    "parallel_execution": True
                })
            
            # Create deep research agent
            from deep_research_agent import DeepResearchAgent
            
            agent = DeepResearchAgent(
                silent=True,
                agent_id=agent_id,
                hunter_type=hunter_type,
                research_memory=self.research_memory,
                research_plan=self.research_plan
            )
            
            # Override step update method
            agent.send_step_update = send_agent_step
            
            start_time = time.time()
            
            # 🎯 Start processing with enhanced status
            await self.send_update("agent_progress", {
                "agent_id": agent_id,
                "status": "PROCESSING...",
                "subtask": subtask,
                "hunter_type": hunter_type,
                "progress": 5,
                "parallel_execution": True,
                "message": f"🔄 {hunter_type.replace('_', ' ').title()} starting research..."
            })
            
            # Run deep research with enhanced monitoring
            deep_result = await agent.deep_research_run(subtask)
            execution_time = time.time() - start_time
            
            # 🎉 Complete with detailed results
            await self.send_update("agent_progress", {
                "agent_id": agent_id,
                "status": "COMPLETED",
                "subtask": subtask,
                "hunter_type": hunter_type,
                "execution_time": execution_time,
                "progress": 100,
                "findings_count": len(deep_result.get("findings", [])),
                "parallel_execution": True,
                "message": f"✅ {hunter_type.replace('_', ' ').title()} completed in {execution_time:.1f}s",
                # Include textual result so frontend can render Agent Contributions
                "result": deep_result.get("specialized_result", "")
            })
            
            return {
                "agent_id": agent_id,
                "hunter_type": hunter_type,
                "status": "success",
                "subtask": subtask,
                "execution_time": execution_time,
                "response": deep_result["specialized_result"],
                "deep_result": deep_result,
                "parallel_execution": True
            }
            
        except Exception as e:
            await self.send_update("agent_progress", {
                "agent_id": agent_id,
                "status": f"FAILED: {str(e)[:50]}...",
                "subtask": subtask,
                "hunter_type": hunter_type,
                "progress": 0,
                "parallel_execution": True,
                "error": str(e)
            })
            
            return {
                "agent_id": agent_id,
                "hunter_type": hunter_type,
                "status": "error",
                "subtask": subtask,
                "execution_time": 0,
                "response": f"Error: {str(e)}",
                "parallel_execution": True
            }
    
    async def _run_deep_research_hunter(self, agent_id, hunter_type, subtask):
        """Legacy method for backward compatibility"""
        return await self._run_deep_research_hunter_parallel(agent_id, hunter_type, subtask)
    
    async def _execute_standard_orchestration(self, user_input: str):
        """Fallback to standard orchestration when deep research is disabled"""
        
        await self.send_update("orchestration_start", {
            "query": user_input,
            "num_agents": self.num_agents,
            "research_type": "standard"
        })
        
        # Use parent class implementation but with async updates
        result = await super().async_orchestrate(user_input)
        
        return result

@app.get("/")
async def root():
    return {"message": "Make It Heavy API is running!"}

async def run_persistent_research(session: PersistentResearchSession):
    """Run research in background for a persistent session"""
    try:
        print(f"🚀 Starting background research for session {session.session_id[:8]}")
        
        # Create orchestrator for this session
        orchestrator = PersistentWebSocketOrchestrator(session)
        
        # Store the orchestrator in session for progress tracking
        session.agents = []
        session.current_phase = "starting"
        
        # Start research process
        orchestration_result = await orchestrator.async_orchestrate(session.query)
        
        # Extract final result and agent results
        final_result = orchestration_result.get("final_result", "")
        agent_results = orchestration_result.get("agent_results", [])
        
        # Mark session as completed with agent results
        await session_manager.complete_session(session.session_id, final_result, agent_results)
        
        # Broadcast completion
        await session.broadcast_update("research_complete", {
            "result": final_result,
            "agent_results": agent_results,
            "total_time": time.time() - session.start_time
        })
        
        print(f"✅ Background research completed for session {session.session_id[:8]}")
        
    except Exception as e:
        print(f"❌ Background research error for session {session.session_id[:8]}: {e}")
        # Ensure session has a status attribute
        if hasattr(session, 'status'):
            session.status = "failed"
        else:
            session.status = "failed"
        await session.broadcast_update("research_error", {
            "error": str(e)
        })

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Wait for messages from client
            try:
                data = await websocket.receive_text()
            except Exception as e:
                # Gracefully handle closed/invalid connections
                print(f"⚠️  WebSocket receive error for {client_id[:8]}: {e}")
                break
            message = json.loads(data)
            
            if message["type"] == "start_research":
                query = message["data"]["query"]
                user_id = message["data"].get("user_id")
                
                # Create persistent session
                session_id = await session_manager.create_session(query, user_id)
                session = session_manager.get_session(session_id)
                
                # Connect client to session
                session_manager.add_client_to_session(session_id, client_id)
                
                # Send session created response
                await manager.send_personal_message({
                    "type": "session_created",
                    "data": {
                        "session_id": session_id,
                        "query": query
                    }
                }, client_id)
                
                # Start background research (non-blocking)
                session.task = asyncio.create_task(run_persistent_research(session))
                
            elif message["type"] == "reconnect_session":
                session_id = message["data"]["session_id"]
                
                # Try to reconnect to existing session
                if session_manager.add_client_to_session(session_id, client_id):
                    session = session_manager.get_session(session_id)
                    
                    # Send current session state
                    await manager.send_personal_message({
                        "type": "session_reconnected",
                        "data": {
                            "session_id": session_id,
                            "query": session.query,
                            "status": session.status,
                            "current_phase": session.current_phase,
                            "progress": session.progress,
                            "agents": session.agents
                        }
                    }, client_id)
                else:
                    await manager.send_personal_message({
                        "type": "reconnect_failed",
                        "data": {"session_id": session_id}
                    }, client_id)
            
            elif message["type"] == "get_active_sessions":
                # Load active sessions
                user_id = message["data"].get("user_id")
                if user_id:
                    # Validate UUID format to avoid Supabase 22P02 errors
                    def _is_valid_uuid(value: str) -> bool:
                        try:
                            uuid.UUID(str(value))
                            return True
                        except Exception:
                            return False

                    if SUPABASE_ENABLED and _is_valid_uuid(user_id):
                        result = await supabase_client.get_active_sessions(user_id)
                        if result["error"]:
                            print(f"❌ Failed to load sessions from Supabase: {result['error']}")
                            user_sessions = []
                        else:
                            user_sessions = [
                                {
                                    "session_id": session["session_id"],
                                    "query": session["query"],
                                    "status": session["status"],
                                    "current_phase": session["current_phase"],
                                    "progress": session["progress"],
                                    "start_time": session.get("start_time")
                                }
                                for session in result["data"]
                            ]
                            print(f"📋 Loaded {len(user_sessions)} active sessions from Supabase for user {user_id[:8]}")
                    elif not SUPABASE_ENABLED:
                        user_sessions = [
                            {
                                "session_id": s["session_id"],
                                "query": s["query"],
                                "status": s["status"],
                                "current_phase": s["current_phase"],
                                "progress": s["progress"],
                                "start_time": s["start_time"],
                            }
                            for s in LOCAL_SESSIONS.values() if s.get("user_id") == user_id and s.get("status") == "ongoing"
                        ]
                    else:
                        # Supabase enabled but invalid user_id (e.g., 'guest') → return empty list
                        user_sessions = []
                else:
                    user_sessions = []
                
                await manager.send_personal_message({
                    "type": "active_sessions",
                    "data": {"sessions": user_sessions}
                }, client_id)
            
            elif message["type"] == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "data": {"timestamp": time.time()}
                }, client_id)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        
        # Remove client from all sessions
        for session_id, session in session_manager.get_active_sessions().items():
            session_manager.remove_client_from_session(session_id, client_id)
        
        print(f"Client {client_id} disconnected")
    except Exception as e:
        # Catch-all to avoid crashing ASGI app on unexpected errors
        print(f"⚠️  Unexpected WebSocket error for {client_id[:8]}: {e}")
        manager.disconnect(client_id)

if __name__ == "__main__":
    print("🚀 Starting Make It Heavy API...")
    print("📡 WebSocket endpoint: ws://localhost:8000/ws/{client_id}")
    print("🔗 Frontend should connect to: http://localhost:5173")
    
    uvicorn.run(
        "backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
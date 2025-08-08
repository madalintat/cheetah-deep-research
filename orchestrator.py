import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from agent import OllamaAgent
from config_loader import load_config

class TaskOrchestrator:
    def __init__(self, config_path="config.yaml", silent=False):
        # Load configuration with environment variable expansion
        self.config = load_config(config_path)
        
        self.num_agents = self.config['orchestrator']['parallel_agents']
        self.task_timeout = self.config['orchestrator']['task_timeout']
        self.aggregation_strategy = self.config['orchestrator']['aggregation_strategy']
        self.silent = silent
        
        # Track agent progress
        self.agent_progress = {}
        self.agent_results = {}
        self.progress_lock = threading.Lock()
    
    def decompose_task(self, user_input: str, num_agents: int) -> List[str]:
        """Use AI to dynamically generate different questions based on user input"""
        
        # Create question generation agent
        question_agent = OllamaAgent(silent=True)
        
        # Get question generation prompt from config
        prompt_template = self.config['orchestrator']['question_generation_prompt']
        generation_prompt = prompt_template.format(
            user_input=user_input,
            num_agents=num_agents
        )
        
        # Remove task completion tool to avoid issues
        question_agent.tools = [tool for tool in question_agent.tools if tool.get('function', {}).get('name') != 'mark_task_complete']
        question_agent.tool_mapping = {name: func for name, func in question_agent.tool_mapping.items() if name != 'mark_task_complete'}
        
        try:
            # Get AI-generated questions
            if not self.silent:
                print(f"🤖 Generating AI tasks for: '{user_input}'")
            
            response = question_agent.run(generation_prompt)
            
            if not self.silent:
                print(f"🎯 AI Response: {response[:200]}..." if len(response) > 200 else f"🎯 AI Response: {response}")
            
            # Clean up response - remove any markdown or extra formatting
            clean_response = response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response.replace('```json', '').replace('```', '')
            if clean_response.startswith('```'):
                clean_response = clean_response.replace('```', '')
            
            # Parse JSON response
            questions = json.loads(clean_response.strip())
            
            # Validate we got the right structure
            if not isinstance(questions, list):
                raise ValueError(f"Expected list, got {type(questions)}")
            
            if len(questions) != num_agents:
                raise ValueError(f"Expected {num_agents} questions, got {len(questions)}")
            
            if not self.silent:
                print(f"✅ Generated {len(questions)} smart AI tasks successfully")
                for i, q in enumerate(questions):
                    print(f"   {i+1}. {q}")
            
            return questions
            
        except (json.JSONDecodeError, ValueError) as e:
            # Intelligent fallback: create smarter variations based on query analysis
            print(f"❌ AI question generation failed: {e}")
            print(f"🔄 Using intelligent fallback for query: '{user_input}'")
            
            # Smart query analysis for better fallbacks
            user_lower = user_input.lower()
            
            # Fashion/Style/Clothing queries - check these first!
            if any(word in user_lower for word in ['fashion', 'style', 'clothing', 'jeans', 'shirt', 'dress', 'shoes', 'outfit', 'wear', 'wardrobe', 'brand']):
                fallback_tasks = [
                    f"Latest styles and popular options for: {user_input}",
                    f"Best brands and where to buy: {user_input}",
                    f"Styling tips and fashion advice for: {user_input}",
                    f"Price ranges and seasonal considerations for: {user_input}"
                ][:num_agents]
                
                print(f"🎯 Using FASHION fallback tasks:")
                for i, task in enumerate(fallback_tasks):
                    print(f"   {i+1}. {task}")
                
                return fallback_tasks
            
            # Technical/Tutorial queries
            elif any(word in user_lower for word in ['how to', 'tutorial', 'guide', 'learn', 'code', 'programming']):
                print(f"🎯 Using TECHNICAL fallback tasks")
                return [
                    f"Step-by-step guide and fundamentals: {user_input}",
                    f"Advanced techniques and best practices for: {user_input}",
                    f"Common problems and troubleshooting: {user_input}",
                    f"Tools and resources for: {user_input}"
                ][:num_agents]
                
            # Shopping/Product queries  
            elif any(word in user_lower for word in ['price', 'buy', 'cost', 'cheap', 'discount', 'store', 'purchase', 'deals']):
                print(f"🎯 Using SHOPPING fallback tasks")
                return [
                    f"Current prices and official sources for: {user_input}",
                    f"Reviews and comparisons: {user_input}",
                    f"Best deals and discounts for: {user_input}",
                    f"Local availability and stores: {user_input}"
                ][:num_agents]
            
            # News/Current Events
            elif any(word in user_lower for word in ['news', 'breaking', 'latest', 'current', 'today', 'recent', 'update']):
                print(f"🎯 Using NEWS fallback tasks")
                return [
                    f"Latest breaking news about: {user_input}",
                    f"Background context and history of: {user_input}",
                    f"Expert analysis and opinions on: {user_input}",
                    f"Public reaction and social media response to: {user_input}"
                ][:num_agents]
                
            # Business/Market Analysis - only for explicit business terms
            elif any(word in user_lower for word in ['market analysis', 'business strategy', 'industry report', 'market research', 'competitive analysis']):
                print(f"🎯 Using BUSINESS fallback tasks")
                return [
                    f"Market analysis and current data about: {user_input}",
                    f"Competitive landscape and key players in: {user_input}",
                    f"Industry trends and future predictions for: {user_input}",
                    f"Strategic recommendations and insights for: {user_input}"
                ][:num_agents]
                
            # General trends (but not fashion/style) 
            elif any(word in user_lower for word in ['trend', 'analysis', 'research', 'study', 'report']) and not any(word in user_lower for word in ['fashion', 'style', 'clothing']):
                print(f"🎯 Using RESEARCH/TRENDS fallback tasks")
                return [
                    f"Current data and statistics about: {user_input}",
                    f"Expert analysis and opinions on: {user_input}",
                    f"Case studies and real examples: {user_input}",
                    f"Future predictions and trends: {user_input}"
                ][:num_agents]
                
            else:
                # General fallback - comprehensive coverage
                print(f"🎯 Using GENERAL fallback tasks")
                return [
                    f"Comprehensive overview and current information about: {user_input}",
                    f"Expert perspectives and professional insights on: {user_input}",
                    f"Practical examples and real-world applications: {user_input}",
                    f"Latest developments and future outlook for: {user_input}"
                ][:num_agents]
    
    def update_agent_progress(self, agent_id: int, status: str, result: str = None):
        """Thread-safe progress tracking"""
        with self.progress_lock:
            self.agent_progress[agent_id] = status
            if result is not None:
                self.agent_results[agent_id] = result
    
    def run_agent_parallel(self, agent_id: int, subtask: str) -> Dict[str, Any]:
        """
        Run a single agent with the given subtask.
        Returns result dictionary with agent_id, status, and response.
        """
        try:
            self.update_agent_progress(agent_id, "PROCESSING...")
            
            # Use simple agent like in main.py
            agent = OllamaAgent(silent=True)
            
            start_time = time.time()
            response = agent.run(subtask)
            execution_time = time.time() - start_time
            
            self.update_agent_progress(agent_id, "COMPLETED", response)
            
            return {
                "agent_id": agent_id,
                "status": "success", 
                "response": response,
                "execution_time": execution_time
            }
            
        except Exception as e:
            # Simple error handling
            return {
                "agent_id": agent_id,
                "status": "error",
                "response": f"Error: {str(e)}",
                "execution_time": 0
            }
    
    def aggregate_results(self, agent_results: List[Dict[str, Any]]) -> str:
        """
        Combine results from all agents into a comprehensive final answer.
        Uses the configured aggregation strategy.
        """
        successful_results = [r for r in agent_results if r["status"] == "success"]
        
        if not successful_results:
            return "All agents failed to provide results. Please try again."
        
        # Extract responses for aggregation
        responses = [r["response"] for r in successful_results]
        
        if self.aggregation_strategy == "consensus":
            return self._aggregate_consensus(responses, successful_results)
        else:
            # Default to consensus
            return self._aggregate_consensus(responses, successful_results)
    
    def _aggregate_consensus(self, responses: List[str], _results: List[Dict[str, Any]]) -> str:
        """
        Use one final AI call to synthesize all agent responses into a coherent, well-formatted answer.
        Attempts to use config.orchestrator.synthesis_prompt if provided; falls back to a sane default.
        """
        if len(responses) == 1:
            return responses[0]

        # Create synthesis agent to combine all responses
        synthesis_agent = OllamaAgent(silent=True)

        # Build agent responses section
        agent_responses_text = ""
        for i, response in enumerate(responses, 1):
            agent_responses_text += f"=== AGENT {i} RESPONSE ===\n{response}\n\n"

        # Prefer structured synthesis prompt from config if available
        orchestrator_cfg = self.config.get('orchestrator', {}) if hasattr(self, 'config') else {}
        template = orchestrator_cfg.get('synthesis_prompt')

        if template:
            try:
                synthesis_prompt = template.format(
                    num_responses=len(responses),
                    agent_responses=agent_responses_text
                )
            except Exception:
                # If template formatting fails, fallback to default
                synthesis_prompt = None
        else:
            synthesis_prompt = None

        if not synthesis_prompt:
            # Default, opinionated, deduplicated synthesis prompt
            synthesis_prompt = (
                f"You have {len(responses)} different research perspectives on the same query.\n"
                "Create ONE unified, comprehensive answer with excellent section formatting (markdown),\n"
                "clear bullet points, strict deduplication, and links consolidated in a Sources section.\n\n"
                "Rules:\n"
                "- Do NOT repeat information; merge duplicates.\n"
                "- Prefer 2025 info.\n"
                "- Provide actionable details (names, links, versions, pricing if present).\n\n"
                f"Agent Research Results:\n{agent_responses_text}\n"
                "Produce the final answer now."
            )

        # Completely remove all tools from synthesis agent to force direct response
        synthesis_agent.tools = []
        synthesis_agent.tool_mapping = {}

        try:
            final_answer = synthesis_agent.run(synthesis_prompt)
            return final_answer
        except Exception as e:
            print(f"\n🚨 SYNTHESIS FAILED: {str(e)}")
            print("📋 Falling back to concatenated responses\n")
            combined = []
            for i, response in enumerate(responses, 1):
                combined.append(f"=== Agent {i} Response ===")
                combined.append(response)
                combined.append("")
            return "\n".join(combined)
    
    def get_progress_status(self) -> Dict[int, str]:
        """Get current progress status for all agents"""
        with self.progress_lock:
            return self.agent_progress.copy()
    
    def orchestrate(self, user_input: str):
        """
        Main orchestration method.
        Takes user input, delegates to parallel agents, and returns aggregated result.
        """
        
        # Reset progress tracking
        self.agent_progress = {}
        self.agent_results = {}
        
        # Decompose task into subtasks
        subtasks = self.decompose_task(user_input, self.num_agents)
        
        # Initialize progress tracking
        for i in range(self.num_agents):
            self.agent_progress[i] = "QUEUED"
        
        # Execute agents in parallel
        agent_results = []
        
        with ThreadPoolExecutor(max_workers=self.num_agents) as executor:
            # Submit all agent tasks
            future_to_agent = {
                executor.submit(self.run_agent_parallel, i, subtasks[i]): i 
                for i in range(self.num_agents)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_agent, timeout=self.task_timeout):
                try:
                    result = future.result()
                    agent_results.append(result)
                except Exception as e:
                    agent_id = future_to_agent[future]
                    agent_results.append({
                        "agent_id": agent_id,
                        "status": "timeout",
                        "response": f"Agent {agent_id + 1} timed out or failed: {str(e)}",
                        "execution_time": self.task_timeout
                    })
        
        # Sort results by agent_id for consistent output
        agent_results.sort(key=lambda x: x["agent_id"])
        
        # Aggregate results
        final_result = self.aggregate_results(agent_results)
        
        return final_result
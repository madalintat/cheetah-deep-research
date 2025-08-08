import json
import requests
import asyncio
from typing import Dict, List, Any
from tools import discover_tools
from datetime import datetime
from config_loader import load_config

class EnhancedOllamaAgent:
    def __init__(self, config_path="config.yaml", silent=False, websocket_manager=None, client_id=None, agent_id=None):
        # Load configuration with environment variable expansion
        self.config = load_config(config_path)
        
        self.silent = silent
        self.websocket_manager = websocket_manager
        self.client_id = client_id
        self.agent_id = agent_id
        
        # Ollama API endpoint
        self.ollama_url = self.config['ollama']['base_url']
        self.model = self.config['ollama']['model']
        
        # Research parameters
        self.search_depth = self.config.get('research', {}).get('depth', 3)  # How many search iterations
        self.search_breadth = self.config.get('research', {}).get('breadth', 5)  # Results per search
        
        # Discover tools dynamically
        self.discovered_tools = discover_tools(self.config, silent=self.silent)
        
        # Build Ollama tools array
        self.tools = [tool.to_openrouter_schema() for tool in self.discovered_tools.values()]
        
        # Build tool mapping
        self.tool_mapping = {name: tool.execute for name, tool in self.discovered_tools.items()}
        
        # Debug: Print available tools for troubleshooting
        if not self.silent:
            print(f"🔧 EnhancedAgent initialized with {len(self.tools)} tools: {list(self.tool_mapping.keys())}")
        
        # Step tracking
        self.research_steps = []
    
    def _parse_text_tool_calls(self, text: str) -> list:
        """Parse tool calls from text when LLM writes them as JSON instead of using tool_calls"""
        import re
        tool_calls = []
        
        # Look for JSON patterns like {"name": "search_web", "parameters": {...}}
        patterns = [
            r'\{"name":\s*"([^"]+)",\s*"parameters":\s*(\{[^}]*\})\}',
            r'\{"function":\s*\{"name":\s*"([^"]+)",\s*"arguments":\s*(\{[^}]*\})\}\}',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    tool_name = match[0]
                    args_str = match[1]
                    args = json.loads(args_str) if args_str.startswith('{') else {}
                    
                    # Convert to standard tool call format
                    tool_call = {
                        "id": f"call_{len(tool_calls)}",
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": args if isinstance(args, dict) else json.loads(args_str)
                        }
                    }
                    tool_calls.append(tool_call)
                    
                except (json.JSONDecodeError, IndexError, KeyError):
                    continue
        
        return tool_calls
    
    async def send_step_update(self, step_type: str, step_data: dict):
        """Send real-time step updates"""
        if self.websocket_manager and self.client_id and self.agent_id is not None:
            try:
                # Ensure step_data is JSON serializable
                safe_step_data = {}
                for key, value in step_data.items():
                    if isinstance(value, (str, int, float, bool, list, dict)):
                        safe_step_data[key] = value
                    else:
                        safe_step_data[key] = str(value)
                
                message = {
                    "type": "agent_step",
                    "data": {
                        "agent_id": self.agent_id,
                        "step_type": step_type,
                        "step_data": safe_step_data,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                await self.websocket_manager.send_personal_message(message, self.client_id)
            except Exception as e:
                if not self.silent:
                    print(f"⚠️  Failed to send step update: {e}")
    
    def call_llm(self, messages):
        """Make Ollama API call with tools"""
        try:
            # Prepare the request payload for Ollama
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.config.get('ollama', {}).get('temperature', 0.7),
                    "top_p": self.config.get('ollama', {}).get('top_p', 0.9),
                }
            }
            
            # Add tools if available
            if self.tools:
                payload["tools"] = self.tools
                if not self.silent:
                    print(f"🔧 Sending {len(self.tools)} tools to LLM: {[t.get('function', {}).get('name', 'unknown') for t in self.tools]}")
            else:
                if not self.silent:
                    print("⚠️  No tools available for LLM!")
            
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            return response.json()
        except Exception as e:
            raise Exception(f"LLM call failed: {str(e)}")
    
    async def handle_tool_call(self, tool_call):
        """Handle a tool call and return the result message"""
        try:
            # Extract tool name and arguments
            tool_name = tool_call.get('name', tool_call.get('function', {}).get('name'))
            raw_args = tool_call.get('arguments', tool_call.get('function', {}).get('arguments', '{}'))
            
            # Handle both string and dict arguments
            if isinstance(raw_args, str):
                tool_args = json.loads(raw_args)
            else:
                tool_args = raw_args
            
            # Track the step
            step_info = {
                "tool": tool_name,
                "query": tool_args.get('query', 'N/A'),
                "status": "executing"
            }
            
            # Send step update with enhanced details
            await self.send_step_update("tool_execution", {
                **step_info,
                "message": f"🔍 Executing {tool_name} for: {tool_args.get('query', 'N/A')[:50]}...",
                "tool_args": tool_args
            })
            
            # Map common aliases to our canonical tool name
            alias_map = {
                "google": "search_web",
                "bing": "search_web",
                "duckduckgo": "search_web",
                "web_search": "search_web",
                "search": "search_web",
                "websearch": "search_web",
                "searchweb": "search_web",
                "crawl": "search_web",
                "crawl4ai": "search_web",
            }
            if tool_name in alias_map:
                tool_name = alias_map[tool_name]

            # Normalize common argument aliases from LLMs
            if tool_name == "search_web" and isinstance(tool_args, dict):
                if "q" in tool_args and "query" not in tool_args:
                    tool_args["query"] = tool_args.pop("q")
                if "maxResults" in tool_args and "max_results" not in tool_args:
                    tool_args["max_results"] = tool_args.pop("maxResults")
                if "deepExtract" in tool_args and "deep_extract" not in tool_args:
                    tool_args["deep_extract"] = tool_args.pop("deepExtract")
                # Additional common aliases
                if "limit" in tool_args and "max_results" not in tool_args:
                    tool_args["max_results"] = tool_args.pop("limit")
                if "num_results" in tool_args and "max_results" not in tool_args:
                    tool_args["max_results"] = tool_args.pop("num_results")
                if "topK" in tool_args and "max_results" not in tool_args:
                    tool_args["max_results"] = tool_args.pop("topK")
                if "deep" in tool_args and "deep_extract" not in tool_args:
                    tool_args["deep_extract"] = tool_args.pop("deep")

            # Call appropriate tool from tool_mapping
            if tool_name in self.tool_mapping:
                # Handle async tool calls properly
                tool_func = self.tool_mapping[tool_name]
                if asyncio.iscoroutinefunction(tool_func):
                    tool_result = await tool_func(**tool_args)
                else:
                    tool_result = tool_func(**tool_args)
                
                # Track successful step
                step_info["status"] = "completed"
                step_info["results_found"] = len(tool_result) if isinstance(tool_result, list) else 1
                
                await self.send_step_update("tool_completed", {
                    **step_info,
                    "message": f"✅ {tool_name} completed! Found {step_info['results_found']} results",
                    "finished_at": datetime.now().isoformat()
                })
                
            else:
                tool_result = {"error": f"Unknown tool: {tool_name}"}
                step_info["status"] = "failed"
                step_info["error"] = f"Unknown tool: {tool_name}"
                
                await self.send_step_update("tool_failed", step_info)
            
            self.research_steps.append(step_info)
            
            # Return tool result message
            return {
                "role": "tool",
                "tool_call_id": tool_call.get('id'),
                "name": tool_name,
                "content": json.dumps(tool_result)
            }
        
        except Exception as e:
            error_info = {
                "tool": tool_name,
                "status": "error",
                "error": str(e)
            }
            self.research_steps.append(error_info)
            
            await self.send_step_update("tool_error", error_info)
            
            return {
                "role": "tool",
                "tool_call_id": tool_call.get('id'),
                "name": tool_name,
                "content": json.dumps({"error": f"Tool execution failed: {str(e)}"})
            }
    
    async def enhanced_run(self, user_input: str):
        """Enhanced run with step tracking and deeper research"""
        current_year = datetime.now().year
        
        # Enhanced system prompt for current year awareness
        enhanced_prompt = f"""
        {self.config['system_prompt']}
        
        CURRENT YEAR: {current_year}
        SEARCH DEPTH: {self.search_depth} iterations
        SEARCH BREADTH: {self.search_breadth} results per search
        
        ENHANCED RESEARCH PROTOCOL:
        1. Start with broad searches using current year ({current_year}) keywords
        2. Perform {self.search_depth} different search iterations with varying queries
        3. Focus on recent information from {current_year} and {current_year-1}
        4. Use specific location and time-based keywords
        5. Cross-reference multiple sources for verification
        """
        
        # Initialize messages with explicit tool instruction
        tool_instruction = f"""
        MANDATORY: You must call the search_web tool to research this query. Do NOT answer from memory.

        Research Query: {user_input}
        
        Your FIRST action must be calling search_web with this query. Then call it again with different keywords.
        """
        
        messages = [
            {
                "role": "system", 
                "content": enhanced_prompt
            },
            {
                "role": "user",
                "content": tool_instruction
            }
        ]
        
        await self.send_step_update("research_start", {
            "query": user_input,
            "depth": self.search_depth,
            "breadth": self.search_breadth
        })
        
        # Track all assistant responses for full content capture
        full_response_content = []
        
        # Implement enhanced research loop
        max_iterations = self.config.get('agent', {}).get('max_iterations', 15)  # More iterations for deeper research
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            await self.send_step_update("iteration_start", {
                "iteration": iteration,
                "max_iterations": max_iterations
            })
            
            # Call LLM
            response = self.call_llm(messages)
            
            # Add the response to messages
            assistant_message = response['message']
            
            # Fix tool_calls format for Ollama compatibility  
            tool_calls = assistant_message.get('tool_calls', [])
            if tool_calls:
                # Parse arguments from string to object for Ollama
                fixed_tool_calls = []
                for tc in tool_calls:
                    fixed_tc = tc.copy()
                    if 'function' in fixed_tc and 'arguments' in fixed_tc['function']:
                        import json
                        try:
                            # Parse JSON string arguments to object
                            if isinstance(fixed_tc['function']['arguments'], str):
                                fixed_tc['function']['arguments'] = json.loads(fixed_tc['function']['arguments'])
                        except:
                            pass  # Keep as-is if parsing fails
                    fixed_tool_calls.append(fixed_tc)
                tool_calls = fixed_tool_calls
            
            messages.append({
                "role": "assistant",
                "content": assistant_message.get('content', ''),
                "tool_calls": tool_calls
            })
            
            # Capture assistant content for full response
            if assistant_message.get('content'):
                full_response_content.append(assistant_message['content'])
            
            # Check if there are tool calls
            tool_calls = assistant_message.get('tool_calls', [])
            
            # FALLBACK: If no tool_calls but the response contains JSON tool calls as text, parse them
            if not tool_calls:
                llm_text = assistant_message.get('content', '')
                parsed_calls = self._parse_text_tool_calls(llm_text)
                if parsed_calls:
                    tool_calls = parsed_calls
                    if not self.silent:
                        print(f"🔧 Parsed {len(tool_calls)} tool calls from text response")
            
            if tool_calls:
                await self.send_step_update("tools_executing", {
                    "tool_count": len(tool_calls),
                    "iteration": iteration
                })
                
                # Handle each tool call
                task_completed = False
                for tool_call in tool_calls:
                    tool_result = await self.handle_tool_call(tool_call)
                    messages.append(tool_result)
                    
                    # Check if this was the task completion tool
                    tool_name = tool_call.get('name', tool_call.get('function', {}).get('name'))
                    if tool_name == "mark_task_complete":
                        task_completed = True
                        await self.send_step_update("research_complete", {
                            "total_iterations": iteration,
                            "total_steps": len(self.research_steps)
                        })
                        
                        # Return ONLY the research content, exclude task completion messages
                        clean_content = []
                        for content in full_response_content:
                            # Filter out task completion tool mentions
                            if "mark_task_complete" not in content and not content.startswith("User's request has been fulfilled"):
                                clean_content.append(content)
                        return "\n\n".join(clean_content)
                
                # If task was completed, we already returned above
                if task_completed:
                    return "\n\n".join(full_response_content)
            else:
                # Debug: Log what the LLM said instead of calling tools
                llm_response = assistant_message.get('content', '')
                if not self.silent:
                    print(f"⚠️  LLM didn't call tools. Response: {llm_response[:200]}...")
                    print(f"💡 Available tools: {list(self.tool_mapping.keys())}")
                
                await self.send_step_update("thinking", {
                    "iteration": iteration,
                    "status": "no_tools_needed",
                    "llm_response": llm_response[:100]  # First 100 chars for debugging
                })
            
            # Continue the loop
        
        await self.send_step_update("research_timeout", {
            "total_iterations": max_iterations,
            "total_steps": len(self.research_steps)
        })
        
        # If max iterations reached, return whatever content we gathered
        return "\n\n".join(full_response_content) if full_response_content else "Maximum iterations reached. Research may be incomplete."
    
    def run(self, user_input: str):
        """Backwards compatibility wrapper"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.enhanced_run(user_input))
        except RuntimeError:
            # If no event loop is running, create one
            return asyncio.run(self.enhanced_run(user_input))
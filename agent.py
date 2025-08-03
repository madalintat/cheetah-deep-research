import json
import requests
from tools import discover_tools
from config_loader import load_config

class OllamaAgent:
    def __init__(self, config_path="config.yaml", silent=False):
        # Load configuration with environment variable expansion
        self.config = load_config(config_path)
        
        # Silent mode for orchestrator (suppresses debug output)
        self.silent = silent
        
        # Ollama API endpoint
        self.ollama_url = self.config['ollama']['base_url']
        self.model = self.config['ollama']['model']
        
        # Discover tools dynamically
        self.discovered_tools = discover_tools(self.config, silent=self.silent)
        
        # Build Ollama tools array
        self.tools = [tool.to_openrouter_schema() for tool in self.discovered_tools.values()]
        
        # Build tool mapping
        self.tool_mapping = {name: tool.execute for name, tool in self.discovered_tools.items()}
    
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
    
    def handle_tool_call(self, tool_call):
        """Handle a tool call and return the result message"""
        try:
            # Extract tool name and arguments
            tool_name = tool_call.get('name', tool_call.get('function', {}).get('name'))
            tool_args = json.loads(tool_call.get('arguments', tool_call.get('function', {}).get('arguments', '{}')))
            
            # Call appropriate tool from tool_mapping
            if tool_name in self.tool_mapping:
                tool_result = self.tool_mapping[tool_name](**tool_args)
            else:
                tool_result = {"error": f"Unknown tool: {tool_name}"}
            
            # Return tool result message
            return {
                "role": "tool",
                "tool_call_id": tool_call.get('id'),
                "name": tool_name,
                "content": json.dumps(tool_result)
            }
        
        except Exception as e:
            return {
                "role": "tool",
                "tool_call_id": tool_call.get('id'),
                "name": tool_name,
                "content": json.dumps({"error": f"Tool execution failed: {str(e)}"})
            }
    
    def run(self, user_input: str):
        """Run the agent with user input and return FULL conversation content"""
        # Initialize messages with system prompt and user input
        messages = [
            {
                "role": "system",
                "content": self.config['system_prompt']
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
        
        # Track all assistant responses for full content capture
        full_response_content = []
        
        # Implement agentic loop
        max_iterations = self.config.get('agent', {}).get('max_iterations', 10)
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            if not self.silent:
                print(f"🔄 Agent iteration {iteration}/{max_iterations}")
            
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
            if tool_calls:
                if not self.silent:
                    print(f"🔧 Agent making {len(tool_calls)} tool call(s)")
                # Handle each tool call
                task_completed = False
                for tool_call in tool_calls:
                    if not self.silent:
                        print(f"   📞 Calling tool: {tool_call.get('name', tool_call.get('function', {}).get('name'))}")
                    tool_result = self.handle_tool_call(tool_call)
                    messages.append(tool_result)
                    
                    # Check if this was the task completion tool
                    tool_name = tool_call.get('name', tool_call.get('function', {}).get('name'))
                    if tool_name == "mark_task_complete":
                        task_completed = True
                        if not self.silent:
                            print("✅ Task completion tool called - exiting loop")
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
                if not self.silent:
                    print("💭 Agent responded without tool calls - continuing loop")
            
            # Continue the loop regardless of whether there were tool calls or not
        
        # If max iterations reached, return whatever content we gathered
        return "\n\n".join(full_response_content) if full_response_content else "Maximum iterations reached. The agent may be stuck in a loop."
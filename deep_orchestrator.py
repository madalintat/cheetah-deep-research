"""
Deep Research Orchestrator - Coordinates deep research agents with planning and memory
Extends the base orchestrator with deep research capabilities
"""

import json
import time
import asyncio
from typing import List, Dict, Any
from orchestrator import TaskOrchestrator
from deep_research_agent import DeepResearchAgent
from research_planning import ResearchPlan
from research_memory import ResearchMemory
from hunter_roles import HunterRoleSystem

class DeepResearchOrchestrator(TaskOrchestrator):
    """Orchestrator with deep research capabilities"""
    
    def __init__(self, config_path="config.yaml", silent=False):
        super().__init__(config_path, silent)
        
        # Deep research components
        self.role_system = HunterRoleSystem()
        self.research_memory = None
        self.research_plan = None
        
        # Deep research configuration
        self.use_deep_research = self.config.get('orchestrator', {}).get('deep_research', True)
        self.hunter_sequence = ["source_scout", "deep_analyst", "fact_checker", "insight_synthesizer"]
        
        if not self.silent:
            print(f"🧠 Deep Research Orchestrator initialized")
            print(f"   Deep research enabled: {self.use_deep_research}")
    
    def decompose_task_deep(self, user_input: str, num_agents: int) -> Dict[str, Any]:
        """Deep task decomposition with hunter specialization"""
        
        if not self.use_deep_research:
            # Fall back to standard decomposition
            subtasks = self.decompose_task(user_input, num_agents)
            return {
                "subtasks": subtasks,
                "hunter_types": ["general"] * len(subtasks),
                "deep_research": False
            }
        
        # Get optimal team composition
        complexity = self._assess_research_complexity(user_input)
        hunter_types = self.role_system.get_optimal_team_composition(complexity)
        
        # Limit to available agents
        hunter_types = hunter_types[:num_agents]
        
        # Generate specialized subtasks for each hunter
        specialized_subtasks = []
        
        for hunter_type in hunter_types:
            profile = self.role_system.get_hunter_profile(hunter_type)
            if profile:
                # Create hunter-specific subtask
                subtask = f"{profile.description}: {user_input}"
                specialized_subtasks.append(subtask)
            else:
                # Fallback generic subtask
                specialized_subtasks.append(f"Research and analyze: {user_input}")
        
        # Pad with generic tasks if needed
        while len(specialized_subtasks) < num_agents:
            specialized_subtasks.append(f"Additional research on: {user_input}")
            hunter_types.append("general")
        
        if not self.silent:
            print(f"🎯 Deep task decomposition completed:")
            for i, (hunter, task) in enumerate(zip(hunter_types, specialized_subtasks)):
                print(f"   Hunter {i+1} ({hunter}): {task[:60]}...")
        
        return {
            "subtasks": specialized_subtasks,
            "hunter_types": hunter_types,
            "deep_research": True,
            "complexity": complexity
        }
    
    def _assess_research_complexity(self, user_input: str) -> str:
        """Assess research complexity to determine team composition"""
        
        user_lower = user_input.lower()
        
        # Complex indicators
        complex_indicators = [
            'comprehensive analysis', 'market research', 'detailed study',
            'business strategy', 'in-depth', 'thorough investigation'
        ]
        
        # Verification-heavy indicators  
        verification_indicators = [
            'fact check', 'verify', 'validate', 'confirm', 'accuracy',
            'truth', 'reliable', 'credible'
        ]
        
        # Simple indicators
        simple_indicators = [
            'quick overview', 'simple question', 'basic info',
            'what is', 'define', 'explain briefly'
        ]
        
        if any(indicator in user_lower for indicator in complex_indicators):
            return "complex"
        elif any(indicator in user_lower for indicator in verification_indicators):
            return "verification_heavy"
        elif any(indicator in user_lower for indicator in simple_indicators):
            return "simple"
        else:
            return "standard"
    
    async def orchestrate_deep_research(self, user_input: str) -> Dict[str, Any]:
        """Main deep research orchestration method"""
        
        if not self.silent:
            print(f"\n🚀 Starting deep research orchestration...")
            print(f"Query: {user_input}")
        
        # Step 1: Initialize shared research systems
        self.research_memory = ResearchMemory(user_input)
        
        # Step 2: Deep task decomposition
        decomposition = self.decompose_task_deep(user_input, self.num_agents)
        subtasks = decomposition["subtasks"]
        hunter_types = decomposition["hunter_types"] 
        
        # Step 3: Create research plan
        self.research_plan = ResearchPlan(user_input, hunter_types)
        
        if not self.silent:
            print(f"📋 Research plan created with {len(self.research_plan.todos)} todos")
            plan_progress = self.research_plan.get_progress()
            print(f"   Estimated time: {plan_progress['estimated_time_remaining']} minutes")
        
        # Step 4: Execute hunters in coordinated sequence
        if decomposition["deep_research"]:
            results = await self._execute_deep_research_sequence(subtasks, hunter_types, user_input)
        else:
            results = await self._execute_standard_research(subtasks, user_input)
        
        # Step 5: Generate final synthesis
        final_result = await self._synthesize_deep_research_results(results, user_input)
        
        # Step 6: Export research memory for persistence
        memory_export = self.research_memory.export_memory()
        
        return {
            "final_result": final_result,
            "research_memory": memory_export,
            "research_plan": self.research_plan.to_dict(),
            "hunter_results": results,
            "deep_research_used": decomposition["deep_research"]
        }
    
    async def _execute_deep_research_sequence(self, subtasks: List[str], 
                                           hunter_types: List[str], 
                                           user_input: str) -> List[Dict[str, Any]]:
        """Execute hunters in optimal sequence for deep research"""
        
        results = []
        
        # Phase 1: Source scouts (parallel)
        scout_tasks = []
        scout_agents = []
        
        for i, (subtask, hunter_type) in enumerate(zip(subtasks, hunter_types)):
            if hunter_type == "source_scout":
                agent = DeepResearchAgent(
                    silent=True,
                    agent_id=i,
                    hunter_type=hunter_type,
                    research_memory=self.research_memory,
                    research_plan=self.research_plan
                )
                scout_agents.append(agent)
                scout_tasks.append(self._run_deep_agent(agent, subtask, i))
        
        if scout_tasks:
            if not self.silent:
                print(f"🔍 Phase 1: Running {len(scout_tasks)} source scouts...")
            scout_results = await asyncio.gather(*scout_tasks)
            results.extend(scout_results)
        
        # Phase 2: Deep analysts (parallel, after scouts)
        analyst_tasks = []
        
        for i, (subtask, hunter_type) in enumerate(zip(subtasks, hunter_types)):
            if hunter_type == "deep_analyst":
                agent = DeepResearchAgent(
                    silent=True,
                    agent_id=i,
                    hunter_type=hunter_type,
                    research_memory=self.research_memory,
                    research_plan=self.research_plan
                )
                analyst_tasks.append(self._run_deep_agent(agent, subtask, i))
        
        if analyst_tasks:
            if not self.silent:
                print(f"🔬 Phase 2: Running {len(analyst_tasks)} deep analysts...")
            analyst_results = await asyncio.gather(*analyst_tasks)
            results.extend(analyst_results)
        
        # Phase 3: Fact checkers (parallel, after analysts)
        checker_tasks = []
        
        for i, (subtask, hunter_type) in enumerate(zip(subtasks, hunter_types)):
            if hunter_type == "fact_checker":
                agent = DeepResearchAgent(
                    silent=True,
                    agent_id=i,
                    hunter_type=hunter_type,
                    research_memory=self.research_memory,
                    research_plan=self.research_plan
                )
                checker_tasks.append(self._run_deep_agent(agent, subtask, i))
        
        if checker_tasks:
            if not self.silent:
                print(f"✅ Phase 3: Running {len(checker_tasks)} fact checkers...")
            checker_results = await asyncio.gather(*checker_tasks)
            results.extend(checker_results)
        
        # Phase 4: Synthesizers (serial, after all others)
        for i, (subtask, hunter_type) in enumerate(zip(subtasks, hunter_types)):
            if hunter_type == "insight_synthesizer":
                if not self.silent:
                    print(f"🧠 Phase 4: Running insight synthesizer...")
                
                agent = DeepResearchAgent(
                    silent=True,
                    agent_id=i,
                    hunter_type=hunter_type,
                    research_memory=self.research_memory,
                    research_plan=self.research_plan
                )
                synthesizer_result = await self._run_deep_agent(agent, subtask, i)
                results.append(synthesizer_result)
        
        return results
    
    async def _execute_standard_research(self, subtasks: List[str], 
                                       user_input: str) -> List[Dict[str, Any]]:
        """Execute standard parallel research (fallback)"""
        
        if not self.silent:
            print(f"📝 Executing standard parallel research...")
        
        tasks = []
        
        for i, subtask in enumerate(subtasks):
            agent = DeepResearchAgent(
                silent=True,
                agent_id=i,
                hunter_type="general",
                research_memory=self.research_memory,
                research_plan=None  # No plan for standard research
            )
            tasks.append(self._run_deep_agent(agent, subtask, i))
        
        results = await asyncio.gather(*tasks)
        return results
    
    async def _run_deep_agent(self, agent: DeepResearchAgent, subtask: str, 
                            agent_id: int) -> Dict[str, Any]:
        """Run a single deep research agent"""
        
        start_time = time.time()
        
        try:
            if not self.silent:
                print(f"   🐆 Hunter {agent_id} ({agent.hunter_type}) starting...")
            
            # Run deep research
            deep_result = await agent.deep_research_run(subtask)
            execution_time = time.time() - start_time
            
            return {
                "agent_id": agent_id,
                "hunter_type": agent.hunter_type,
                "status": "success",
                "subtask": subtask,
                "execution_time": execution_time,
                "response": deep_result["specialized_result"],
                "deep_result": deep_result,
                "findings_count": len(deep_result.get("findings", [])),
                "collaboration_summary": deep_result.get("collaboration_summary", {})
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            if not self.silent:
                print(f"   ❌ Hunter {agent_id} failed: {str(e)}")
            
            return {
                "agent_id": agent_id,
                "hunter_type": agent.hunter_type,
                "status": "error",
                "subtask": subtask,
                "execution_time": execution_time,
                "response": f"Error: {str(e)}",
                "error": str(e)
            }
    
    async def _synthesize_deep_research_results(self, results: List[Dict[str, Any]], 
                                              user_input: str) -> str:
        """Synthesize all deep research results into final answer"""
        
        if not self.silent:
            print(f"🔄 Synthesizing deep research results...")
        
        # Collect all findings and responses
        all_responses = []
        total_findings = 0
        hunter_contributions = {}
        
        for result in results:
            # Ensure result is a dict and has required fields
            if isinstance(result, dict) and result.get("status") == "success":
                all_responses.append(result.get("response", ""))
                total_findings += result.get("findings_count", 0)
                
                hunter_type = result.get("hunter_type", "unknown")
                if hunter_type not in hunter_contributions:
                    hunter_contributions[hunter_type] = 0
                hunter_contributions[hunter_type] += result.get("findings_count", 0)
            elif not isinstance(result, dict):
                print(f"⚠️  Invalid result type in synthesis: {type(result)} - {result}")
            elif result.get("status") != "success":
                print(f"⚠️  Failed result in synthesis: {result.get('status')} - {result.get('response', 'No error details')}")
        
        # Use standard aggregation with enhanced context
        synthesis_context = f"""
DEEP RESEARCH SYNTHESIS

Original Query: {user_input}
Total Findings: {total_findings}
Hunter Contributions: {json.dumps(hunter_contributions, indent=2)}

Research Memory: {len(self.research_memory.findings) if self.research_memory else 0} total findings stored
Research Plan: {self.research_plan.get_progress()['progress_percentage']:.1f}% completed

The following responses represent specialized research from different hunter types:
"""
        
        # Add synthesis context to aggregation
        enhanced_responses = [synthesis_context] + all_responses
        
        # Use parent class aggregation method
        final_result = self.aggregate_results([
            {"response": response} for response in enhanced_responses
        ])
        
        if not self.silent:
            print(f"✅ Deep research synthesis completed")
            print(f"   Final result length: {len(final_result)} characters")
            print(f"   Research findings: {total_findings}")
        
        return final_result
    
    # Override orchestrate to use deep research
    async def async_orchestrate(self, user_input: str) -> Dict[str, Any]:
        """Async orchestration with deep research capabilities"""
        
        if self.use_deep_research:
            deep_result = await self.orchestrate_deep_research(user_input)
            return {
                "final_result": deep_result["final_result"],
                "agent_results": deep_result["hunter_results"],
                "total_time": time.time(),
                "deep_research_data": {
                    "memory_export": deep_result["research_memory"],
                    "research_plan": deep_result["research_plan"]
                }
            }
        else:
            # Use parent implementation for standard research
            return await super().async_orchestrate(user_input)
"""
Deep Research Agent - Enhanced agent with planning, specialization, and memory
Integrates todo planning, hunter roles, and shared research memory
"""

import json
import time
import asyncio
from typing import Dict, List, Any, Optional
from enhanced_agent import EnhancedOllamaAgent
from research_planning import ResearchPlan, PlanningTool, ResearchTodo, TodoStatus
from hunter_roles import HunterRoleSystem, HunterProfile
from research_memory import ResearchMemory, FindingType, SourceQuality

class DeepResearchAgent(EnhancedOllamaAgent):
    """Enhanced agent with deep research capabilities"""
    
    def __init__(self, config_path="config.yaml", silent=False, websocket_manager=None, 
                 client_id=None, agent_id=None, hunter_type="source_scout", 
                 research_memory=None, research_plan=None):
        
        # Initialize base enhanced agent
        super().__init__(config_path, silent, websocket_manager, client_id, agent_id)
        
        # Deep research components
        self.hunter_type = hunter_type
        self.role_system = HunterRoleSystem()
        self.hunter_profile = self.role_system.get_hunter_profile(hunter_type)
        
        # Shared systems (injected from orchestrator)
        self.research_memory = research_memory
        self.research_plan = research_plan
        self.planning_tool = PlanningTool(research_plan, hunter_type) if research_plan else None
        
        # Deep research state
        self.current_todo = None
        self.research_context = ""
        self.collaboration_notes = []
        
        if not self.silent:
            print(f"🐆 Deep Research Agent initialized: {hunter_type.upper()}")
            if self.hunter_profile:
                print(f"   Specialization: {self.hunter_profile.expertise.value}")
    
    async def deep_research_run(self, research_query: str) -> Dict[str, Any]:
        """Main deep research method with planning and collaboration"""
        
        if not self.silent:
            print(f"\n🚀 {self.hunter_type.upper()} starting deep research...")
            print(f"Query: {research_query}")
        
        # Step 1: Get specialized system prompt
        specialized_prompt = self._generate_specialized_prompt(research_query)
        
        # Step 2: Load research context from team
        if self.research_memory:
            self.research_context = self.research_memory.generate_research_context(self.hunter_type)
        
        # Step 3: Get next todo from plan
        if self.planning_tool:
            self.current_todo = self.planning_tool.get_next_todo()
            if self.current_todo:
                self.planning_tool.start_todo(self.current_todo.id)
                await self.send_step_update("todo_started", {
                    "todo_id": self.current_todo.id,
                    "description": self.current_todo.description
                })
        
        # Step 4: Execute specialized research
        research_result = await self._execute_specialized_research(research_query, specialized_prompt)
        
        # Step 5: Process and store findings
        findings = await self._process_research_results(research_result)
        
        # Step 6: Complete todo and update plan
        if self.current_todo and self.planning_tool:
            self.planning_tool.complete_todo(self.current_todo.id, {
                "findings_count": len(findings),
                "execution_time": time.time() - self.current_todo.created_at,
                "quality_score": self._calculate_quality_score(findings)
            })
            
            await self.send_step_update("todo_completed", {
                "todo_id": self.current_todo.id,
                "findings_count": len(findings)
            })
        
        # Step 7: Share results with team
        collaboration_summary = await self._generate_collaboration_summary(findings)
        
        return {
            "hunter_type": self.hunter_type,
            "research_query": research_query,
            "findings": findings,
            "collaboration_summary": collaboration_summary,
            "todo_completed": self.current_todo.id if self.current_todo else None,
            "specialized_result": research_result
        }
    
    def _generate_specialized_prompt(self, research_query: str) -> str:
        """Generate specialized system prompt based on hunter type"""
        
        base_prompt = self.config['system_prompt']
        
        if self.hunter_profile:
            specialized_prompt = self.role_system.generate_hunter_system_prompt(
                self.hunter_type, research_query
            )
        else:
            specialized_prompt = base_prompt
        
        # Add research context from team
        if self.research_context:
            specialized_prompt += f"\n\nTEAM RESEARCH CONTEXT:\n{self.research_context}"
        
        # Add current todo context
        if self.current_todo:
            specialized_prompt += f"\n\nCURRENT TODO:\n{self.current_todo.description}"
            specialized_prompt += f"\nPriority: {self.current_todo.priority}/5"
            specialized_prompt += f"\nEstimated time: {self.current_todo.estimated_time} minutes"
        
        # Add collaboration instructions
        specialized_prompt += self._get_collaboration_instructions()
        
        return specialized_prompt
    
    def _get_collaboration_instructions(self) -> str:
        """Get specific collaboration instructions based on hunter type"""
        
        instructions = "\n\nCOLLABORATION PROTOCOL:\n"
        
        if self.hunter_type == "source_scout":
            instructions += """
• Focus on SOURCE DISCOVERY and EVALUATION
• Create comprehensive source map for the team
• Prioritize credible, recent, and diverse sources
• Assess source quality and relevance scores
• Note sources that need deeper analysis by analysts
"""
        elif self.hunter_type == "deep_analyst":
            instructions += """
• Focus on DEEP CONTENT ANALYSIS of sources found by scouts
• Extract detailed facts, figures, and examples
• Identify patterns and themes in the information
• Note claims that need verification by fact checkers
• Prepare detailed findings for synthesis
"""
        elif self.hunter_type == "fact_checker":
            instructions += """
• Focus on VERIFICATION and CROSS-REFERENCING
• Validate claims made by analysts against multiple sources
• Check dates, statistics, and factual assertions
• Identify contradictions and resolve them
• Provide confidence scores for verified information
"""
        elif self.hunter_type == "insight_synthesizer":
            instructions += """
• Focus on SYNTHESIS and INSIGHT GENERATION
• Combine all team findings into coherent insights
• Identify actionable recommendations and implications
• Create comprehensive summary of research
• Highlight key findings and their significance
"""
        
        instructions += "\n• ALWAYS coordinate with team through shared research memory"
        instructions += "\n• BUILD on previous hunters' work, don't duplicate effort"
        instructions += "\n• MAINTAIN your specialized focus while supporting team goals"
        
        return instructions
    
    async def _execute_specialized_research(self, research_query: str, specialized_prompt: str) -> str:
        """Execute research using specialized prompt and approach with enhanced real-time updates"""
        
        # Prepare messages with specialized context
        messages = [
            {
                "role": "system",
                "content": specialized_prompt
            },
            {
                "role": "user", 
                "content": f"Execute your specialized research for: {research_query}"
            }
        ]
        
        await self.send_step_update("specialized_research_start", {
            "hunter_type": self.hunter_type,
            "specialization": self.hunter_profile.expertise.value if self.hunter_profile else "general",
            "message": f"🎯 {self.hunter_type.replace('_', ' ').title()} starting specialized research..."
        })
        
        # Enhanced step updates during research
        await self.send_step_update("research_phase", {
            "phase": "initialization",
            "message": f"🔧 {self.hunter_type.replace('_', ' ').title()} initializing research tools..."
        })
        
        # Run enhanced research with specialized context (call parent method to avoid recursion)
        result = await super().enhanced_run(research_query)
        
        await self.send_step_update("research_phase", {
            "phase": "completion",
            "message": f"✅ {self.hunter_type.replace('_', ' ').title()} research completed!"
        })
        
        return result
    
    async def _process_research_results(self, research_result: str) -> List[Dict[str, Any]]:
        """Process research results and extract structured findings"""
        
        findings = []
        
        if not self.research_memory:
            return findings
        
        # Extract findings based on hunter type specialization
        if self.hunter_type == "source_scout":
            findings = await self._extract_source_findings(research_result)
        elif self.hunter_type == "deep_analyst":
            findings = await self._extract_analysis_findings(research_result)
        elif self.hunter_type == "fact_checker":
            findings = await self._extract_verification_findings(research_result)
        elif self.hunter_type == "insight_synthesizer":
            findings = await self._extract_synthesis_findings(research_result)
        
        # Store findings in shared memory
        for finding in findings:
            finding_id = self.research_memory.add_finding(
                hunter_id=f"{self.hunter_type}_{self.agent_id}",
                hunter_type=self.hunter_type,
                finding_type=finding["type"],
                content=finding["content"],
                sources=finding["sources"],
                confidence=finding["confidence"],
                tags=finding.get("tags", []),
                metadata=finding.get("metadata", {})
            )
            finding["finding_id"] = finding_id
        
        return findings
    
    async def _extract_source_findings(self, research_result: str) -> List[Dict[str, Any]]:
        """Extract source-related findings for source scout"""
        
        findings = []
        
        # Simple extraction - in real implementation, use LLM to parse
        lines = research_result.split('\n')
        sources = []
        
        for line in lines:
            if 'http' in line.lower() or 'www.' in line.lower():
                # Extract URL and context
                sources.append(line.strip())
        
        if sources:
            findings.append({
                "type": FindingType.SOURCE,
                "content": f"Discovered {len(sources)} sources for research",
                "sources": sources[:10],  # Limit to top 10
                "confidence": 0.8,
                "tags": ["source_discovery"],
                "metadata": {"source_count": len(sources)}
            })
        
        return findings
    
    async def _extract_analysis_findings(self, research_result: str) -> List[Dict[str, Any]]:
        """Extract analysis findings for deep analyst"""
        
        findings = []
        
        # Extract facts and insights
        lines = research_result.split('\n')
        facts = []
        
        for line in lines:
            line = line.strip()
            if any(indicator in line.lower() for indicator in ['according to', 'studies show', 'research indicates', 'data shows']):
                facts.append(line)
        
        if facts:
            findings.append({
                "type": FindingType.FACT,
                "content": f"Extracted {len(facts)} factual insights from sources",
                "sources": [],  # Would be populated from actual source tracking
                "confidence": 0.7,
                "tags": ["deep_analysis", "facts"],
                "metadata": {"fact_count": len(facts), "facts": facts[:5]}
            })
        
        return findings
    
    async def _extract_verification_findings(self, research_result: str) -> List[Dict[str, Any]]:
        """Extract verification findings for fact checker"""
        
        findings = []
        
        # Look for verification patterns
        if any(word in research_result.lower() for word in ['verified', 'confirmed', 'cross-referenced']):
            findings.append({
                "type": FindingType.VERIFICATION,
                "content": "Verification analysis completed for team findings",
                "sources": [],
                "confidence": 0.9,
                "tags": ["verification", "fact_check"],
                "metadata": {"verification_type": "cross_reference"}
            })
        
        return findings
    
    async def _extract_synthesis_findings(self, research_result: str) -> List[Dict[str, Any]]:
        """Extract synthesis findings for insight synthesizer"""
        
        findings = []
        
        # Look for synthesis patterns
        if len(research_result) > 500:  # Substantial synthesis
            findings.append({
                "type": FindingType.SYNTHESIS,
                "content": "Comprehensive research synthesis completed",
                "sources": [],
                "confidence": 0.8,
                "tags": ["synthesis", "insights"],
                "metadata": {"synthesis_length": len(research_result)}
            })
        
        return findings
    
    async def _generate_collaboration_summary(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary for team collaboration"""
        
        summary = {
            "hunter_type": self.hunter_type,
            "findings_contributed": len(findings),
            "specialization_focus": self.hunter_profile.expertise.value if self.hunter_profile else "general",
            "collaboration_notes": [],
            "next_steps": [],
            "team_handoffs": []
        }
        
        # Add hunter-specific collaboration notes
        if self.hunter_type == "source_scout":
            summary["collaboration_notes"].append("Source map created for team analysis")
            summary["team_handoffs"].append("High-quality sources ready for deep analyst")
            
        elif self.hunter_type == "deep_analyst":
            summary["collaboration_notes"].append("Detailed content analysis completed")
            summary["team_handoffs"].append("Claims and facts ready for verification")
            
        elif self.hunter_type == "fact_checker":
            summary["collaboration_notes"].append("Verification and cross-referencing completed")
            summary["team_handoffs"].append("Validated findings ready for synthesis")
            
        elif self.hunter_type == "insight_synthesizer":
            summary["collaboration_notes"].append("Final synthesis and insights generated")
            summary["next_steps"].append("Research deliverable ready for presentation")
        
        return summary
    
    def _calculate_quality_score(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate quality score for completed work"""
        
        if not findings:
            return 0.0
        
        # Simple quality scoring based on finding types and confidence
        total_score = 0.0
        for finding in findings:
            confidence = finding.get("confidence", 0.5)
            type_bonus = {
                FindingType.SOURCE: 1.0,
                FindingType.FACT: 1.2,
                FindingType.VERIFICATION: 1.5,
                FindingType.SYNTHESIS: 1.3
            }.get(finding["type"], 1.0)
            
            total_score += confidence * type_bonus
        
        return min(total_score / len(findings), 1.0)
    
    # Override enhanced_run to use deep research when appropriate
    async def enhanced_run(self, user_input: str):
        """Enhanced run that can use deep research capabilities"""
        
        # Always fall back to standard enhanced run to avoid recursion
        # The orchestrator calls deep_research_run() directly when needed
        return await super().enhanced_run(user_input)
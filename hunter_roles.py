"""
Deep Research Hunter Specialization System
Defines specialized hunter types with unique capabilities and focus areas
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class HunterExpertise(Enum):
    SOURCE_DISCOVERY = "source_discovery"
    DEEP_ANALYSIS = "deep_analysis" 
    FACT_VERIFICATION = "fact_verification"
    INSIGHT_SYNTHESIS = "insight_synthesis"

@dataclass
class HunterProfile:
    """Defines a hunter's specialization and capabilities"""
    hunter_type: str
    name: str
    expertise: HunterExpertise
    description: str
    primary_tools: List[str]
    search_strategies: List[str]
    success_metrics: List[str]
    collaboration_style: str
    
class HunterRoleSystem:
    """Manages hunter role definitions and assignments"""
    
    def __init__(self):
        self.hunter_profiles = self._define_hunter_profiles()
        self.role_sequence = ["source_scout", "deep_analyst", "fact_checker", "insight_synthesizer"]
    
    def _define_hunter_profiles(self) -> Dict[str, HunterProfile]:
        """Define all available hunter profiles"""
        
        profiles = {}
        
        # SOURCE SCOUT - Reconnaissance and initial source discovery
        profiles["source_scout"] = HunterProfile(
            hunter_type="source_scout",
            name="Source Scout",
            expertise=HunterExpertise.SOURCE_DISCOVERY,
            description="Specialized in rapid source discovery, evaluation, and reconnaissance",
            primary_tools=["search_web", "source_evaluator"],
            search_strategies=[
                "Broad keyword sweeps with multiple search engines",
                "Authority site targeting (official sources, institutions)",
                "Recent content prioritization (2024-2025)",
                "Source diversity maximization",
                "Geographic and domain-specific searches"
            ],
            success_metrics=[
                "Number of unique quality sources discovered",
                "Source credibility scores",
                "Coverage breadth across different perspectives",
                "Recency of information found"
            ],
            collaboration_style="Sets foundation for team, provides source map to other hunters"
        )
        
        # DEEP ANALYST - Comprehensive content analysis and extraction
        profiles["deep_analyst"] = HunterProfile(
            hunter_type="deep_analyst", 
            name="Deep Analyst",
            expertise=HunterExpertise.DEEP_ANALYSIS,
            description="Specialized in thorough content analysis and detailed information extraction",
            primary_tools=["search_web", "content_extractor", "pattern_analyzer"],
            search_strategies=[
                "Deep-dive searches on specific topics identified by scout",
                "Technical and detailed keyword combinations", 
                "Academic and research paper searches",
                "Industry-specific terminology usage",
                "Comparative analysis searches"
            ],
            success_metrics=[
                "Depth of information extracted",
                "Number of specific facts and figures gathered",
                "Quality of examples and case studies found",
                "Technical accuracy of information"
            ],
            collaboration_style="Builds on scout findings, provides detailed content for verification"
        )
        
        # FACT CHECKER - Verification and cross-referencing specialist  
        profiles["fact_checker"] = HunterProfile(
            hunter_type="fact_checker",
            name="Fact Checker", 
            expertise=HunterExpertise.FACT_VERIFICATION,
            description="Specialized in verifying claims and cross-referencing information",
            primary_tools=["search_web", "fact_validator", "cross_referencer"],
            search_strategies=[
                "Verification searches for specific claims and statistics",
                "Alternative source searches for same information",
                "Authoritative source confirmation searches",
                "Date and timeline verification searches",
                "Contradiction detection searches"
            ],
            success_metrics=[
                "Percentage of claims verified",
                "Number of sources cross-referenced", 
                "Accuracy confidence scores",
                "Contradictions identified and resolved"
            ],
            collaboration_style="Validates analyst findings, ensures information reliability"
        )
        
        # INSIGHT SYNTHESIZER - Synthesis and insight generation
        profiles["insight_synthesizer"] = HunterProfile(
            hunter_type="insight_synthesizer",
            name="Insight Synthesizer",
            expertise=HunterExpertise.INSIGHT_SYNTHESIS, 
            description="Specialized in combining findings into actionable insights and recommendations",
            primary_tools=["analysis_tool", "pattern_matcher", "insight_generator"],
            search_strategies=[
                "Trend identification searches",
                "Implication and consequence searches", 
                "Best practice and recommendation searches",
                "Future outlook and prediction searches",
                "Actionable insight validation searches"
            ],
            success_metrics=[
                "Quality of synthesized insights",
                "Actionability of recommendations",
                "Comprehensiveness of final analysis",
                "User value and relevance"
            ],
            collaboration_style="Synthesizes all team findings into final comprehensive research"
        )
        
        return profiles
    
    def get_hunter_profile(self, hunter_type: str) -> Optional[HunterProfile]:
        """Get profile for a specific hunter type"""
        return self.hunter_profiles.get(hunter_type)
    
    def get_all_profiles(self) -> Dict[str, HunterProfile]:
        """Get all hunter profiles"""
        return self.hunter_profiles.copy()
    
    def get_optimal_team_composition(self, research_complexity: str = "standard") -> List[str]:
        """Get optimal team composition based on research complexity"""
        
        compositions = {
            "simple": ["source_scout", "deep_analyst"],
            "standard": ["source_scout", "deep_analyst", "fact_checker", "insight_synthesizer"], 
            "complex": ["source_scout", "deep_analyst", "fact_checker", "insight_synthesizer"],
            "verification_heavy": ["source_scout", "fact_checker", "deep_analyst", "insight_synthesizer"]
        }
        
        return compositions.get(research_complexity, compositions["standard"])
    
    def generate_hunter_system_prompt(self, hunter_type: str, research_query: str) -> str:
        """Generate specialized system prompt for a hunter type"""
        
        profile = self.get_hunter_profile(hunter_type)
        if not profile:
            raise ValueError(f"Unknown hunter type: {hunter_type}")
        
        prompt = f"""
🐆 YOU ARE: {profile.name.upper()} - ELITE RESEARCH SPECIALIST

HUNTER IDENTITY:
Role: {profile.description}
Expertise: {profile.expertise.value.replace('_', ' ').title()}
Mission: {research_query}

🎯 YOUR SPECIALIZATION:
{chr(10).join(f"• {strategy}" for strategy in profile.search_strategies)}

🔧 YOUR PRIMARY TOOLS:
{chr(10).join(f"• {tool}" for tool in profile.primary_tools)}

📊 SUCCESS METRICS:
{chr(10).join(f"• {metric}" for metric in profile.success_metrics)}

🤝 TEAM COLLABORATION:
{profile.collaboration_style}

OPERATING PROTOCOL:
1. FOCUS EXCLUSIVELY on your specialization area
2. USE your specialized search strategies 
3. COLLABORATE by building on team members' work
4. MEASURE success against your specific metrics
5. MAINTAIN quality standards expected of your expertise

CRITICAL: You are part of a coordinated research team. Your role is to excel in your 
specialization while contributing to the overall research mission.
"""
        
        return prompt
    
    def get_hunter_capabilities(self, hunter_type: str) -> Dict[str, Any]:
        """Get detailed capabilities for a hunter type"""
        
        profile = self.get_hunter_profile(hunter_type)
        if not profile:
            return {}
            
        return {
            "hunter_type": hunter_type,
            "name": profile.name,
            "expertise_area": profile.expertise.value,
            "primary_focus": profile.description,
            "tools": profile.primary_tools,
            "strategies": profile.search_strategies,
            "metrics": profile.success_metrics,
            "team_role": profile.collaboration_style
        }
    
    def validate_team_coverage(self, hunter_types: List[str]) -> Dict[str, Any]:
        """Validate that a team has good coverage across expertise areas"""
        
        expertise_covered = set()
        missing_expertise = set()
        
        for hunter_type in hunter_types:
            profile = self.get_hunter_profile(hunter_type)
            if profile:
                expertise_covered.add(profile.expertise)
        
        all_expertise = set(HunterExpertise)
        missing_expertise = all_expertise - expertise_covered
        
        coverage_score = len(expertise_covered) / len(all_expertise) * 100
        
        return {
            "coverage_score": coverage_score,
            "expertise_covered": [exp.value for exp in expertise_covered],
            "missing_expertise": [exp.value for exp in missing_expertise],
            "team_balanced": coverage_score >= 75,
            "recommendations": self._generate_team_recommendations(missing_expertise)
        }
    
    def _generate_team_recommendations(self, missing_expertise: set) -> List[str]:
        """Generate recommendations for improving team composition"""
        
        recommendations = []
        
        if HunterExpertise.SOURCE_DISCOVERY in missing_expertise:
            recommendations.append("Add Source Scout for better initial source discovery")
            
        if HunterExpertise.DEEP_ANALYSIS in missing_expertise:
            recommendations.append("Add Deep Analyst for thorough content analysis")
            
        if HunterExpertise.FACT_VERIFICATION in missing_expertise:
            recommendations.append("Add Fact Checker for information validation")
            
        if HunterExpertise.INSIGHT_SYNTHESIS in missing_expertise:
            recommendations.append("Add Insight Synthesizer for final analysis")
        
        return recommendations
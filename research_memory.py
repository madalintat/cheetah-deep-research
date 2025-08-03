"""
Deep Research Memory System
Shared knowledge base for hunter collaboration and research persistence
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class FindingType(Enum):
    SOURCE = "source"
    FACT = "fact"
    INSIGHT = "insight"
    VERIFICATION = "verification"
    SYNTHESIS = "synthesis"

class SourceQuality(Enum):
    EXCELLENT = "excellent"  # Official, authoritative, recent
    GOOD = "good"           # Reliable, well-sourced
    FAIR = "fair"           # Decent but limited
    POOR = "poor"           # Questionable or outdated

@dataclass
class ResearchFinding:
    """A single research finding with metadata"""
    finding_id: str
    hunter_id: str
    hunter_type: str
    finding_type: FindingType
    content: str
    sources: List[str]
    confidence: float  # 0.0 to 1.0
    timestamp: float
    related_findings: List[str] = None
    verification_status: str = "unverified"  # unverified, verified, disputed
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.related_findings is None:
            self.related_findings = []
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['finding_type'] = self.finding_type.value
        return data

@dataclass 
class SourceRecord:
    """Record of a research source with quality assessment"""
    source_id: str
    url: str
    title: str
    domain: str
    discovered_by: str
    quality: SourceQuality
    credibility_score: float  # 0.0 to 1.0
    recency_score: float     # 0.0 to 1.0  
    relevance_score: float   # 0.0 to 1.0
    content_extracted: bool = False
    extraction_summary: str = ""
    timestamp: float = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.tags is None:
            self.tags = []
    
    def get_overall_score(self) -> float:
        """Calculate overall source quality score"""
        weights = {
            'credibility': 0.4,
            'recency': 0.3, 
            'relevance': 0.3
        }
        
        return (
            self.credibility_score * weights['credibility'] +
            self.recency_score * weights['recency'] +
            self.relevance_score * weights['relevance']
        )
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['quality'] = self.quality.value
        return data

class ResearchMemory:
    """Shared memory system for research collaboration"""
    
    def __init__(self, research_query: str):
        self.research_query = research_query
        self.session_id = f"session_{int(time.time())}"
        
        # Core data structures
        self.findings: Dict[str, ResearchFinding] = {}
        self.sources: Dict[str, SourceRecord] = {}
        self.cross_references: Dict[str, List[str]] = {}
        self.research_timeline: List[Dict[str, Any]] = []
        
        # Collaboration state
        self.hunter_progress: Dict[str, Dict[str, Any]] = {}
        self.shared_insights: List[str] = []
        self.key_themes: List[str] = []
        
        # Quality tracking
        self.verification_matrix: Dict[str, Dict[str, str]] = {}
        self.confidence_scores: Dict[str, float] = {}
        
        self.created_at = time.time()
    
    def add_finding(self, hunter_id: str, hunter_type: str, finding_type: FindingType,
                   content: str, sources: List[str], confidence: float = 0.8,
                   tags: List[str] = None, metadata: Dict[str, Any] = None) -> str:
        """Add a new research finding"""
        
        finding_id = f"finding_{len(self.findings):04d}"
        
        finding = ResearchFinding(
            finding_id=finding_id,
            hunter_id=hunter_id,
            hunter_type=hunter_type,
            finding_type=finding_type,
            content=content,
            sources=sources,
            confidence=confidence,
            timestamp=time.time(),
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self.findings[finding_id] = finding
        
        # Update timeline
        self.research_timeline.append({
            "type": "finding_added",
            "finding_id": finding_id,
            "hunter_type": hunter_type,
            "timestamp": finding.timestamp,
            "summary": content[:100] + "..." if len(content) > 100 else content
        })
        
        # Auto-detect related findings
        self._detect_related_findings(finding_id)
        
        return finding_id
    
    def add_source(self, hunter_id: str, url: str, title: str, 
                  quality: SourceQuality, credibility: float, 
                  recency: float, relevance: float,
                  extraction_summary: str = "", tags: List[str] = None) -> str:
        """Add a new source record"""
        
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        source_id = f"source_{len(self.sources):04d}"
        
        source = SourceRecord(
            source_id=source_id,
            url=url,
            title=title,
            domain=domain,
            discovered_by=hunter_id,
            quality=quality,
            credibility_score=credibility,
            recency_score=recency,
            relevance_score=relevance,
            extraction_summary=extraction_summary,
            tags=tags or []
        )
        
        self.sources[source_id] = source
        
        # Update timeline
        self.research_timeline.append({
            "type": "source_added",
            "source_id": source_id,
            "hunter_id": hunter_id,
            "url": url,
            "quality": quality.value,
            "timestamp": source.timestamp
        })
        
        return source_id
    
    def verify_finding(self, finding_id: str, verifier_hunter: str, 
                      verification_result: str, evidence: List[str] = None):
        """Add verification for a finding"""
        
        if finding_id in self.findings:
            finding = self.findings[finding_id]
            finding.verification_status = verification_result
            
            # Update verification matrix
            if finding_id not in self.verification_matrix:
                self.verification_matrix[finding_id] = {}
            
            self.verification_matrix[finding_id][verifier_hunter] = verification_result
            
            # Update timeline
            self.research_timeline.append({
                "type": "finding_verified",
                "finding_id": finding_id,
                "verifier": verifier_hunter,
                "result": verification_result,
                "timestamp": time.time()
            })
    
    def cross_reference(self, finding_id_1: str, finding_id_2: str, 
                       relationship: str = "related"):
        """Create cross-reference between findings"""
        
        if finding_id_1 not in self.cross_references:
            self.cross_references[finding_id_1] = []
        if finding_id_2 not in self.cross_references:
            self.cross_references[finding_id_2] = []
        
        # Bidirectional relationship
        self.cross_references[finding_id_1].append(finding_id_2)
        self.cross_references[finding_id_2].append(finding_id_1)
        
        # Update finding objects
        if finding_id_1 in self.findings:
            self.findings[finding_id_1].related_findings.append(finding_id_2)
        if finding_id_2 in self.findings:
            self.findings[finding_id_2].related_findings.append(finding_id_1)
    
    def get_findings_by_hunter(self, hunter_type: str) -> List[ResearchFinding]:
        """Get all findings from a specific hunter type"""
        return [f for f in self.findings.values() if f.hunter_type == hunter_type]
    
    def get_findings_by_type(self, finding_type: FindingType) -> List[ResearchFinding]:
        """Get all findings of a specific type"""
        return [f for f in self.findings.values() if f.finding_type == finding_type]
    
    def get_top_sources(self, limit: int = 10) -> List[SourceRecord]:
        """Get top sources by overall quality score"""
        sources = list(self.sources.values())
        sources.sort(key=lambda x: x.get_overall_score(), reverse=True)
        return sources[:limit]
    
    def get_verified_findings(self) -> List[ResearchFinding]:
        """Get all verified findings"""
        return [f for f in self.findings.values() if f.verification_status == "verified"]
    
    def get_hunter_summary(self, hunter_type: str) -> Dict[str, Any]:
        """Get summary of what other hunters have discovered"""
        
        other_findings = [f for f in self.findings.values() if f.hunter_type != hunter_type]
        other_sources = [s for s in self.sources.values() if s.discovered_by != hunter_type]
        
        summary = {
            "total_findings": len(other_findings),
            "findings_by_type": {},
            "top_sources": [],
            "key_insights": [],
            "verification_needed": []
        }
        
        # Group findings by type
        for finding in other_findings:
            ftype = finding.finding_type.value
            if ftype not in summary["findings_by_type"]:
                summary["findings_by_type"][ftype] = 0
            summary["findings_by_type"][ftype] += 1
        
        # Top 5 sources from other hunters
        top_sources = sorted(other_sources, key=lambda x: x.get_overall_score(), reverse=True)[:5]
        summary["top_sources"] = [
            {"url": s.url, "title": s.title, "score": s.get_overall_score()}
            for s in top_sources
        ]
        
        # Key insights needing verification
        unverified = [f for f in other_findings if f.verification_status == "unverified"]
        summary["verification_needed"] = [
            {"id": f.finding_id, "content": f.content[:100] + "..."}
            for f in unverified[:3]
        ]
        
        return summary
    
    def generate_research_context(self, hunter_type: str) -> str:
        """Generate context summary for a hunter"""
        
        summary = self.get_hunter_summary(hunter_type)
        context = f"RESEARCH CONTEXT for {hunter_type.upper()}:\n"
        context += f"Query: {self.research_query}\n\n"
        
        context += "TEAM PROGRESS SO FAR:\n"
        context += f"• {summary['total_findings']} findings discovered by other hunters\n"
        context += f"• {len(self.sources)} sources identified\n"
        context += f"• {len(self.get_verified_findings())} findings verified\n\n"
        
        if summary['top_sources']:
            context += "TOP SOURCES FOUND:\n"
            for i, source in enumerate(summary['top_sources'], 1):
                context += f"{i}. {source['title']} (Score: {source['score']:.2f})\n"
        
        if summary['verification_needed']:
            context += "\nFINDINGS NEEDING VERIFICATION:\n"
            for finding in summary['verification_needed']:
                context += f"• {finding['content']}\n"
        
        return context
    
    def _detect_related_findings(self, new_finding_id: str):
        """Auto-detect related findings using simple keyword matching"""
        
        new_finding = self.findings[new_finding_id]
        new_words = set(new_finding.content.lower().split())
        
        for existing_id, existing_finding in self.findings.items():
            if existing_id == new_finding_id:
                continue
                
            existing_words = set(existing_finding.content.lower().split())
            
            # Simple keyword overlap detection
            overlap = len(new_words.intersection(existing_words))
            if overlap >= 3:  # Threshold for relatedness
                self.cross_reference(new_finding_id, existing_id, "keyword_related")
    
    def export_memory(self) -> Dict[str, Any]:
        """Export complete memory state"""
        return {
            "session_id": self.session_id,
            "research_query": self.research_query,
            "created_at": self.created_at,
            "findings": {fid: f.to_dict() for fid, f in self.findings.items()},
            "sources": {sid: s.to_dict() for sid, s in self.sources.items()},
            "cross_references": self.cross_references,
            "timeline": self.research_timeline,
            "verification_matrix": self.verification_matrix,
            "summary": {
                "total_findings": len(self.findings),
                "total_sources": len(self.sources),
                "verified_findings": len(self.get_verified_findings()),
                "top_source_domains": self._get_top_domains()
            }
        }
    
    def _get_top_domains(self) -> List[str]:
        """Get most common source domains"""
        domain_counts = {}
        for source in self.sources.values():
            domain_counts[source.domain] = domain_counts.get(source.domain, 0) + 1
        
        return sorted(domain_counts.keys(), key=lambda d: domain_counts[d], reverse=True)[:5]
"""
Deep Research Planning System - Todo-based task management for agents
Inspired by Claude Code's planning methodology
"""

import json
import time
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

class TodoStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    BLOCKED = "blocked"

@dataclass
class ResearchTodo:
    """A single research todo item"""
    id: str
    description: str
    hunter_type: str
    priority: int  # 1-5, 1 being highest
    status: TodoStatus = TodoStatus.PENDING
    estimated_time: int = 5  # minutes
    dependencies: List[str] = None  # todo IDs this depends on
    results: Dict[str, Any] = None
    created_at: float = None
    completed_at: float = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.results is None:
            self.results = {}
        if self.created_at is None:
            self.created_at = time.time()
    
    def mark_in_progress(self):
        """Mark todo as in progress"""
        self.status = TodoStatus.IN_PROGRESS
        
    def mark_completed(self, results: Dict[str, Any] = None):
        """Mark todo as completed with optional results"""
        self.status = TodoStatus.COMPLETED
        self.completed_at = time.time()
        if results:
            self.results.update(results)
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['status'] = self.status.value
        return data

class ResearchPlan:
    """Manages the overall research plan with todos for deep research"""
    
    def __init__(self, query: str, hunter_types: List[str]):
        self.query = query
        self.hunter_types = hunter_types
        self.todos: List[ResearchTodo] = []
        self.created_at = time.time()
        self.plan_id = f"plan_{int(time.time())}"
        
        # Generate initial research plan
        self._generate_research_plan()
    
    def _generate_research_plan(self):
        """Generate comprehensive research todos based on query and hunter types"""
        
        # Define hunter-specific todo templates
        hunter_todo_templates = {
            "source_scout": [
                "Identify and evaluate 8-10 high-quality sources",
                "Assess source credibility and relevance scores",
                "Map information landscape and coverage gaps", 
                "Create source quality ranking matrix"
            ],
            "deep_analyst": [
                "Perform deep content extraction from top 5 sources",
                "Analyze information patterns and themes",
                "Extract detailed facts, figures, and examples",
                "Identify information quality and gaps"
            ],
            "fact_checker": [
                "Cross-reference claims across multiple sources",
                "Verify statistics and factual assertions",
                "Identify conflicting information and resolve",
                "Validate source dates and currency"
            ],
            "insight_synthesizer": [
                "Synthesize findings into coherent insights", 
                "Identify actionable recommendations",
                "Create structured summary with key points",
                "Prepare final research deliverable"
            ]
        }
        
        # Generate todos for each hunter type
        todo_id = 0
        for hunter_type in self.hunter_types:
            if hunter_type in hunter_todo_templates:
                templates = hunter_todo_templates[hunter_type]
                priority = 1 if hunter_type == "source_scout" else 2
                
                for i, template in enumerate(templates):
                    todo = ResearchTodo(
                        id=f"todo_{todo_id:03d}",
                        description=f"{template} for: {self.query}",
                        hunter_type=hunter_type,
                        priority=priority + i,
                        estimated_time=8 + (i * 3)  # Escalating time estimates
                    )
                    
                    # Set dependencies - later hunters depend on earlier ones
                    if hunter_type != "source_scout" and todo_id > 0:
                        # Find previous hunter's todos
                        prev_todos = [t for t in self.todos if t.hunter_type != hunter_type]
                        if prev_todos:
                            todo.dependencies = [prev_todos[-1].id]  # Depend on last todo of previous type
                    
                    self.todos.append(todo)
                    todo_id += 1
    
    def get_todos_for_hunter(self, hunter_type: str) -> List[ResearchTodo]:
        """Get todos assigned to a specific hunter type"""
        return [todo for todo in self.todos if todo.hunter_type == hunter_type]
    
    def get_available_todos(self, hunter_type: str) -> List[ResearchTodo]:
        """Get todos that are ready to be worked on (no pending dependencies)"""
        hunter_todos = self.get_todos_for_hunter(hunter_type)
        available = []
        
        for todo in hunter_todos:
            if todo.status == TodoStatus.PENDING:
                # Check if all dependencies are completed
                dependencies_met = True
                for dep_id in todo.dependencies:
                    dep_todo = self.get_todo_by_id(dep_id)
                    if dep_todo and dep_todo.status != TodoStatus.COMPLETED:
                        dependencies_met = False
                        break
                
                if dependencies_met:
                    available.append(todo)
        
        return sorted(available, key=lambda x: x.priority)
    
    def get_todo_by_id(self, todo_id: str) -> ResearchTodo:
        """Get a specific todo by ID"""
        for todo in self.todos:
            if todo.id == todo_id:
                return todo
        return None
    
    def get_progress(self) -> Dict[str, Any]:
        """Get overall research progress"""
        total = len(self.todos)
        completed = len([t for t in self.todos if t.status == TodoStatus.COMPLETED])
        in_progress = len([t for t in self.todos if t.status == TodoStatus.IN_PROGRESS])
        
        return {
            "total_todos": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": total - completed - in_progress,
            "progress_percentage": (completed / total * 100) if total > 0 else 0,
            "estimated_time_remaining": sum(
                t.estimated_time for t in self.todos 
                if t.status in [TodoStatus.PENDING, TodoStatus.IN_PROGRESS]
            )
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert research plan to dictionary for serialization"""
        return {
            "plan_id": self.plan_id,
            "query": self.query,
            "hunter_types": self.hunter_types,
            "todos": [todo.to_dict() for todo in self.todos],
            "created_at": self.created_at,
            "progress": self.get_progress()
        }

class PlanningTool:
    """Tool for agents to interact with their research plan"""
    
    def __init__(self, plan: ResearchPlan, hunter_type: str):
        self.plan = plan
        self.hunter_type = hunter_type
    
    def get_next_todo(self) -> ResearchTodo:
        """Get the next available todo for this hunter"""
        available = self.plan.get_available_todos(self.hunter_type)
        return available[0] if available else None
    
    def start_todo(self, todo_id: str) -> bool:
        """Mark a todo as started"""
        todo = self.plan.get_todo_by_id(todo_id)
        if todo and todo.status == TodoStatus.PENDING:
            todo.mark_in_progress()
            return True
        return False
    
    def complete_todo(self, todo_id: str, results: Dict[str, Any] = None) -> bool:
        """Mark a todo as completed with results"""
        todo = self.plan.get_todo_by_id(todo_id)
        if todo and todo.status == TodoStatus.IN_PROGRESS:
            todo.mark_completed(results)
            return True
        return False
    
    def get_plan_summary(self) -> str:
        """Get a text summary of the research plan for agent context"""
        todos = self.plan.get_todos_for_hunter(self.hunter_type)
        summary = f"RESEARCH PLAN for {self.hunter_type.upper()}:\n"
        summary += f"Query: {self.plan.query}\n\n"
        
        for i, todo in enumerate(todos, 1):
            status_emoji = {
                TodoStatus.PENDING: "⏳",
                TodoStatus.IN_PROGRESS: "🔄", 
                TodoStatus.COMPLETED: "✅",
                TodoStatus.BLOCKED: "🚫"
            }
            
            summary += f"{status_emoji[todo.status]} {i}. {todo.description}\n"
            if todo.dependencies:
                summary += f"   Depends on: {', '.join(todo.dependencies)}\n"
        
        progress = self.plan.get_progress()
        summary += f"\nOVERALL PROGRESS: {progress['completed']}/{progress['total_todos']} todos completed "
        summary += f"({progress['progress_percentage']:.1f}%)\n"
        
        return summary
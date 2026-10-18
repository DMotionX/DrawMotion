from typing import List, Any
from PySide6.QtCore import QPointF

class Action:
    def __init__(self, action_type: str, payload: Any, start_time: float = 0.0, duration: float = 0.0, priority: str = "medium"):
        self.action_type = action_type # 'draw', 'write', 'move-hand', 'pause'
        self.payload = payload         # The actual data (e.g., text string, image path)
        self.start_time = start_time
        self.duration = duration
        self.priority = priority       # 'high', 'medium', 'low'
        self.start_pos: QPointF = None
        self.end_pos: QPointF = None

class Phase:
    def __init__(self, name: str):
        self.name = name
        self.actions: List[Action] = []
        
    def add_action(self, action: Action):
        self.actions.append(action)

class ScenePlan:
    def __init__(self):
        self.phases: List[Phase] = []
        
    def add_phase(self, phase: Phase):
        self.phases.append(phase)

class HierarchicalPlanner:
    """
    Layer 3: Hierarchical Planning Engine
    Sorts and groups actions into logical phases.
    """
    
    @staticmethod
    def build_plan(raw_actions: List[Action]) -> ScenePlan:
        """
        Takes raw classified actions and organizes them into a hierarchical plan.
        Priority sorting: high -> medium -> low
        """
        plan = ScenePlan()
        
        # Phase 1: High Priority (e.g., main shapes, main diagrams)
        phase1 = Phase("Main Drawing")
        for a in raw_actions:
            if a.priority == "high":
                phase1.add_action(a)
                
        # Phase 2: Medium Priority (e.g., labels, text annotations)
        phase2 = Phase("Annotation")
        for a in raw_actions:
            if a.priority == "medium":
                phase2.add_action(a)
                
        # Phase 3: Low Priority (e.g., decorations, shading)
        phase3 = Phase("Details")
        for a in raw_actions:
            if a.priority == "low":
                phase3.add_action(a)
                
        # Only add phases that have actions
        if phase1.actions: plan.add_phase(phase1)
        if phase2.actions: plan.add_phase(phase2)
        if phase3.actions: plan.add_phase(phase3)
        
        return plan

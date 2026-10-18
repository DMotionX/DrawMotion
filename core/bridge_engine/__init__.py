from typing import List, Dict
from .scene_context import SceneContext, SceneObject
from .content_analyzer import ContentAnalyzer
from .semantic_classifier import SemanticClassifier
from .hierarchical_planner import HierarchicalPlanner, Action, ScenePlan
from .spatial_engine import SpatialEngine
from .transition_system import TransitionSystem
from PySide6.QtCore import QPointF, QRectF

class SmartBridgeEngine:
    """
    DrawMotion Smart Bridge Engine V2 - Orchestrator
    Intelligent Presentation Engine that bridges drawing and writing.
    """
    
    def __init__(self):
        self.context = SceneContext()
        
    def process_inputs(self, raw_inputs: List[Dict]) -> ScenePlan:
        """
        Main pipeline: Takes raw user inputs and outputs a fully scheduled ScenePlan.
        """
        actions = []
        
        # Step 1: Analyze & Classify
        for idx, input_item in enumerate(raw_inputs):
            analysis = ContentAnalyzer.analyze(input_item)
            mode = SemanticClassifier.classify(analysis, self.context)
            
            priority = input_item.get("priority", "medium")
            if analysis["type"] == "image":
                priority = "high" # Usually shapes are high priority
                
            action = Action(
                action_type=mode,
                payload=input_item["data"],
                priority=priority
            )
            
            # Store fake bounding box for testing
            action.start_pos = input_item.get("pos", QPointF(0,0))
            
            actions.append((action, analysis))
            
        # Step 2: Hierarchical Planning
        raw_actions_only = [a[0] for a in actions]
        plan = HierarchicalPlanner.build_plan(raw_actions_only)
        
        # Step 3: Scheduling & Spatial Alignment & Transitions
        current_time = 0.0
        last_action_end_pos = None
        
        for phase in plan.phases:
            for action in phase.actions:
                
                # Spatial Layout for Annotations
                if action.action_type == "annotate":
                    nearest_obj = self.context.find_nearest_object(action.start_pos)
                    if nearest_obj:
                        action.start_pos = SpatialEngine.find_best_label_position(nearest_obj, self.context, lang="EN")
                        
                # Add Transition if needed
                if last_action_end_pos:
                    transition = TransitionSystem.create_smooth_transition(last_action_end_pos, action.start_pos)
                    if transition:
                        # We would insert a transition action here in a real engine
                        current_time += transition["duration"]
                        
                # Schedule this action
                action.start_time = current_time
                action.duration = 2.0 # Placeholder for execution time
                current_time += action.duration
                
                # Update Context
                last_action_end_pos = QPointF(action.start_pos.x() + 50, action.start_pos.y() + 50) # Fake end pos
                self.context.update_hand_position(last_action_end_pos)
                self.context.set_mode(action.action_type)
                
                # Register in memory
                bbox = QRectF(action.start_pos.x(), action.start_pos.y(), 100, 100)
                self.context.add_object(SceneObject(str(id(action)), action.action_type, bbox))
                
        return plan

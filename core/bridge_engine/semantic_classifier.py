from typing import Dict
from .scene_context import SceneContext

class SemanticClassifier:
    """
    Layer 2: Semantic Classifier
    Decides the high-level 'mode' of operation (draw, write, annotate, diagram, hybrid).
    Context-aware: Uses SceneContext to inform decisions.
    """
    
    @staticmethod
    def classify(analysis_result: Dict, context: SceneContext) -> str:
        """
        Returns the rendering mode based on the analysis.
        """
        semantic_type = analysis_result.get("semantic", "unknown")
        
        # Check context: if we just drew a shape, and now we get text, it's likely an annotation.
        last_action = context.get_last_action()
        if last_action in ["draw", "diagram"] and semantic_type in ["sentence", "equation"]:
            # If the new item is text and we just drew a shape, it's an annotation.
            # In a real engine, we'd also check spatial proximity here.
            return "annotate"
            
        # Core Classification
        if semantic_type == "shape":
            return "draw"
        elif semantic_type == "sentence":
            return "write"
        elif semantic_type == "diagram_with_text":
            return "diagram"
        elif semantic_type == "equation":
            # Equations might require mixed drawing/writing (e.g., long fraction lines, integral signs)
            return "hybrid"
            
        # Default fallback
        if analysis_result["type"] == "image":
            return "draw"
        return "write"

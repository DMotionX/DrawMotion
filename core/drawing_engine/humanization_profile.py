from dataclasses import dataclass

@dataclass
class HumanizationProfile:
    """
    Defines the parameters for simulating human hand movement.
    These parameters are adaptive based on zoom level and element type.
    """
    jitter_amount: float = 0.0      # Random noise applied to points
    overshoot: float = 0.0          # How much lines extend past intersections
    sketch_passes: int = 1          # Number of times a line is redrawn (for sketch style)
    allow_humanization: bool = True # Can be forced off for diagrams/logos
    
    @classmethod
    def create_adaptive(cls, base_intensity: float, zoom_level: float, object_type: str) -> 'HumanizationProfile':
        """
        Factory method that calculates adaptive parameters.
        """
        if object_type in ["diagram", "logo"] or not base_intensity:
            return cls(allow_humanization=False)
            
        # If user zooms out a lot, we reduce the visual noise to prevent messy rendering
        zoom_factor = min(1.0, zoom_level) 
        
        jitter = (base_intensity * 5.0) * zoom_factor
        overshoot = (base_intensity * 10.0) * zoom_factor
        
        passes = 1
        if base_intensity > 0.7:
            passes = 3
        elif base_intensity > 0.4:
            passes = 2
            
        return cls(
            jitter_amount=jitter,
            overshoot=overshoot,
            sketch_passes=passes,
            allow_humanization=True
        )

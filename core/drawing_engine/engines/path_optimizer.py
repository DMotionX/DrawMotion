from typing import List
from PySide6.QtCore import QPointF
import math

class PathOptimizer:
    """
    Smart Direction Engine:
    Evaluates different permutations/directions of a path and chooses the optimal
    one based on a Cost Function.
    """
    
    @staticmethod
    def _calculate_cost(points: List[QPointF]) -> float:
        """
        Cost function based on:
        - Total path length
        - Number of sharp jumps (pen lifts)
        - Flow direction (left-to-right is generally cheaper for human hands)
        """
        if not points: return 0.0
        
        total_distance = 0.0
        pen_lifts = 0
        
        # Penalize right-to-left movement slightly to favor natural human writing direction
        direction_penalty = 0.0
        
        for i in range(1, len(points)):
            p1, p2 = points[i-1], points[i]
            dist = math.hypot(p2.x() - p1.x(), p2.y() - p1.y())
            total_distance += dist
            
            # If distance between consecutive points is large, it's a pen lift
            if dist > 50.0:
                pen_lifts += 1
                
            # Right-to-Left penalty (unless it's a vertical stroke)
            if p2.x() < p1.x() and abs(p2.x() - p1.x()) > abs(p2.y() - p1.y()):
                direction_penalty += 10.0
                
        return total_distance + (pen_lifts * 100.0) + direction_penalty

    @staticmethod
    def find_best_direction(points: List[QPointF]) -> List[QPointF]:
        """
        Returns the optimal sequence of points.
        """
        if not points:
            return []
            
        # Candidate 1: As is (usually whatever SVG gave us)
        c1 = points
        
        # Candidate 2: Reversed (bottom-up / right-left)
        c2 = list(reversed(points))
        
        # In a full implementation, we'd add top-to-bottom bounding box sorting here.
        # For now, we compare the original and reversed based on cost.
        
        cost1 = PathOptimizer._calculate_cost(c1)
        cost2 = PathOptimizer._calculate_cost(c2)
        
        return c1 if cost1 <= cost2 else c2

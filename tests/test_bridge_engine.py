import sys
import os

# Add project root to path so we can import core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.bridge_engine import SmartBridgeEngine
from PySide6.QtCore import QPointF

def run_test():
    engine = SmartBridgeEngine()
    
    # Simulate a user dropping a Shape and then some Text
    inputs = [
        {
            "type": "image",
            "data": "circle.svg",
            "pos": QPointF(100, 100),
            "priority": "high",
            "metadata": {"contains_text": False}
        },
        {
            "type": "text",
            "data": "Radius = 5cm",
            "pos": QPointF(100, 100), # User dropped it exactly on the circle
            "priority": "medium"
        }
    ]
    
    print("--- Running Smart Bridge Engine V2 ---")
    plan = engine.process_inputs(inputs)
    
    print(f"Total Phases: {len(plan.phases)}")
    for phase in plan.phases:
        print(f"\nPhase: {phase.name}")
        for action in phase.actions:
            print(f"  - Action: {action.action_type.upper()}")
            print(f"    Payload: {action.payload}")
            print(f"    Start Time: {action.start_time}s, Duration: {action.duration}s")
            print(f"    Pos: ({action.start_pos.x()}, {action.start_pos.y()})")
            
if __name__ == "__main__":
    run_test()

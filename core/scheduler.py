import math

class SmartScheduler:
    """
    Compiles actual canvas items into a Virtual Timeline schedule.
    Resolves overlaps by ensuring only one item is drawn at a time.
    Injects 'move-hand' actions between drawings.
    """
    def __init__(self, hand_speed=1000):
        self.hand_speed = hand_speed # pixels per second

    def compile(self, items):
        if not items:
            return []
            
        # 1. Sort items by their anim_delay (absolute start time)
        sorted_items = sorted(items, key=lambda x: (getattr(x, 'anim_delay', 0.0), x.zValue()))
        
        schedule = []
        current_time = 0.0
        
        # 2. Resolve Overlaps and Build Draw Queue
        for item in sorted_items:
            start_time = max(getattr(item, 'anim_delay', 0.0), current_time)
            duration = getattr(item, 'anim_duration', 8.0)
            end_time = start_time + duration
            
            schedule.append({
                'type': 'draw',
                'item': item,
                'start': start_time,
                'end': end_time
            })
            
            current_time = end_time
            
        # 3. Inject Hand Movement Actions
        final_schedule = []
        
        for i in range(len(schedule)):
            current = schedule[i]
            final_schedule.append(current)
            
            if i < len(schedule) - 1:
                next_item = schedule[i + 1]
                
                current_item_obj = current['item']
                next_item_obj = next_item['item']
                
                try:
                    if current_item_obj.parentItem() != next_item_obj.parentItem():
                        # Different scenes! Do not inject hand movement delay.
                        continue
                        
                    # Use bounding box centers for scheduling to completely avoid visual side effects
                    end_pos = current_item_obj.sceneBoundingRect().center()
                    start_pos = next_item_obj.sceneBoundingRect().center()
                    
                    dx = start_pos.x() - end_pos.x()
                    dy = start_pos.y() - end_pos.y()
                    distance = math.hypot(start_pos.x() - end_pos.x(), start_pos.y() - end_pos.y())
                    
                    move_time = distance / self.hand_speed
                    if move_time > 0.7:
                        move_time = 0.7 # Cap movement time to prevent boring delays
                        
                    move_start_time = current['end']
                    move_end_time = move_start_time + move_time
                    
                    final_schedule.append({
                        'type': 'move-hand',
                        'item': None,
                        'from_pos': end_pos,
                        'to_pos': start_pos,
                        'start': move_start_time,
                        'end': move_end_time,
                        'duration': move_time
                    })
                    
                    # Resolve overlaps with the movement
                    if next_item['start'] < move_end_time:
                        shift = move_end_time - next_item['start']
                        next_item['start'] += shift
                        next_item['end'] += shift
                        

                except Exception as e:
                    print("Error calculating hand movement:", e)
                    pass
                    
        return final_schedule

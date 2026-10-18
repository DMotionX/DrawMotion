from .fade import FadeTransition
from .slide import SlideTransition
from .wipe import WipeTransition
from .zoom import ZoomTransition
from .iris import IrisTransition
from .flash import FlashTransition
from .bounce_wipe import BounceWipeTransition
from .split import SplitTransition
from .squeeze import SqueezeTransition
from .color_dissolve import ColorDissolveTransition
from .door_wipe import DoorWipeTransition

__all__ = [
    'FadeTransition',
    'SlideTransition',
    'WipeTransition',
    'ZoomTransition',
    'IrisTransition',
    'FlashTransition',
    'BounceWipeTransition',
    'SplitTransition',
    'SqueezeTransition',
    'ColorDissolveTransition',
    'DoorWipeTransition'
]

# Registry: name → class, used by TransitionManager
TRANSITION_REGISTRY = {
    'fade':  FadeTransition,
    'slide': SlideTransition,
    'wipe':  WipeTransition,
    'zoom':  ZoomTransition,
    'iris':  IrisTransition,
    'flash': FlashTransition,
    'bounce': BounceWipeTransition,
    'split': SplitTransition,
    'squeeze': SqueezeTransition,
    'color_dissolve': ColorDissolveTransition,
    'door_wipe': DoorWipeTransition,
}

# Display metadata for each effect (used to build the UI picker)
TRANSITION_METADATA = [
    {
        'id':    'fade',
        'label': 'Fade',
        'color': '#7C3AED',   # purple
        'cls':   FadeTransition,
    },
    {
        'id':    'slide',
        'label': 'Slide',
        'color': '#2563EB',   # blue
        'cls':   SlideTransition,
    },
    {
        'id':    'wipe',
        'label': 'Wipe',
        'color': '#059669',   # emerald
        'cls':   WipeTransition,
    },
    {
        'id':    'zoom',
        'label': 'Zoom',
        'color': '#D97706',   # amber
        'cls':   ZoomTransition,
    },
    {
        'id':    'iris',
        'label': 'Iris',
        'color': '#DB2777',   # pink
        'cls':   IrisTransition,
    },
    {
        'id':    'flash',
        'label': 'Flash',
        'color': '#9CA3AF',   # gray/white
        'cls':   FlashTransition,
    },
    {
        'id':    'bounce',
        'label': 'Bounce',
        'color': '#F59E0B',   # orange
        'cls':   BounceWipeTransition,
    },
    {
        'id':    'split',
        'label': 'Split',
        'color': '#10B981',   # teal
        'cls':   SplitTransition,
    },
    {
        'id':    'squeeze',
        'label': 'Squeeze',
        'color': '#8B5CF6',   # light purple
        'cls':   SqueezeTransition,
    },
    {
        'id':    'color_dissolve',
        'label': 'Dissolve',
        'color': '#EC4899',   # hot pink
        'cls':   ColorDissolveTransition,
    },
    {
        'id':    'door_wipe',
        'label': 'Door Wipe',
        'color': '#3B82F6',   # light blue
        'cls':   DoorWipeTransition,
    }
]

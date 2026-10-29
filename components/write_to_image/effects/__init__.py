"""
DrawMotion Text Effects Package.
Provides decoupled pure-Python post-processing visual shaders/effects
and interactive QML preview widgets for text rendering.
"""

from .text_effects import (
    apply_text_effect,
    apply_glow_effect,
    apply_neon_effect,
    apply_ink_bleed_effect,
    apply_drop_shadow_effect,
    apply_glitch_effect,
    apply_holographic_effect,
    AVAILABLE_EFFECTS,
)
from .effects_bridge import TextEffectsBridge
from .effects_widget import TextEffectsWidget

__all__ = [
    'apply_text_effect',
    'apply_glow_effect',
    'apply_neon_effect',
    'apply_ink_bleed_effect',
    'apply_drop_shadow_effect',
    'apply_glitch_effect',
    'apply_holographic_effect',
    'AVAILABLE_EFFECTS',
    'TextEffectsBridge',
    'TextEffectsWidget',
]

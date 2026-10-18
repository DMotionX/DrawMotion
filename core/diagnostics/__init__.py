"""
DrawMotion Diagnostics & Lifecycle Engine
Provides zero-overhead startup tracking and runtime diagnostics.
"""
from .lifecycle_tracker import StartupLifecycleTracker

__all__ = ["StartupLifecycleTracker"]

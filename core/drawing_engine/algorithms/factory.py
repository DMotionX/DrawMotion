from typing import Type, Dict
from .base_algorithm import BaseDrawingAlgorithm
from .solid_reveal.algorithm import SolidRevealAlgorithm
from .clean_outline.algorithm import CleanOutlineAlgorithm
from .organic_sketch.algorithm import OrganicSketchAlgorithm
from .hatch_shading.algorithm import HatchShadingAlgorithm
from .line_art.algorithm import LineArtAlgorithm
from .professional.algorithm import ProfessionalAlgorithm
from .topographic.algorithm import TopographicShadingAlgorithm

# Phase 1: Isolated Library Assets
from .library_assets.smart_blueprint import SmartBlueprintAlgorithm
from .library_assets.icon_sketch import IconSketchAlgorithm
from .library_assets.fast_contour import FastContourAlgorithm

class AlgorithmFactory:
    @staticmethod
    def get_algorithm(style_name: str) -> BaseDrawingAlgorithm:
        algorithms = {
            "Professional": ProfessionalAlgorithm, 
            "Sketch": OrganicSketchAlgorithm,
            "Educational": HatchShadingAlgorithm,
            "Solid Reveal": SolidRevealAlgorithm,
            "Clean Outline": CleanOutlineAlgorithm,
            "Organic Sketch": OrganicSketchAlgorithm,
            "Hatch Shading": TopographicShadingAlgorithm,
            "Line Art (Skeleton)": LineArtAlgorithm,
            "Smart Blueprint (Library)": SmartBlueprintAlgorithm,
            "Icon Sketch (Library)": IconSketchAlgorithm,
            "Fast Contour (Library)": FastContourAlgorithm
        }
        algo_class = algorithms.get(style_name, SolidRevealAlgorithm)
        return algo_class()

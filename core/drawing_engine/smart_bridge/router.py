import os

def create_smart_item(file_path, pixmap):
    """
    Smart Bridge (Phase 3)
    Routes the file to the correct Engine based on extension.
    - SVG -> SVGCanvasItem (Vector Engine)
    - PNG/JPG -> AnimatedRasterItem (Raster Engine)
    - Fallback -> AnimatedImageItem
    """
    ext = file_path.lower().split('.')[-1]
    
    if ext == 'svg':
        from core.drawing_engine.smart_bridge.analyzer import SVGAnalyzer
        if SVGAnalyzer.is_complex(file_path):
            # Complex SVG (AI generated/Heavy) -> Rasterize it and use Zero-Lag Raster Engine
            from core.drawing_engine.raster_engine.raster_item import AnimatedRasterItem
            item = AnimatedRasterItem(pixmap)
            item.layer_name = "Rasterized SVG" # UI Indicator for the user
            item.drawing_style = "Zero-Lag Sweep"
            return item
        else:
            # Simple SVG -> Normal Vector Engine
            from asset_library.engine.svg_canvas_item import SVGCanvasItem
            return SVGCanvasItem(file_path)
    else:
        # User requested to keep the advanced algorithms (Solid Reveal, etc.) for normal PNG/JPG
        # Therefore, we route back to AnimatedImageItem which contains AlgorithmFactory.
        # AnimatedRasterItem is kept in the codebase for future explicit "Zero-Lag Mode" toggles.
        from graphics.animated_image_item import AnimatedImageItem
        return AnimatedImageItem(pixmap)

import os
from utils.paths import get_app_data_dir

class AssetLoader:
    """
    Core loader for SVG assets.
    Responsible for fetching the SVGs from both internal resources and AppData.
    """
    def __init__(self):
        self.appdata_svg_dir = os.path.join(get_app_data_dir(), "assets", "svg")
        os.makedirs(self.appdata_svg_dir, exist_ok=True)
        
        self.internal_svg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "library", "svg"))

    def get_all_assets(self):
        assets = []
        
        # Load internal preset SVGs
        if os.path.exists(self.internal_svg_dir):
            for filename in os.listdir(self.internal_svg_dir):
                if filename.lower().endswith('.svg'):
                    filepath = os.path.join(self.internal_svg_dir, filename)
                    assets.append({
                        'filepath': filepath,
                        'name': os.path.splitext(filename)[0]
                    })
                    
        # Load user AppData SVGs
        if os.path.exists(self.appdata_svg_dir):
            for filename in os.listdir(self.appdata_svg_dir):
                if filename.lower().endswith('.svg'):
                    filepath = os.path.join(self.appdata_svg_dir, filename)
                    assets.append({
                        'filepath': filepath,
                        'name': os.path.splitext(filename)[0]
                    })
                    
        return assets

class ContentAnalyzer:
    """
    Layer 1: Multi-Level Content Analysis
    Extracts deep insights from raw inputs (geometry, text, layout, semantics).
    """
    
    @staticmethod
    def analyze(raw_content: dict) -> dict:
        """
        Analyzes a content dictionary.
        Expected raw_content keys: 'type' ('image' or 'text'), 'data' (Pixmap or string), 'bbox'
        """
        analysis = {
            "type": raw_content.get("type", "unknown"),
            "geometry": {"has_shapes": False, "complexity": 0},
            "text": {"has_text": False, "is_sentence": False, "is_equation": False},
            "layout": {"bbox": raw_content.get("bbox", None)},
            "semantic": "unknown"
        }
        
        # 1. Geometry & Text Detection (Simulated for images, direct for text)
        if analysis["type"] == "image":
            # In a full implementation, we'd run OpenCV/Tesseract here.
            # Mocking analysis: assume images have shapes.
            analysis["geometry"]["has_shapes"] = True
            analysis["geometry"]["complexity"] = 5  # Arbitrary complexity scale
            
            # Simulated OCR: checking if metadata hints at text
            if raw_content.get("metadata", {}).get("contains_text", False):
                analysis["text"]["has_text"] = True
                
        elif analysis["type"] == "text":
            text_str = raw_content.get("data", "")
            analysis["text"]["has_text"] = True
            
            # Simple NLP
            has_symbols = any(c in "+-*/=" for c in text_str)
            has_words = any(c.isalpha() for c in text_str)
            
            if has_symbols and not has_words:
                analysis["text"]["is_equation"] = True
            else:
                analysis["text"]["is_sentence"] = True
                if has_symbols:
                    analysis["text"]["is_equation"] = True # Mixed
                    
        # 2. Semantic Insight Extraction
        # E.g. Diagram, Sentence, Equation, Shape
        if analysis["type"] == "image":
            if analysis["text"]["has_text"]:
                analysis["semantic"] = "diagram_with_text"
            else:
                analysis["semantic"] = "shape"
                
        elif analysis["type"] == "text":
            if analysis["text"]["is_equation"]:
                analysis["semantic"] = "equation"
            else:
                analysis["semantic"] = "sentence"
                
        return analysis

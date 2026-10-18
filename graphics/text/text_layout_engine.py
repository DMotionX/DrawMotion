from PySide6.QtGui import QFontMetricsF, QTextOption, QTextLayout
from PySide6.QtCore import QRectF, Qt, QPointF
from .text_node_model import TextNodeModel

class TextLayoutEngine:
    """
    Computes precise bounding boxes, line breaks, and text options 
    based on the Model. It ensures correct rendering for RTL (Arabic) 
    and LTR (English) text without tying into the View layer.
    """
    
    @staticmethod
    def get_text_option(model: TextNodeModel) -> QTextOption:
        """
        Generates the QTextOption configuring alignment and text direction.
        """
        option = QTextOption()
        
        # Configure Alignment
        option.setAlignment(model.alignment)
        
        # Configure Direction
        if model.language == "ar":
            option.setTextDirection(Qt.LayoutDirection.RightToLeft)
        else:
            option.setTextDirection(Qt.LayoutDirection.LeftToRight)
            
        # Wrap mode
        option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        
        return option

    @staticmethod
    def compute_bounding_rect(model: TextNodeModel, fixed_width: float = -1) -> QRectF:
        """
        Calculates the exact bounding rectangle for the text based on its font and content.
        If fixed_width is > 0, it wraps text within that width.
        """
        if not model.text:
            # Return a default small box if empty
            fm = QFontMetricsF(model.get_font())
            return QRectF(0, 0, 100, fm.height())
            
        font = model.get_font()
        option = TextLayoutEngine.get_text_option(model)
        
        layout = QTextLayout(model.text, font)
        layout.setTextOption(option)
        
        # Calculate Layout
        y = 0.0
        max_width = 0.0
        
        layout.beginLayout()
        while True:
            line = layout.createLine()
            if not line.isValid():
                break
                
            if fixed_width > 0:
                line.setLineWidth(fixed_width)
            else:
                # If no fixed width, let it take natural width
                line.setLineWidth(10000) # Arbitrary large number
                
            line.setPosition(QPointF(0, y))
            y += line.height()
            
            # Track the widest line
            if line.naturalTextWidth() > max_width:
                max_width = line.naturalTextWidth()
                
        layout.endLayout()
        
        # Calculate final dimensions
        final_width = fixed_width if fixed_width > 0 else max_width
        
        # Add some padding to the bounding box
        padding = 10
        
        return QRectF(0, 0, final_width + padding * 2, y + padding * 2)
        
    @staticmethod
    def update_model_bounds(model: TextNodeModel, fixed_width: float = -1):
        """
        Helper method to compute bounds and directly update the model.
        """
        bounds = TextLayoutEngine.compute_bounding_rect(model, fixed_width)
        model.bounding_rect = bounds

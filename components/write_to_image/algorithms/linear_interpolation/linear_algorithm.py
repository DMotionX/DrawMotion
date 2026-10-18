import numpy as np
from ..base_algorithm import BaseWritingAlgorithm

class LinearInterpolationAlgorithm(BaseWritingAlgorithm):
    """
    نموذج الاستيفاء الخطي (Linear Interpolation Model).
    يقوم بكشف مسار الصورة بانتظام تام وتوزيع خطي ثابت من نقطة البداية إلى النهاية.
    """
    
    @property
    def style(self) -> str:
        return "linear_interpolation"
        
    def generate_times(self, seeds: list, is_rtl: bool) -> np.ndarray:
        """
        يولد وقت ظهور لكل بذرة بتوزيع خطي متساوٍ.
        """
        if not seeds:
            return np.array([])
            
        return np.linspace(0.0, 1.0, len(seeds))

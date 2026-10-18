import numpy as np
from ..base_algorithm import BaseWritingAlgorithm

class MinimumJerkAlgorithm(BaseWritingAlgorithm):
    """
    النموذج الكينماتيكي لليد (Minimum-Jerk Kinematic Model).
    يحاكي الانقباض العضلي لليد البشرية بحيث تكون السرعة بطيئة في البداية والنهاية (تسارع وتباطؤ ناعم)
    وأعلى سرعة في منتصف مسار الكلمة.
    """
    
    @property
    def style(self) -> str:
        return "minimum_jerk"
        
    def generate_times(self, seeds: list, is_rtl: bool) -> np.ndarray:
        if not seeds:
            return np.array([])
            
        N = len(seeds)
        if N == 1:
            return np.array([0.0])
            
        # المسافات المكانية الموزعة بانتظام على الهيكل العظمي للنص
        s_values = np.linspace(0.0, 1.0, N)
        
        # دالة Minimum Jerk الكينماتيكية: s(t) = 10*t^3 - 15*t^4 + 6*t^5
        # لحساب الزمن (t) بناءً على المسافة (s)، نستخدم الاستيفاء العكسي (Inverse Interpolation)
        t_samples = np.linspace(0.0, 1.0, 2000)
        s_samples = 10 * (t_samples**3) - 15 * (t_samples**4) + 6 * (t_samples**5)
        
        # استنتاج الزمن t لكل نقطة s
        times = np.interp(s_values, s_samples, t_samples)
        
        return times

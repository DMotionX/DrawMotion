import numpy as np
from ..base_algorithm import BaseWritingAlgorithm

class OrnsteinUhlenbeckNoiseAlgorithm(BaseWritingAlgorithm):
    """
    نموذج التشويش العشوائي (Ornstein-Uhlenbeck Noise Model).
    يضيف تشويشاً رياضياً دقيقاً (اهتزازات ميكروية في السرعة) وتفاوتات عشوائية لمحاكاة الكاتب المتردد 
    أو لإضافة طابع عفوي غير مثالي لعملية الكتابة.
    """
    
    @property
    def style(self) -> str:
        return "ou_noise"
        
    def generate_times(self, seeds: list, is_rtl: bool) -> np.ndarray:
        if not seeds:
            return np.array([])
            
        N = len(seeds)
        if N < 2:
            return np.linspace(0.0, 1.0, N)
            
        # محاكاة عملية أورنشتاين-أولينبيك (Ornstein-Uhlenbeck Process) للسرعة
        # المعادلة: v_t = v_{t-1} + theta * (mu - v_{t-1}) + sigma * dW
        
        mu = 1.0       # السرعة الأساسية المستهدفة (Mean)
        theta = 0.1    # قوة العودة للمتوسط (Reversion speed)
        sigma = 0.3    # قوة التشويش العشوائي (Volatility)
        
        v = np.ones(N)
        
        # تثبيت الـ Seed العشوائي لكي يكون الأنيميشن متطابقاً في كل مرة يتم تشغيله لنفس النص
        # (نستخدم طول البذور كـ seed بسيط)
        np.random.seed(N)
        
        for i in range(1, N):
            dW = np.random.normal(0, 1)
            dv = theta * (mu - v[i-1]) + sigma * dW
            v[i] = v[i-1] + dv
            
        # نمنع السرعة من أن تصبح سالبة أو صفرية (كي لا يعود القلم للخلف أو يتوقف تماماً)
        v = np.clip(v, 0.1, 3.0)
        
        # الزمن المستغرق يتناسب عكسياً مع السرعة
        dt = 1.0 / v
        
        # الزمن التراكمي
        times = np.cumsum(dt)
        
        # توحيد الزمن
        times = times - times[0]
        times = times / times[-1]
            
        return times

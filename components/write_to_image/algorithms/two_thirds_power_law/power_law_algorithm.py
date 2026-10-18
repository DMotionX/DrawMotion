import numpy as np
from ..base_algorithm import BaseWritingAlgorithm

class TwoThirdsPowerLawAlgorithm(BaseWritingAlgorithm):
    """
    نموذج قانون القوة الثلثين (2/3 Power Law Model).
    قانون فيزيائي يربط سرعة القلم بانحناء المسار. 
    الخوارزمية تبطئ القلم ديناميكياً عند المنحنيات الحادة والزوايا، وتسرعه في الخطوط المستقيمة.
    """
    
    @property
    def style(self) -> str:
        return "two_thirds_power_law"
        
    def generate_times(self, seeds: list, is_rtl: bool) -> np.ndarray:
        if not seeds:
            return np.array([])
            
        N = len(seeds)
        if N < 3:
            return np.linspace(0.0, 1.0, N)
            
        seeds_arr = np.array(seeds, dtype=float)
        
        # 1. تنعيم المسار لتقليل الضوضاء الناتجة عن البكسلات
        window = 5
        smoothed = np.copy(seeds_arr)
        for i in range(1, N-1):
            start = max(0, i - window//2)
            end = min(N, i + window//2 + 1)
            smoothed[i] = np.mean(seeds_arr[start:end], axis=0)
            
        # 2. حساب المشتقة الأولى (السرعة المكانية)
        dx = np.gradient(smoothed[:, 0])
        dy = np.gradient(smoothed[:, 1])
        
        # 3. حساب المشتقة الثانية (التسارع المكاني)
        ddx = np.gradient(dx)
        ddy = np.gradient(dy)
        
        # 4. حساب الانحناء (Curvature - Kappa)
        speed_sq = dx**2 + dy**2
        speed_sq[speed_sq < 1e-5] = 1e-5 # منع القسمة على الصفر
        
        kappa = np.abs(dx * ddy - dy * ddx) / (speed_sq**(1.5))
        
        # 5. تطبيق قانون الثلثين: السرعة تتناسب مع (kappa ^ -1/3)
        # نحدد حداً أدنى وأقصى للانحناء لمنع السرعات اللانهائية
        kappa_clamped = np.clip(kappa, 1e-3, 10.0)
        velocity = kappa_clamped ** (-1.0 / 3.0)
        
        # 6. الزمن المستغرق لكل خطوة (dt) يتناسب عكسياً مع السرعة
        dt = 1.0 / velocity
        
        # 7. حساب الزمن التراكمي
        times = np.cumsum(dt)
        
        # 8. توحيد الزمن ليكون بين 0.0 و 1.0
        times = times - times[0]
        if times[-1] > 0:
            times = times / times[-1]
        else:
            times = np.linspace(0.0, 1.0, N)
            
        return times

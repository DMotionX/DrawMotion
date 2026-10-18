import numpy as np
from ..base_algorithm import BaseWritingAlgorithm

class StopAndGoAlgorithm(BaseWritingAlgorithm):
    """
    نموذج التوقف المتقطع (Segmented Stop-and-Go Model).
    يقوم باكتشاف المسافات الفاصلة (بين الحروف أو الكلمات) ويطبق انقباضة عضلية مستقلة لكل حرف (تسارع ثم تباطؤ)،
    مع فرض وقفة قاطعة وواضحة جداً بين كل جزء والآخر لمحاكاة الكتابة المتأنية جداً.
    """
    
    @property
    def style(self) -> str:
        return "stop_and_go"
        
    def generate_times(self, seeds: list, is_rtl: bool) -> np.ndarray:
        if not seeds:
            return np.array([])
            
        N = len(seeds)
        if N < 3:
            return np.linspace(0.0, 1.0, N)
            
        seeds_arr = np.array(seeds, dtype=float)
        
        # 1. حساب المسافة بين كل نقطتين متتاليتين لاكتشاف القفزات (حرف جديد)
        dist = np.sqrt(np.sum((seeds_arr[1:] - seeds_arr[:-1])**2, axis=1))
        
        # نعتبر أي مسافة أكبر من 5 بكسل بمثابة قفزة لحرف أو مقطع جديد
        jump_indices = np.where(dist > 5.0)[0]
        
        # 2. تقسيم المسار إلى مقاطع (Segments)
        segments = []
        start_idx = 0
        for j_idx in jump_indices:
            segments.append((start_idx, j_idx + 1))
            start_idx = j_idx + 1
        segments.append((start_idx, N))
        
        # 3. معالجة كل مقطع على حدة
        times = np.zeros(N)
        current_time = 0.0
        
        for start, end in segments:
            seg_len = end - start
            if seg_len <= 1:
                times[start] = current_time
                current_time += 0.01  # وقت افتراضي للمقاطع القصيرة جداً
                continue
                
            # تطبيق منحنى جيبي (Sine Curve) للسرعة لكل مقطع: سرعة بطيئة في البداية والنهاية
            s_seg = np.linspace(0.05, 0.95, seg_len)
            v_seg = np.sin(np.pi * s_seg)
            
            dt_seg = 1.0 / v_seg
            t_seg = np.cumsum(dt_seg)
            
            # توحيد زمن المقطع
            t_seg = t_seg - t_seg[0]
            if t_seg[-1] > 0:
                t_seg = t_seg / t_seg[-1]
                
            # وزن الزمن المخصص للمقطع بناءً على طوله مقارنة بطول النص الكلي
            # (المقاطع الطويلة تأخذ وقتاً أطول)
            t_seg = t_seg * (float(seg_len) / float(N))
            
            times[start:end] = current_time + t_seg
            
            # إضافة وقفة قاطعة (Pause) في نهاية المقطع بنسبة 5% من الوقت الإجمالي
            current_time = times[end-1] + 0.05
            
        # 4. توحيد الزمن النهائي ليكون بين 0.0 و 1.0
        times = times - times[0]
        if times[-1] > 0:
            times = times / times[-1]
        else:
            times = np.linspace(0.0, 1.0, N)
            
        return times

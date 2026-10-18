import numpy as np
from abc import ABC, abstractmethod

class BaseWritingAlgorithm(ABC):
    """
    الأساس المعماري لكل خوارزميات الكتابة.
    يجب أن ترث كل خوارزمية هذا الصنف وتنفذ الدالة generate_times.
    """
    
    @property
    @abstractmethod
    def style(self) -> str:
        """يعيد اسم الخوارزمية (النمط)"""
        pass
        
    @abstractmethod
    def generate_times(self, seeds: list, is_rtl: bool) -> np.ndarray:
        """
        تقوم بتوليد مصفوفة زمنية (من 0.0 إلى 1.0) لكل بذرة في قائمة البذور.
        """
        pass

from PySide6.QtCore import QThreadPool, QObject
from .worker import TaskWorker

class AsyncEngine(QObject):
    """
    Central background task engine to prevent UI freezes.
    Manages a thread pool for executing heavy calculations.
    """
    _instance = None
    
    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool()
        # Limit to 2 threads to avoid overusing CPU for UI tasks
        self.thread_pool.setMaxThreadCount(2) 
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AsyncEngine()
        return cls._instance
        
    def run_task(self, func, on_result=None, on_error=None, on_finished=None, *args, **kwargs):
        """
        Runs a function in the background.
        Callbacks are executed on the main thread safely.
        """
        worker = TaskWorker(func, *args, **kwargs)
        if on_result:
            worker.signals.result.connect(on_result)
        if on_error:
            worker.signals.error.connect(on_error)
        if on_finished:
            worker.signals.finished.connect(on_finished)
            
        self.thread_pool.start(worker)

    def shutdown(self):
        """Waits for active background tasks to finish before shutdown."""
        try:
            if hasattr(self, 'thread_pool') and self.thread_pool:
                self.thread_pool.waitForDone(500)
        except Exception:
            pass

    def __del__(self):
        self.shutdown()

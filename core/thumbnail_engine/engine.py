import os
from PySide6.QtCore import QObject, QThread, Signal, Slot, QSize, Qt
from PySide6.QtGui import QImage, QPixmap, QIcon

class ThumbnailWorker(QObject):
    """
    Background worker that runs indefinitely in a separate thread.
    Processes image paths and emits them back as QIcons safely.
    """
    thumbnail_ready = Signal(str, object)
    
    @Slot(str)
    def process_request(self, path):
        if path.lower().endswith('.svg'):
            # SVG files are extremely lightweight and vector-based.
            # QImage fails to read them directly without QSvgRenderer.
            try:
                self.thumbnail_ready.emit(path, "SVG_FORMAT")
            except Exception:
                pass
            return
            
        from PySide6.QtGui import QImageReader
        reader = QImageReader(path)
        if reader.canRead():
            # Prevent Out-Of-Memory (OOM) for huge PNG/JPG files
            # Decode the image directly into a smaller buffer using the codec!
            orig_size = reader.size()
            if orig_size.width() > 600 or orig_size.height() > 600:
                reader.setScaledSize(orig_size.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio))
            
            img = reader.read()
            if not img.isNull():
                img = img.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                try:
                    self.thumbnail_ready.emit(path, img) # Emit QImage, which is thread-safe
                except Exception:
                    pass
                return
                
        try:
            self.thumbnail_ready.emit(path, None)
        except Exception:
            pass

class ThumbnailEngine(QObject):
    """
    Singleton engine to handle all thumbnail requests globally.
    Features caching and robust thread-safe background loading.
    """
    _instance = None
    
    # Internal signal to cross thread boundary safely
    _request_queued = Signal(str)
    
    def __init__(self):
        super().__init__()
        import collections
        self.cache = collections.OrderedDict()
        self.MAX_CACHE_SIZE = 100
        self.callbacks = {} # Maps path to list of waiting callbacks
        
        # Setup persistent background thread for maximum safety (No QRunnable deletion bugs)
        self.worker = ThumbnailWorker()
        self.thread = QThread()
        self.thread.setObjectName("ThumbnailEngineThread")
        self.worker.moveToThread(self.thread)
        
        # Connect signals for cross-thread communication
        self._request_queued.connect(self.worker.process_request)
        self.worker.thumbnail_ready.connect(self._on_thumbnail_ready)
        
        self.thread.start()

        # Ensure thread is cleanly terminated upon application quit
        from PySide6.QtCore import QCoreApplication
        app = QCoreApplication.instance()
        if app:
            app.aboutToQuit.connect(self.shutdown)
        import atexit
        atexit.register(self.shutdown)

        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ThumbnailEngine()
        return cls._instance
        
    def request_thumbnail(self, path: str, callback: callable):
        """
        Request a thumbnail for a file path. 
        If cached, returns immediately. Otherwise, queues for background processing.
        """
        if path in self.cache:
            # LRU Cache: Move to end to mark as recently used
            icon = self.cache.pop(path)
            self.cache[path] = icon
            callback(icon)
            return
            
        if path not in self.callbacks:
            self.callbacks[path] = []
            self._request_queued.emit(path) # Send to background thread
            
        self.callbacks[path].append(callback)
        
    @Slot(str, object)
    def _on_thumbnail_ready(self, path, img_or_flag):
        """
        Called on the MAIN THREAD when the worker finishes a thumbnail.
        """
        icon = None
        if img_or_flag == "SVG_FORMAT":
            # Safely render SVG using QSvgRenderer on the Main Thread
            try:
                from PySide6.QtSvg import QSvgRenderer
                from PySide6.QtCore import QByteArray
                from PySide6.QtGui import QPainter
                
                with open(path, 'r', encoding='utf-8') as f:
                    svg_str = f.read()
                
                renderer = QSvgRenderer(QByteArray(svg_str.encode('utf-8')))
                if renderer.isValid():
                    pixmap = QPixmap(200, 200)
                    pixmap.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(pixmap)
                    renderer.render(painter)
                    painter.end()
                    icon = QIcon(pixmap)
            except Exception as e:
                print(f"Failed to render SVG thumbnail for {path}: {e}")
        elif img_or_flag:
            icon = QIcon(QPixmap.fromImage(img_or_flag))
            
        if icon:
            self.cache[path] = icon
            # Auto-GC: Keep cache size under limit (LRU Eviction)
            if len(self.cache) > self.MAX_CACHE_SIZE:
                self.cache.popitem(last=False)
            
        if path in self.callbacks:
            # Execute all waiting callbacks safely
            for cb in self.callbacks.pop(path):
                try:
                    cb(icon)
                except Exception:
                    pass

    def shutdown(self):
        """Safely stops the background thumbnail worker thread to prevent QThread destruction errors."""
        try:
            if hasattr(self, 'thread') and self.thread and self.thread.isRunning():
                self.thread.quit()
                if not self.thread.wait(500):
                    self.thread.terminate()
                    self.thread.wait(200)
        except Exception:
            pass

    def __del__(self):
        self.shutdown()


import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}

class FeedbackFileHandler(FileSystemEventHandler):
    """Watches a folder for new image/PDF files and triggers the processing pipeline."""
    
    def __init__(self, process_callback):
        """
        Args:
            process_callback (callable): A function that takes (filepath) as argument
                and runs the full OCR + analysis pipeline on it.
        """
        super().__init__()
        self.process_callback = process_callback
        self._processed = set()
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        filepath = event.src_path
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext not in SUPPORTED_EXTENSIONS:
            return
        
        # Avoid duplicate triggers
        if filepath in self._processed:
            return
        self._processed.add(filepath)
        
        # Small delay to ensure file is fully written to disk
        time.sleep(1.0)
        
        try:
            self.process_callback(filepath)
        except Exception as e:
            print(f"[Watcher] Error processing {filepath}: {e}")


class FolderWatcher:
    """Manages the lifecycle of a watchdog Observer on a specific folder."""
    
    def __init__(self, folder_path, process_callback):
        self.folder_path = folder_path
        self.process_callback = process_callback
        self._observer = None
        self._thread = None
        self._running = False
    
    def start(self):
        """Starts the folder watcher in a background thread."""
        if self._running:
            return
        
        os.makedirs(self.folder_path, exist_ok=True)
        
        handler = FeedbackFileHandler(self.process_callback)
        self._observer = Observer()
        self._observer.schedule(handler, self.folder_path, recursive=False)
        self._observer.daemon = True
        self._observer.start()
        self._running = True
        print(f"[Watcher] Started watching: {self.folder_path}")
    
    def stop(self):
        """Stops the folder watcher."""
        if not self._running or not self._observer:
            return
        
        self._observer.stop()
        self._observer.join(timeout=5)
        self._running = False
        self._observer = None
        print(f"[Watcher] Stopped watching: {self.folder_path}")
    
    @property
    def is_running(self):
        return self._running

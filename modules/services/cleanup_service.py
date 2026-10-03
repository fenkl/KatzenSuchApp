"""Cleanup Service for KatzenSuchApp."""

import atexit
import os
import signal
from pathlib import Path
from modules.Mhandle_log import get_logger

log = get_logger(__name__)


class CleanupService:
    """Service for cleanup operations."""
    
    def __init__(self):
        self.cleanup_handlers = []
        self._register_handlers()
    
    def _register_handlers(self):
        """Register cleanup handlers."""
        atexit.register(self.cleanup_all)
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle signals."""
        log.info(f"Received signal {signum}")
        self.cleanup_all()
        exit(0)
    
    def cleanup_all(self):
        """Perform all cleanup operations."""
        log.info("Starting cleanup")
        
        # Cleanup temp files
        temp_dir = Path.home() / ".katzensuchapp_temp"
        if temp_dir.exists():
            import shutil
            try:
                shutil.rmtree(temp_dir)
                log.info(f"Cleaned temp directory {temp_dir}")
            except Exception as e:
                log.error(f"Error cleaning temp dir: {e}")
        
        # Cleanup playwright data if needed
        log.info("Cleanup complete")
    
    def cleanup_playwright(self):
        """Cleanup Playwright resources."""
        log.info("Cleaning up Playwright resources")
        # Playwright cleanup would go here
    
    def remove_pid_file(self, pid_file: str = None):
        """Remove PID file."""
        if pid_file and os.path.exists(pid_file):
            try:
                os.remove(pid_file)
                log.info(f"Removed PID file {pid_file}")
            except Exception as e:
                log.error(f"Error removing PID file: {e}")


# Singleton instance
cleanup_service = CleanupService()

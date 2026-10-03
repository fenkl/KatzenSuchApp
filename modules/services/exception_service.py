"""Exception Service for KatzenSuchApp."""

import sys
import traceback
from modules.Mhandle_log import get_logger

log = get_logger(__name__)


class ExceptionService:
    """Service for handling exceptions."""
    
    def __init__(self):
        self._setup_global_handlers()
    
    def _setup_global_handlers(self):
        """Setup global exception handlers."""
        sys.excepthook = self._global_exception_handler
        
        # Set up asyncio exception handler if available
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            loop.set_exception_handler(self._async_exception_handler)
        except Exception:
            pass
    
    def _global_exception_handler(self, exc_type, exc_value, exc_traceback):
        """Global exception handler."""
        log.error(f"Uncaught exception: {exc_type.__name__}: {exc_value}")
        log.error("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        
        self._send_alert(exc_type, exc_value, exc_traceback)
    
    def _async_exception_handler(self, loop, context):
        """Async exception handler."""
        log.error(f"Async exception: {context}")
        log.error(f"Message: {context.get('message', 'Unknown')}")
        if 'exception' in context:
            log.error(f"Exception: {context['exception']}")
    
    def _send_alert(self, exc_type, exc_value, exc_traceback):
        """Send alert for exception."""
        pass
    
    def handle_exception(self, e: Exception, context: str = ""):
        """Handle exception with context."""
        log.error(f"Exception in {context}: {e}")
        log.error(traceback.format_exc())


# Singleton instance
exception_service = ExceptionService()

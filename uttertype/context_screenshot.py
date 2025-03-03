"""
Active window screenshot capture for macOS.

This module provides functionality to capture a screenshot of the currently active
window on macOS systems. For other platforms, it will return None.

Dependencies (install with optional 'macos' extra):
- mss
- Pillow
"""

import sys
from typing import Optional

# Import conditionally to avoid errors on non-macOS systems
if sys.platform == 'darwin':
    try:
        from PIL import Image
    except ImportError:
        print("Pillow not installed. Install with: uv sync --extra macos")
else:
    # Define Image class for type hints on non-macOS
    class Image:
        class Image:
            pass

def capture_active_window() -> Optional[Image.Image]:
    """
    Capture a screenshot of the currently active window on macOS.
    
    Returns:
        PIL Image object if successful, None otherwise or on non-macOS platforms.
    """
    # Check if we're on macOS
    if sys.platform != 'darwin':
        return None

    try:
        # Try to import the required libraries
        try:
            from mss import mss
            # macOS-specific imports
            from AppKit import NSWorkspace
            from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
        except ImportError as e:
            print(f"Required dependency not available: {e}")
            print("Install macOS dependencies with: uv sync --extra macos")
            return None
        
        # Get active application
        active_app = NSWorkspace.sharedWorkspace().activeApplication()
        app_pid = active_app['NSApplicationProcessIdentifier']
        
        # Get information about the frontmost window
        window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)

        # Find the frontmost window that belongs to our active application
        target_window = None
        for window in window_list:
            if window.get('kCGWindowOwnerPID', 0) == app_pid:
                # This window belongs to our active application
                target_window = window
                break

        if target_window and 'kCGWindowBounds' in target_window:
            # Extract window bounds
            bounds = target_window['kCGWindowBounds']
            left = bounds['X']
            top = bounds['Y']
            width = bounds['Width']
            height = bounds['Height']

            # Create monitor dict for mss
            monitor = {"left": left, "top": top, "width": width, "height": height}
        else:
            # Could not find specific window, return None
            return None
            
        # Take the screenshot using mss
        with mss() as sct:
            screenshot = sct.grab(monitor)
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            return img
            
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None


if __name__ == "__main__":
    # Test the functionality
    if sys.platform == 'darwin':
        img = capture_active_window()
        if img:
            print(f"Screenshot captured: {img.width}x{img.height}")
            img.show()  # Display the image
        else:
            print("Failed to capture screenshot")
    else:
        print("This functionality is only available on macOS")
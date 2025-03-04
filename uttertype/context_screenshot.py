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
        raise
else:
    # Define Image class for type hints on non-macOS
    class Image:
        class Image:
            pass

def capture_active_window(max_dimension: int = 1200) -> Optional[Image.Image]:
    """
    Capture a screenshot of the currently active window on macOS.
    
    Args:
        max_dimension: Maximum width or height of the returned image, preserving aspect ratio.
                     Defaults to 1200 pixels.
    
    Returns:
        PIL Image object if successful, None otherwise or on non-macOS platforms.
        The image will be scaled down to fit within max_dimension while preserving aspect ratio.
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
            
            # Resize the image if it's larger than max_dimension
            width, height = img.size
            if width > max_dimension or height > max_dimension:
                # Calculate the scaling factor to preserve aspect ratio
                scale_factor = min(max_dimension / width, max_dimension / height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                img = img.resize((new_width, new_height), Image.LANCZOS)
                
            return img
            
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None


if __name__ == "__main__":
    # Test the functionality
    if sys.platform == 'darwin':
        img = capture_active_window(max_dimension=1600)  # Test with a smaller max dimension
        if img:
            print(f"Screenshot captured: {img.width}x{img.height}")
            img.show()  # Display the image
        else:
            print("Failed to capture screenshot")
    else:
        print("This functionality is only available on macOS")

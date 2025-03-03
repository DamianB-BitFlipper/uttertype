import os
import sys
from pynput.keyboard import HotKey


class UnifiedHotKey(HotKey):
    """
    A unified hotkey handler that works with both standard hotkeys and the macOS globe key.
    
    This class inherits from pynput's HotKey but adds hold functionality and
    special handling for the macOS globe key.
    """
    
    # Globe key virtual key code (macOS)
    GLOBE_KEY_VK = 63
    
    def __init__(
        self, 
        keys=None, 
        on_activate=lambda: None,
        on_deactivate=lambda: None,
        on_other_key=lambda: None,
        is_globe_key=False
    ):
        self.active = False
        self._is_globe_key = is_globe_key
        self._on_deactivate = on_deactivate
        self._on_other_key = on_other_key
        self._raw_on_activate = on_activate
        
        # Set up activation function
        def _mod_on_activate():
            self.active = True
            self._raw_on_activate()
            
        # For globe key, we don't use the standard hotkey keys
        # but we still inherit from HotKey for consistency
        if is_globe_key:
            # Initialize with empty key set
            super().__init__(set(), _mod_on_activate)
        else:
            super().__init__(keys, _mod_on_activate)
    
    def press(self, key):
        # Globe key special handling
        if self._is_globe_key:
            if hasattr(key, "vk") and key.vk == self.GLOBE_KEY_VK:
                if self.active:  # hold ended
                    self.active = False
                    self._on_deactivate()
                else:  # hold started
                    self.active = True
                    self._raw_on_activate()
                
            # Some other key was pressed while the globe key is held
            elif self.active and getattr(key, "vk", 0) != self.GLOBE_KEY_VK:
                self._on_other_key()
            return
            
        # Standard hotkey handling
        # Check if another key is being pressed during active hotkey
        if self.active and key not in self._keys:
            self._on_other_key()
            
        # Continue with normal processing
        super().press(key)
        
    def release(self, key):
        # Globe key special handling (press and release are mixed)
        if self._is_globe_key:
            if hasattr(key, "vk") and key.vk == self.GLOBE_KEY_VK:
                self.press(key)
            return
            
        # Standard hotkey handling
        super().release(key)
        
        # The `self._state != self._keys` happens when at least
        # one of the hot-keys is no longer pressed
        if self.active and self._state != self._keys:
            self.active = False
            self._on_deactivate()


def create_keylistener(transcriber):
    key_code = os.getenv(
        "UTTERTYPE_RECORD_HOTKEYS",
        "<globe>" if sys.platform == "darwin" else "<ctrl>+<alt>+v"
    )

    # The globe key needs special hot-key handling
    if key_code == "<globe>":
        return UnifiedHotKey(
            on_activate=transcriber.start_recording,
            on_deactivate=transcriber.stop_recording,
            on_other_key=transcriber.cancel_recording,
            is_globe_key=True
        )

    return UnifiedHotKey(
        UnifiedHotKey.parse(key_code),
        on_activate=transcriber.start_recording,
        on_deactivate=transcriber.stop_recording,
        on_other_key=transcriber.cancel_recording
    )

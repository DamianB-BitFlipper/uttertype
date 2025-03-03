import os
import sys
from pynput.keyboard import HotKey


class UnifiedHotKey(HotKey):
    """
    A unified hotkey handler that works with both standard hotkeys and the macOS globe key.
    
    This class inherits from pynput's HotKey but adds hold functionality and
    special handling for the macOS globe key. The globe key only gets the release
    trigger and not the press trigger.
    """
    
    # Globe key virtual key code (macOS)
    GLOBE_KEY_VK = 63
    
    def __init__(
        self, 
        keys,
        on_activate=lambda: None,
        on_deactivate=lambda: None,
        on_other_key=lambda: None,
    ):
        self._on_activate = on_activate
        self._on_deactivate = on_deactivate
        self._on_other_key = on_other_key

        self._globe_key_pressed = False

        super().__init__(keys, self._on_activate)

    @property
    def active(self):
        # The hot key is active when all of the `_keys` are pressed (represented by `_state`)
        return self._state == self._keys

    def press(self, key):
        # If the hot-key is active, but another key was pressed
        if self.active and key not in self._keys:
            self._on_other_key()
            
        # Continue with normal processing
        super().press(key)
        
    def release(self, key):
        # Globe key special handling since it only gets the release trigger
        if getattr(key, "vk", 0) == self.GLOBE_KEY_VK:
            # It is not pressed yet, so send the `press signal` and exit
            if not self._globe_key_pressed:
                self._globe_key_pressed = True
                self.press(key)
                return
            else:
                self._globe_key_pressed = False

        # Standard hotkey handling
        super().release(key)
        
        # Because of the release, the hot-key may become no longer active
        if not self.active:
            self._on_deactivate()


def create_keylistener(transcriber):
    key_code = os.getenv(
        "UTTERTYPE_RECORD_HOTKEYS",
        "<globe>" if sys.platform == "darwin" else "<ctrl>+<alt>+v"
    )

    # Convert the globe key to its virtual key code
    if '<globe>' in key_code:
        key_code = key_code.replace('<globe>', '<63>')

    return UnifiedHotKey(
        UnifiedHotKey.parse(key_code),
        on_activate=transcriber.start_recording,
        on_deactivate=transcriber.stop_recording,
        on_other_key=transcriber.cancel_recording
    )

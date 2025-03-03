import os
import sys
from pynput.keyboard import HotKey


class HoldHotKey(HotKey):
    def __init__(self, keys, on_activate, on_deactivate, on_other_key):
        self.active = False
        self.transcriber = None  # Will be set in create_keylistener

        def _mod_on_activate():
            self.active = True
            on_activate()

        def _mod_on_deactivate():
            self.active = False
            on_deactivate()

        super().__init__(keys, _mod_on_activate)
        self._on_deactivate = _mod_on_deactivate
        self._on_other_key = on_other_key

    def press(self, key):
        # Check if the hotkey is active and another key is being pressed
        if self.active:
            # Convert keys to a set for easier comparison
            hotkey_keys_set = set(self._keys)
            # Check if the pressed key is not part of the hotkey
            if hasattr(key, 'vk') and key not in hotkey_keys_set:
                # Another key was pressed during recording, cancel it
                self._on_other_key()
        
        # Continue with normal processing
        super().press(key)

    def release(self, key):
        super().release(key)
        if self.active and self._state != self._keys:
            self._on_deactivate()


class HoldGlobeKey:
    """
    For macOS only, globe key requires special handling
    """

    def __init__(self, on_activate, on_deactivate, on_other_key):
        self.held = False
        self._on_activate = on_activate
        self._on_deactivate = on_deactivate
        self._on_other_key = on_other_key
        self.last_key_vk = None  # Track the last pressed key's vk code

    def press(self, key):
        if hasattr(key, "vk"):
            if key.vk == 63:  # Globe key
                if self.held:  # hold ended
                    self._on_deactivate()
                else:  # hold started
                    self._on_activate()
                self.held = not self.held
                self.last_key_vk = key.vk
            elif self.held and key.vk != 63 and key.vk != self.last_key_vk:
                # A different key was pressed while globe key is held
                # Cancel the recording
                self._on_other_key()

    def release(self, key):
        """Press and release signals are mixed for globe key"""
        # For globe key, handle via press
        if hasattr(key, "vk") and key.vk == 63:
            self.press(key)


def create_keylistener(transcriber, env_var="UTTERTYPE_RECORD_HOTKEYS"):
    key_code = os.getenv(env_var, "")

    if (sys.platform == "darwin") and (key_code in ["<globe>", ""]):
        return HoldGlobeKey(
            on_activate=transcriber.start_recording,
            on_deactivate=transcriber.stop_recording,
            on_other_key=transcriber.cancel_recording,
        )

    key_code = key_code if key_code else "<ctrl>+<alt>+v"

    hotkey = HoldHotKey(
          HoldHotKey.parse(key_code),
          on_activate=transcriber.start_recording,
          on_deactivate=transcriber.stop_recording,
          on_other_key=transcriber.cancel_recording,
      )
      
    return hotkey

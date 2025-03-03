import os
import sys
from pynput.keyboard import HotKey


class HoldHotKey(HotKey):
    def __init__(self, keys, on_activate, on_deactivate, on_other_key):
        self.active = False

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
        if self.active and key not in self._keys:
            # Another key was pressed during recording, cancel it
            self._on_other_key()
        
        # Continue with normal processing
        super().press(key)

    def release(self, key):
        super().release(key)
        # The `self._state != self._keys` happens when at least
        # one of the hot-keys is no longer pressed
        if self.active and self._state != self._keys:
            self._on_deactivate()


class HoldGlobeKey:
    """
    For macOS only, globe key requires special handling.

    Specifically, it only triggers the `release` event.
    """

    def __init__(self, on_activate, on_deactivate, on_other_key):
        self.held = False
        self._on_activate = on_activate
        self._on_deactivate = on_deactivate
        self._on_other_key = on_other_key

    def press(self, key):
        if hasattr(key, "vk"):
            if key.vk == 63:  # Globe key
                if self.held:  # hold ended
                    self._on_deactivate()
                else:  # hold started
                    self._on_activate()
                self.held = not self.held

        # Some other key was pressed while the globe key is held
        if self.held and getattr(key, "vk", 0) != 63:
            self._on_other_key()

    def release(self, key):
        """Press and release signals are mixed for globe key"""
        # For globe key, handle via press
        if hasattr(key, "vk") and key.vk == 63:
            self.press(key)


def create_keylistener(transcriber):
    key_code = os.getenv(
        "UTTERTYPE_RECORD_HOTKEYS",
        "<globe>" if sys.platform == "darwin" else "<ctrl>+<alt>+v"
    )

    # The globe key needs special hot-key handling
    if key_code == "<globe>":
        return HoldGlobeKey(
            on_activate=transcriber.start_recording,
            on_deactivate=transcriber.stop_recording,
            on_other_key=transcriber.cancel_recording,
        )

    return HoldHotKey(
          HoldHotKey.parse(key_code),
          on_activate=transcriber.start_recording,
          on_deactivate=transcriber.stop_recording,
          on_other_key=transcriber.cancel_recording,
      )

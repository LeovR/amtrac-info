from base64 import b64encode

from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from ableton.v2.control_surface import midi

MANUFACTURER_ID = (int("0x7d", 0),)
MESSAGE_START = (midi.SYSEX_START,) + MANUFACTURER_ID + (1, 1)


class SongInfoClipSlot(ControlSurfaceComponent):
    __module__ = __name__
    __doc__ = " ClipSlot "

    def __init__(self, parent, slot):
        ControlSurfaceComponent.__init__(self)
        self._parent = parent
        self._slot = slot
        self._parent.log_message('ClipSlot')
        # self._slot.add_playing_status_listener(self.playing_status_changed)
        self._slot.clip.add_playing_status_listener(self.playing_status_changed)
        self._slot.add_is_triggered_listener(self.on_is_triggered_changed)

    def playing_status_changed(self):
        if self._slot.is_playing:
            clip_name = self._slot.clip.name
            if clip_name[0] == '{':
                message_text = clip_name
            else:
                message_text = '{C} ' + clip_name
            self.send_message(message_text)
            self._parent.log_message(self._slot.clip.name.encode('ascii', 'replace') + ': is playing')

    def send_message(self, message_text):
        sysex_message = self.make_message(message_text)
        self._parent.log_message(str(sysex_message))
        self._parent._send_midi(sysex_message)

    def on_is_triggered_changed(self):
        if self._slot.is_triggered:
            clip_name = self._slot.clip.name
            if clip_name[0] != '{':
                self.send_message('{N} ' + clip_name)
            self._parent.log_message(self._slot.clip.name.encode('ascii', 'replace') + ' is triggered')

    @staticmethod
    def make_message(text):
        # arr = map(ord, text.encode('ascii', 'ignore'))
        arr = map(ord, b64encode(text.encode('utf-8')))
        return MESSAGE_START + tuple(arr) + (midi.SYSEX_END,)

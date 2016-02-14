from _Framework.ControlSurfaceComponent import ControlSurfaceComponent

from SongInfoClipSlot import SongInfoClipSlot

class SongInfoTrack(ControlSurfaceComponent):
    __module__ = __name__
    __doc__ = " Track "

    def __init__(self, parent, track):
        ControlSurfaceComponent.__init__(self)
        self._parent = parent
        self._track = track
        self.init_clip_slots()
        # self._track.add_playing_slot_index_listener(self.play_slot_index_changed)

    def play_slot_index_changed(self):
        clip = self.get_clip(self._track.playing_slot_index)
        if clip:
            self._parent.log_message('clip ' + clip.name)
            self._parent._send_midi((NOTE_ON_STATUS, SELECT_BEATS_NOTE, BUTTON_STATE_ON))
            self._parent._send_midi((NOTE_ON_STATUS, SELECT_SMPTE_NOTE, BUTTON_STATE_OFF))

    def get_clip(self, slot_index):
        clip = None
        if self._track and slot_index >= 0:
            slot = self._track.clip_slots[slot_index]
            if slot.has_clip and not slot.clip.is_recording and not slot.clip.is_triggered:
                clip = slot.clip
        return clip

    def init_clip_slots(self):
        for slot in self._track.clip_slots:
            if slot.has_clip:
                SongInfoClipSlot(self._parent, slot)

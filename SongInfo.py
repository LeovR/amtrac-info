"""
# SongInfo
"""

from __future__ import with_statement

from _Framework.ButtonElement import ButtonElement
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import *
from _Framework.TransportComponent import TransportComponent

from SongInfoTrack import SongInfoTrack

CHANNEL = 0


class SongInfo(ControlSurface):
    __module__ = __name__
    __doc__ = " SongInfo "

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        with self.component_guard():
            self._current_tracks = []
            self.setup_tracks()
            self.setup_transport_control()

    def disconnect(self):
        self._current_tracks = []
        ControlSurface.disconnect(self)

    def setup_tracks(self):
        for t in self.song().tracks:
            if self._current_tracks and t in self._current_tracks:
                self.register_track(t)
            else:
                t.add_name_listener(self.setup_tracks)
                self._current_tracks.append(t)
                self.register_track(t)

    def register_track(self, t):
        if t.name and t.name[0] == '{' and '}' in t.name:
            self.log_message('Track' + t.name)
            SongInfoTrack(self, t)

    def setup_transport_control(self):
        is_momentary = True
        transport = TransportComponent()
        transport.set_play_button(ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL, 0))
        transport.set_stop_button(ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL, 1))

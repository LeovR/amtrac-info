"""
# SongInfo
"""

from __future__ import with_statement

from base64 import b64encode

import Live
from _Framework.ButtonElement import ButtonElement
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import *
from _Framework.TransportComponent import TransportComponent
from ableton.v2.control_surface import midi

from SongInfoTrack import SongInfoTrack

MANUFACTURER_ID = (int("0x7d", 0),)
MESSAGE_START = (midi.SYSEX_START,) + MANUFACTURER_ID + (1, 1)

CHANNEL = 0
NOTE_OFF_STATUS = 128
NOTE_ON_STATUS = 144

SCENE_OFFSET = 10
SCENE_NOTES = range(SCENE_OFFSET, 50)

STOP_MIDI_NOTE = 0


class SongInfo(ControlSurface):
    __module__ = __name__
    __doc__ = " SongInfo "

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        with self.component_guard():
            self._current_tracks = []
            self._scenes = dict()
            self._c_instance = c_instance
            self.setup_scenes()
            self.setup_tracks()
            self.setup_transport_control()
            self.send_song_configuration()

    def disconnect(self):
        self._current_tracks = []
        self._scenes = dict()
        ControlSurface.disconnect(self)

    @staticmethod
    def find_between(s, first, last):
        try:
            start = s.index(first) + len(first)
            end = s.index(last, start)
            return s[start:end]
        except ValueError:
            return ""

    @staticmethod
    def get_scene_index(scene):
        number = SongInfo.find_between(scene.name, '{', '}')
        return number

    def setup_scenes(self):
        scenes = self.song().scenes
        for scene in scenes:
            if scene.name and scene.name[0] == '{' and '}' in scene.name:
                self.log_message('Found scene ' + scene.name)
                index = int(SongInfo.get_scene_index(scene))
                self._scenes[index] = scene
        for i, s in sorted(self._scenes.items()):
            self.log_message('Scene ' + str(i) + ' ' + s.name)

    def setup_tracks(self):
        for t in self.song().tracks:
            if self._current_tracks and t in self._current_tracks:
                self.register_track(t)
            else:
                t.add_name_listener(self.setup_tracks)
                self._current_tracks.append(t)
                self.register_track(t)

    def build_midi_map(self, midi_map_handle):
        ControlSurface.build_midi_map(self, midi_map_handle)
        script_handle = self._c_instance.handle()
        for midi_no in SCENE_NOTES:
            Live.MidiMap.forward_midi_note(script_handle, midi_map_handle, 0, midi_no)

    def receive_midi(self, midi_bytes):
        if midi_bytes[0] & 240 == NOTE_ON_STATUS:
            note = midi_bytes[1]
            if note >= SCENE_OFFSET:
                note_without_offset = note - SCENE_OFFSET
                if note_without_offset in self._scenes:
                    self._scenes[note_without_offset].fire()
            else:
                ControlSurface.receive_midi(self, midi_bytes)
        else:
            ControlSurface.receive_midi(self, midi_bytes)

    def register_track(self, t):
        if t.name and t.name[0] == '{' and '}' in t.name:
            self.log_message('Track ' + t.name)
            SongInfoTrack(self, t)

    def setup_transport_control(self):
        is_momentary = True
        self._transport = TransportComponent()
        self._transport.set_stop_button(ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL, STOP_MIDI_NOTE))

    def send_song_configuration(self):
        if not self._scenes:
            return
        for i, s in sorted(self._scenes.items()):
            message_text = '{C}{' + str(i) + '}{' + s.name.split('} ', 1)[1] + '}'
            self.log_message(message_text)
            self.send_message(message_text)

    @staticmethod
    def make_message(text):
        arr = map(ord, b64encode(text.encode('utf-8')))
        return MESSAGE_START + tuple(arr) + (midi.SYSEX_END,)

    def send_message(self, message_text):
        sysex_message = self.make_message(message_text)
        self.log_message(str(sysex_message))
        self._send_midi(sysex_message)

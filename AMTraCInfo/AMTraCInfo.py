"""
# AMTraCInfo
"""

from __future__ import with_statement

from base64 import b64encode

import Live
from _Framework.ButtonElement import ButtonElement
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import *
from _Framework.TransportComponent import TransportComponent
from ableton.v2.control_surface import midi

from AMTraCInfoScene import AMTraCInfoScene
from AMTraCInfoSceneSignaturePublisher import AMTraCInfoSceneSignaturePublisher

MANUFACTURER_ID = (int("0x7d", 0),)
MESSAGE_START = (midi.SYSEX_START,) + MANUFACTURER_ID + (1, 1)

CHANNEL = 0
NOTE_OFF_STATUS = 128
NOTE_ON_STATUS = 144

SCENE_OFFSET = 10
SCENE_MAX_NOTES = 30
SCENE_NOTES = range(SCENE_OFFSET, SCENE_OFFSET + SCENE_MAX_NOTES)

CONTROL_OFFSET = SCENE_MAX_NOTES + SCENE_OFFSET + 1
CONTROL_MAX_NOTES = 10
CONTROL_NOTES = range(CONTROL_OFFSET, CONTROL_OFFSET + CONTROL_MAX_NOTES)
CONTROL_REPEAT = 0
CONTROL_START = 1
CONTROL_CLIPS_STOP = 2

NOTES = SCENE_NOTES + CONTROL_NOTES

REPEAT_MIDI_NOTE = CONTROL_OFFSET

STOP_MIDI_NOTE = 0


class AMTraCInfo(ControlSurface):
    __module__ = __name__
    __doc__ = " AMTraC-Info "

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        with self.component_guard():
            self._repeat_tracks = []
            self._scenes = dict()
            self._c_instance = c_instance
            self.setup_scenes()
            self.setup_tracks()
            self.setup_transport_control()
            self.send_complete_song_configuration()
            self._transport = None

    def disconnect(self):
        self._scenes = dict()
        ControlSurface.disconnect(self)

    def send_complete_song_configuration(self):
        self.send_configuration_start()
        self.send_song_configuration()
        self.send_configuration_finished()

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
        number = AMTraCInfo.find_between(scene.name, '{', '}')
        return number

    def setup_scenes(self):
        scenes = self.song().scenes
        for scene in scenes:
            AMTraCInfoSceneSignaturePublisher(self, scene)
            if scene.name and scene.name[0] == '{' and '}' in scene.name:
                self.log_message('Found scene ' + scene.name)
                index = int(AMTraCInfo.get_scene_index(scene))
                self._scenes[index - 1] = scene
            else:
                AMTraCInfoScene(self, scene)
        for i, s in sorted(self._scenes.items()):
            self.log_message('Scene ' + str(i) + ' ' + s.name)

    def setup_tracks(self):
        for t in self.song().tracks:
            self.register_track(t)

    def build_midi_map(self, midi_map_handle):
        ControlSurface.build_midi_map(self, midi_map_handle)
        script_handle = self._c_instance.handle()
        for midi_no in NOTES:
            Live.MidiMap.forward_midi_note(script_handle, midi_map_handle, 0, midi_no)

    def toggle_repeat(self):
        for t in self._repeat_tracks:
            t.mute = not t.mute

    def receive_midi(self, midi_bytes):
        if midi_bytes[0] & 240 == NOTE_ON_STATUS:
            note = midi_bytes[1]
            self.log_message(note)
            if note in CONTROL_NOTES:
                note_without_offset = note - CONTROL_OFFSET
                if note_without_offset == CONTROL_REPEAT:
                    self.toggle_repeat()
                elif note_without_offset == CONTROL_START:
                    self.send_complete_song_configuration()
                elif note_without_offset == CONTROL_CLIPS_STOP:
                    self.stop_clips()
            elif note in SCENE_NOTES:
                note_without_offset = note - SCENE_OFFSET
                if note_without_offset in self._scenes:
                    self.start_scene(note_without_offset)
            else:
                ControlSurface.receive_midi(self, midi_bytes)
        else:
            ControlSurface.receive_midi(self, midi_bytes)

    def start_scene(self, note_without_offset):
        self._scenes[note_without_offset].fire()
        self.song().metronome = True

    def stop_clips(self):
        self.song().stop_all_clips()

    def register_track(self, t):
        if t.name and '{R}' in t.name:
            self.log_message('Repeat-Track ' + t.name)
            self._repeat_tracks.append(t)

    def setup_transport_control(self):
        is_momentary = True
        self._transport = TransportComponent()
        self._transport.set_stop_button(ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL, STOP_MIDI_NOTE))

    def send_song_configuration(self):
        if not self._scenes:
            return
        for i, s in sorted(self._scenes.items()):
            message_text = '{SC||' + str(i) + '|' + (s.name.split('} ', 1)[1]).split(' ||')[0][:16]
            self.send_message(message_text)

    def send_configuration_start(self):
        message_text = '{CS|'
        self.send_message(message_text)

    def send_configuration_finished(self):
        message_text = '{CF|'
        self.send_message(message_text)

    @staticmethod
    def make_message(text):
        arr = map(ord, b64encode(text.encode('utf-8')))
        return MESSAGE_START + tuple(arr) + (midi.SYSEX_END,)

    def send_message(self, message_text):
        self.log_message(message_text)
        sysex_message = self.make_message(message_text)
        self.log_message(str(sysex_message))
        self._send_midi(sysex_message)

from _Framework.ControlSurfaceComponent import ControlSurfaceComponent


class AMTraCInfoSceneSignaturePublisher(ControlSurfaceComponent):
    __module__ = __name__
    __doc__ = " AMTraC-Info SceneSignaturePublisher "

    def __init__(self, parent, scene):
        ControlSurfaceComponent.__init__(self)
        self._parent = parent
        self._scene = scene
        scene.add_is_triggered_listener(self.is_triggered_fired)

    def is_triggered_fired(self):
        if not self._scene.is_triggered:
            numerator = self.song().signature_numerator
            denominator = self.song().signature_denominator
            self._parent.log_message(self._scene.name + " is playing with " + str(numerator) + "/" + str(denominator))
            self._parent.send_message('{SS|' + str(numerator) + '|' + str(denominator))

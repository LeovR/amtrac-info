from _Framework.ControlSurfaceComponent import ControlSurfaceComponent


class AMTraCInfoScene(ControlSurfaceComponent):
    __module__ = __name__
    __doc__ = " AMTraC-Info Scene "

    def __init__(self, parent, scene):
        ControlSurfaceComponent.__init__(self)
        self._parent = parent
        self._scene = scene
        scene.add_is_triggered_listener(self.is_triggered_fired)

    def is_triggered_fired(self):
        if self._scene.is_triggered:
            self._parent.log_message(self._scene.name + " is triggered")
            self._parent.send_message('{NP|' + self._scene.name.split(' ||')[0][:16])
        else:
            self._parent.log_message(self._scene.name + " is playing")
            self._parent.send_message('{CP|' + self._scene.name.split(' ||')[0][:16])

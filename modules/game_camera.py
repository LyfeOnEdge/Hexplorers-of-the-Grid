import ursina

class EditorCamera(ursina.EditorCamera):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	def input(self, key):
		if ursina.mouse.hovered_entity:
			if ursina.mouse.hovered_entity.has_ancestor(ursina.camera.ui):
				return #Don't do anything if hovered over a ui element
		else:
			return super().input(key)
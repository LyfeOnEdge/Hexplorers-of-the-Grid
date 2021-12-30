import math, json, random
import ursina

from modules.map_gen import MapMaker
from modules.settings import settings

class App(ursina.Ursina):
	def __init__(self, *args, **kwargs):
		ursina.Ursina.__init__(self, *args, **kwargs)
		self.origin = ursina.Entity(model='sphere', color=ursina.color.rgb(0,0,0), scale=0.000001, origin = (0,0), x=0,y=0,z=0)
		self.editor_camera = ursina.EditorCamera(enabled=False, ignore_paused=True)
		self.editor_camera.enabled = True

		self.radius_slider = ursina.Slider(0, 70, default=settings.default_radius, step=1, text='Radius', parent=ursina.camera.ui, eternal = True, position = (-0.75,0.45))
		self.radius_slider.on_value_changed = self.set_radius_multiplier

		self.scale_slider = ursina.Slider(0.1, 25, default=settings.default_scale, step=0.1, text='Scale', parent=ursina.camera.ui, eternal = True, position = (-0.75,0.375))
		self.scale_slider.on_value_changed = self.set_scale_multiplier

		self.terrain_amp_slider = ursina.Slider(0, 10, default=settings.default_terrain_amp, step=0.1, text='Ter. Amp.', parent=ursina.camera.ui, eternal = True, position = (-0.75,0.30))
		self.terrain_amp_slider.on_value_changed = self.set_terrain_multiplier

		self.terrain_scale_slider = ursina.Slider(0.1, 20, default=settings.default_terrain_scale, step=0.1, text='Ter. Scale', parent=ursina.camera.ui, eternal = True, position = (-0.75,0.225))
		self.terrain_scale_slider.on_value_changed = self.set_terrain_scale

		self.button = ursina.Button(parent=ursina.camera.ui, eternal = True, position = (-0.75,0.150), on_click = self.generate_map, scale=0.1)
		self.combine_button = ursina.Button(parent=ursina.camera.ui, eternal = True, position = (-0.75,0.150), on_click = self.combine_map, scale=0.1)
		self.map_entities = []

		self.scale = 1
		self.radius = 3
		self.terrain_amplification = 1
		self.terrain_scale=1
		self.map = MapMaker((0,0), settings.default_scale, settings.default_radius, settings.default_terrain_amp, settings.default_terrain_scale)
		self.generate_map()

	def set_radius_multiplier(self):
		self.map.map_radius = self.radius_slider.value

	def set_scale_multiplier(self):
		self.map.map_scale = self.scale_slider.value

	def set_terrain_multiplier(self):
		self.map.terrain_amplification = self.terrain_amp_slider.value

	def set_terrain_scale(self):
		self.map.terrain_scale = self.terrain_scale_slider.value

	def generate_map(self):
		self.map.generate_map()

	def combine_map(self):
		self.map.combine()



app = App()
ursina.camera.mode = "orthoganol"
app.run()

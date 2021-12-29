import math, json, random
import ursina

from modules.map_gen import generate_map

# class HexGrid(ursina.Entity):
# 	def __init__(self, *args, **kwargs)
# 		ursina.Entity.__init__(self, *args, **kwargs)



class App(ursina.Ursina):
	def __init__(self, *args, **kwargs):
		ursina.Ursina.__init__(self, *args, **kwargs)
		self.origin = ursina.Entity(model='sphere', color=ursina.color.rgb(0,0,0), scale=0.000001, origin = (0,0), x=0,y=0,z=0)
		self.editor_camera = ursina.EditorCamera(enabled=False, ignore_paused=True)
		self.editor_camera.enabled = True

		self.radius_slider = ursina.Slider(0, 25, default=3, step=1, text='Radius', parent=ursina.camera.ui, eternal = True, position = (-0.75,0.45))
		self.radius_slider.on_value_changed = self.set_radius_multiplier

		self.scale_slider = ursina.Slider(0.1, 25, default=1, step=0.1, text='Scale', parent=ursina.camera.ui, eternal = True, position = (-0.75,0.375))
		self.scale_slider.on_value_changed = self.set_scale_multiplier

		self.terrain_amp_slider = ursina.Slider(0, 10, default=1, step=0.1, text='Ter. Amp.', parent=ursina.camera.ui, eternal = True, position = (-0.75,0.30))
		self.terrain_amp_slider.on_value_changed = self.set_terrain_multiplier

		self.terrain_scale_slider = ursina.Slider(0.1, 20, default=1, step=0.1, text='Ter. Scale', parent=ursina.camera.ui, eternal = True, position = (-0.75,0.225))
		self.terrain_scale_slider.on_value_changed = self.set_terrain_scale

		self.button = ursina.Button(parent=ursina.camera.ui, eternal = True, position = (-0.75,0.150), on_click = self.generate_map, scale=0.1)
		self.map_entities = []

		self.scale = 1
		self.radius = 3
		self.terrain_amp = 1
		self.terrain_scale=1
		self.generate_map()

	def set_radius_multiplier(self):
		self.radius = self.radius_slider.value

	def set_scale_multiplier(self):
		self.scale = self.scale_slider.value

	def set_terrain_multiplier(self):
		self.terrain_amp = self.terrain_amp_slider.value

	def set_terrain_scale(self):
		self.terrain_scale = self.terrain_scale_slider.value

	def generate_map(self,scale=None,radius=None,amplification=None,terrain_scale=None):
		radius = radius or self.radius
		scale = scale or self.scale
		amplification = amplification or self.terrain_amp
		terrain_scale = terrain_scale or self.terrain_scale
		self.radius = radius
		self.scale = scale
		self.terrain_amp = amplification
		self.terrain_scale = terrain_scale
		if self.map_entities:
			self.map_entities = []
			try:
				ursina.scene.clear()
			except Exception as e:
				print(e)
		self.map_entities = generate_map((0, 0), self.radius, self.scale, self.terrain_amp, self.terrain_scale)

























app = App()
ursina.camera.mode = "orthoganol"
app.run()

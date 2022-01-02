import math, json, random
import ursina

from modules.map_gen import MapMaker
from modules.catanengine import Game, Player
from modules.settings import settings
from modules.UrsinaLighting import LitInit

class App(ursina.Ursina):
	def __init__(self, *args, **kwargs):
		ursina.Ursina.__init__(self, *args, **kwargs)

		self.game = Game()
		self.map = MapMaker(self.game, (0,0), settings.default_radius)
		self.map.generate_map()

		self.origin = ursina.Entity(model='sphere', color=ursina.color.rgb(0,0,0), scale=0.000001, origin = (0,0), x=0,y=0,z=0)
		self.editor_camera = ursina.EditorCamera(enabled=False, ignore_paused=True)
		self.editor_camera.enabled = True

		self.radius_slider = ursina.Slider(0, 70, default=settings.default_radius, step=1, text='Radius', parent=ursina.camera.ui, eternal = True, position = (-0.75,0.45))
		self.radius_slider.on_value_changed = self.set_radius_multiplier

		self.toggle_water_button = ursina.Button(parent=ursina.camera.ui, eternal = True, position = (-0.85,0.075), on_click = self.map.toggle_water, scale=0.035)
		self.toggle_grid_button = ursina.Button(parent=ursina.camera.ui, eternal = True, position = (-0.85,0.00), on_click = self.map.toggle_grid, scale=0.035)
		self.toggle_skybox_button = ursina.Button(parent=ursina.camera.ui, eternal = True, position = (-0.85,-0.075), on_click = self.map.toggle_skybox, scale=0.035)
		# blue, green = Player(), Player()
		# self.game.start([blue, green])
		green = Player()
		self.game.start([green])

	def set_radius_multiplier(self):
		self.map.map_radius = self.radius_slider.value

app = App()
ursina.camera.mode = "orthoganol"

def update():
	app.game.gameloop()

app.run()


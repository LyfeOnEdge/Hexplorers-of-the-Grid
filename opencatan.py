import math, json, random
import ursina
from opensimplex import OpenSimplex

NOISE_DAMPENING = 1
random.seed(random.random())
generator = OpenSimplex(seed=3*int(random.uniform(0,50))).noise2
generator_2 = OpenSimplex(seed=17*int(random.uniform(0,50))).noise2
generator_3 = OpenSimplex(seed=27*int(random.uniform(0,50))).noise2

def get_heightmap(x,z):
	return (generator(x/5, z/5) + generator_2(x/9, z/9))/(2 * NOISE_DAMPENING) + 1.1 * generator_3(x/10, x/10 + z/25)

def get_random_color():
	return ursina.color.rgb(random.randint(0,255),random.randint(0,255),random.randint(0,255))

sqrt3 = math.sqrt(3)
def _calc_hexagon_verts(x_offset, z_offset, x,z,r,y=0, terrain_amplification = 1,terrain_scale=1):
	x*=r #Scale
	z*=r
	hr = r*0.5
	sqrt3hr = sqrt3*hr
	verts = [(v[0]+x_offset,y+get_heightmap(v[0]/terrain_scale,v[1]/terrain_scale)*terrain_amplification,v[1]+z_offset) for v in[
		(x, r + z),
		(sqrt3hr + x, hr + z),
		(sqrt3hr + x, -hr + z),
		(x, -r + z),
		(-sqrt3hr + x, -hr + z),
		(-sqrt3hr + x, hr + z)
	]]
	return verts

def calc_hexagon_verts_from_center_point(*args, **kwargs):
	return (_calc_hexagon_verts(*args,**kwargs), ((0,5,4),(0,4,3),(0,3,2),(0,2,1),(0,1,0)))

def calc_hexagon_outline_verts_from_center_point(*args, **kwargs):
	return (_calc_hexagon_verts(*args,**kwargs),((0,1,2,3,4,5,0),(0,0)))

def calc_hex_grid_points_from_radius(r = 1):
	num_rows = 2*r + 1
	rows = []
	for row_num in range(num_rows):
		if row_num <= r:
			num_hexagons = r + row_num + 1
		else:
			num_hexagons = r + (num_rows - row_num)
		column = []
		if row_num >= r:
			x_offset = (row_num * (sqrt3/2))
		else:
			x_offset = -((row_num - 2 * r) * (sqrt3/2))
		x_offset -= (sqrt3) * 1.5 * r
		z_offset = ((r - row_num) * 1.5)
		for h in range(num_hexagons):
			column.append(((x_offset + (sqrt3*h)), z_offset))

		rows.append(column)
	return rows

def draw_honeycomb(position,radius,scale,terrain_amplification,terrain_scale):
	origin_x, origin_z = position
	points = calc_hex_grid_points_from_radius(radius)
	tiles=[]
	for row in points:
		for x,z in row:
			p = calc_hexagon_verts_from_center_point(origin_x, origin_z, x, z, scale, 0, terrain_amplification=terrain_amplification,terrain_scale=terrain_scale)
			linepoints = calc_hexagon_outline_verts_from_center_point(origin_x, origin_z, x, z, scale, 0, terrain_amplification=terrain_amplification,terrain_scale=terrain_scale)
			t = Tile(p, ursina.color.rgb(255,255,255))
			t.outline = ursina.Entity(model=ursina.Mesh(vertices=(linepoints[0]), triangles=linepoints[1], mode='line', thickness=3*int(min(1,scale))), color=ursina.color.rgb(0,0,0), y = 0.02)
			tiles.append(t)
	return tiles

class Tile(ursina.Entity):
	def __init__(self, points, color):
		self.verts, self.tris = points
		ursina.Entity.__init__(self, model=ursina.Mesh(vertices=self.verts, triangles=self.tris, mode='ngon', thickness=1), color=color)
		self.outline = None

	def update(self):
		if self.hovered:
			print("Hovered")

	# def update(self):
	# 	if self.hovered:
	# 		self.color = ursina.rgb(0,0,255)
	# 		self.animate_color(self.color, duration=.1, interrupt='finish')

		
class MenuButton(ursina.Button):
    def __init__(self, text='', **kwargs):
        super().__init__(text, scale=(.25, .075), highlight_color=color.azure, **kwargs)

        for key, value in kwargs.items():
            setattr(self, key ,value)

class App(ursina.Ursina):
	def __init__(self, *args, **kwargs):
		ursina.Ursina.__init__(self, *args, **kwargs)
		self.origin = ursina.Entity(model='sphere', color=ursina.color.rgb(0,0,0), scale=0.000001, origin = (0,0), x=0,y=0,z=0)
		self.camera_pivot = ursina.Entity(parent=self.origin, y=20)
		self.editor_camera = ursina.EditorCamera(enabled=False, ignore_paused=True)
		self.editor_camera.enabled = True

		self.radius_slider = ursina.Slider(0, 25, default=0, step=1, text='Radius', parent=ursina.camera.ui, eternal = True, position = (-0.75,0.45))
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
		self.radius = 0
		self.terrain_amp = 1
		self.terrain_scale=1
		self.generate_map()
		self.editor_camera.y += 3

	def set_radius_multiplier(self):
		self.radius = self.radius_slider.value

	def set_scale_multiplier(self):
		self.scale = self.scale_slider.value

	def set_terrain_multiplier(self):
		self.terrain_amp = self.terrain_amp_slider.value

	def set_terrain_scale(self):
		self.terrain_scale = self.terrain_scale_slider.value

	def generate_map(self, radius = None, scale = None, amplification = None, terrain_scale = None):
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
		self.map_entities = draw_honeycomb((0, 0), self.radius, self.scale, self.terrain_amp, self.terrain_scale)

app = App()
# ursina.camera.orthographic = False
app.run()


























from ursina import *


# button_size = (.25, .075)
button_spacing = .075 * 1.25
menu_parent = Entity(parent=camera.ui, y=.15)
main_menu = Entity(parent=menu_parent)
load_menu = Entity(parent=menu_parent)
options_menu = Entity(parent=menu_parent)

state_handler = Animator({
    'main_menu' : main_menu,
    'load_menu' : load_menu,
    'options_menu' : options_menu,
    }
)


# main menu content
main_menu.buttons = [
    MenuButton('resume'),
    MenuButton('new game'),
    MenuButton('load game', on_click=Func(setattr, state_handler, 'state', 'load_menu')),
    MenuButton('options', on_click=Func(setattr, state_handler, 'state', 'options_menu')),
    MenuButton('quit', on_click=Sequence(Wait(.01), Func(sys.exit))),
]
for i, e in enumerate(main_menu.buttons):
    e.parent = main_menu
    e.y = -i * button_spacing



# load menu content
for i in range(3):
    MenuButton(parent=load_menu, text=f'Empty Slot {i}', y=-i * button_spacing)
load_menu.back_button = MenuButton(parent=load_menu, text='back', y=((-i-2) * button_spacing), on_click=Func(setattr, state_handler, 'state', 'main_menu'))



# options menu content
review_text = Text(parent=options_menu, x=.275, y=.25, text='Preview text', origin=(-.5,0))
for t in [e for e in scene.entities if isinstance(e, Text)]:
    t.original_scale = t.scale

text_scale_slider = Slider(0, 2, default=1, step=.1, dynamic=True, text='Text Size:', parent=options_menu, x=-.25)
def set_text_scale():
    for t in [e for e in scene.entities if isinstance(e, Text) and hasattr(e, 'original_scale')]:
        t.scale = t.original_scale * text_scale_slider.value
text_scale_slider.on_value_changed = set_text_scale



volume_slider = Slider(0, 1, default=Audio.volume_multiplier, step=.1, text='Master Volume:', parent=options_menu, x=-.25)
def set_volume_multiplier():
    Audio.volume_multiplier = volume_slider.value
volume_slider.on_value_changed = set_volume_multiplier

options_back = MenuButton(parent=options_menu, text='Back', x=-.25, origin_x=-.5, on_click=Func(setattr, state_handler, 'state', 'main_menu'))

for i, e in enumerate((text_scale_slider, volume_slider, options_back)):
    e.y = -i * button_spacing


# animate the buttons in nicely when changing menu
for menu in (main_menu, load_menu, options_menu):
    def animate_in_menu(menu=menu):
        for i, e in enumerate(menu.children):
            e.original_x = e.x
            e.x += .1
            e.animate_x(e.original_x, delay=i*.05, duration=.1, curve=curve.out_quad)

            e.alpha = 0
            e.animate('alpha', .7, delay=i*.05, duration=.1, curve=curve.out_quad)

            if hasattr(e, 'text_entity'):
                e.text_entity.alpha = 0
                e.text_entity.animate('alpha', 1, delay=i*.05, duration=.1)

    menu.on_enable = animate_in_menu


background = Entity(model='quad', texture='shore', parent=camera.ui, scale=(camera.aspect_ratio,1), color=color.white, z=1)

app.run()

import math, json, random
import ursina
from opensimplex import OpenSimplex

from catanengine import pick_random_resource_type, get_resource_color

NOISE_DAMPENING = 1
random.seed(random.random())
# generator = OpenSimplex(seed=3*int(random.uniform(0,50))).noise2
# generator_2 = OpenSimplex(seed=17*int(random.uniform(0,50))).noise2
# generator_3 = OpenSimplex(seed=27*int(random.uniform(0,50))).noise2
ISLAND_HEIGHT_MULTIPLIER = 2
SHORE_DROP = 2

class generator_object:
	def __init__(self):
		random.seed(random.random())
		self.generator = OpenSimplex(seed=3*int(random.uniform(0,50))).noise2
		self.generator_2 = OpenSimplex(seed=17*int(random.uniform(0,50))).noise2
		self.generator_3 = OpenSimplex(seed=27*int(random.uniform(0,50))).noise2
	def regen(self):
		random.seed(random.random())
		self.generator = OpenSimplex(seed=3*int(random.uniform(0,50))).noise2
		self.generator_2 = OpenSimplex(seed=17*int(random.uniform(0,50))).noise2
		self.generator_3 = OpenSimplex(seed=27*int(random.uniform(0,50))).noise2

Generator = generator_object()

def get_heightmap(x,z):
	return abs((Generator.generator(x/5, z/5) + Generator.generator_2(x/9, z/9))/(2*NOISE_DAMPENING))

def get_random_color():
	return ursina.color.rgb(random.randint(0,255),random.randint(0,255),random.randint(0,255))


#My "Volcano Island" layout secret sauce
#Give a max radius and current radius
#Returns a multiplier to apply to island heightmap
#X modulates a cos wave to break up the sin wave
def apply_island_clamp_function(height, scale, max_radius, current_radius, x):
	if max_radius and max_radius > 2:
		numerator = (current_radius - max_radius)**3
		denomenator = (current_radius - (max_radius+3*scale)**2)
		result = math.sqrt(abs(numerator**0.8/denomenator))

		#Might be the issue
		result -= 0.55 * (current_radius/max_radius) 

		result *= ISLAND_HEIGHT_MULTIPLIER
		result = abs(result)
		result *= height
	else:
		result = 1
	return result


sqrt3 = math.sqrt(3)
def _calc_hexagon_verts(position,r,map_radius, terrain_amplification = 1,terrain_scale=1):
	x,y,z=position
	hr = r*0.5
	sqrt3hr = sqrt3*hr
	#N, NE, SE, S, SW, NW
	hex_verts = [[0, r],[sqrt3hr, hr],[sqrt3hr, -hr],[0, -r],[-sqrt3hr, -hr],[-sqrt3hr, hr]]
	verts = []
	for v in hex_verts:
		height = get_heightmap((v[0]+x*r)/terrain_scale,(v[1]+z*r)/terrain_scale)*terrain_amplification*2.5
		current_radius = math.sqrt((v[0]+x*r)*(v[0]+x*r)+(v[1]+z*r)*(v[1]+z*r))
		verts.append(
			[float("{:.5f}".format(v[0])),
			float("{:.5f}".format(apply_island_clamp_function(height, r, map_radius, current_radius,v[0]+x*r))),
			float("{:.5f}".format(v[1]))]
		)
	return verts

def _calc_water_hexagon_verts(r,scale):
	r+=1
	scale *= 30
	hr = r*0.5*scale
	sqrt3hr = sqrt3*hr
	#N, NE, SE, S, SW, NW
	hex_verts = [[0, r*scale],[sqrt3hr, hr],[sqrt3hr, -hr],[0, -r*scale],[-sqrt3hr, -hr],[-sqrt3hr, hr]]
	verts = []
	for v in hex_verts: verts.append([v[0],0,v[1]])
	return verts, ((0,5,4),(0,4,3),(0,3,2),(0,2,1),(0,1,0))



# def _calc_shore_hexagons(position, radius, scale,terrain_amplification,terrain_scale):
# 	x,y,z = position
# 	r = radius + 1
# 	num_rows = 2*r + 1
# 	rows = []
# 	for row_num in range(num_rows):
# 		if row_num <= r:
# 			num_hexagons = r + row_num + 1
# 		else:
# 			num_hexagons = r + (num_rows - row_num)
# 		row = []
# 		if row_num >= r:
# 			x_offset = (row_num * (sqrt3/2))
# 		else:
# 			x_offset = -((row_num - 2 * r) * (sqrt3/2))
# 		x_offset -= (sqrt3) * 1.5 * r
# 		z_offset = ((r - row_num) * 1.5)
# 		for h in range(num_hexagons):
# 			row.append(((x_offset + (sqrt3*h)), z_offset))
# 		rows.append(row)

# 	def calculate_perimeter_hexagon_verts(pos):
# 		pos_x, pos_z = pos
# 		hr = r*0.5
# 		sqrt3hr = sqrt3*hr
# 		hex_verts = [(0, r),(sqrt3hr, hr),(sqrt3hr, -hr),(0, -r),(-sqrt3hr, -hr),(-sqrt3hr, hr)]
# 		verts = []
# 		for v in hex_verts:
# 			height = get_heightmap((v[0]+pos_x*r)/terrain_scale,(v[1]+z*r)/terrain_scale)*terrain_amplification*2.5
# 			current_radius = math.sqrt((v[0]+pos_x*r)*(v[0]+pos_x*r)+(v[1]+z*r)*(v[1]+z*r))
# 			verts.append(
# 				[float("{:.5f}".format(v[0])),
# 				float("{:.5f}".format(apply_island_clamp_function(height, r, radius*scale, current_radius,v[0]+pos_x*r))),
# 				float("{:.5f}".format(v[1]))]
# 			)
# 		return verts
# 	perimeter_hexagons = []
# 	row_index = 0
# 	for ro in rows:
# 		index = 0
# 		for x,z in ro:
# 			#if hexagon is in the first row
# 			needed = False
# 			#N, NE, SE, S, SW, NW
# 			hex_verts = calculate_perimeter_hexagon_verts((x,z))

# 			if row_index == 0:#If in the top row
# 				needed=True
# 				# hex_verts[5][1]-=SHORE_DROP
# 				# hex_verts[0][1]-=SHORE_DROP
# 				# hex_verts[1][1]-=SHORE_DROP

# 			if index == 0:#If in the first column
# 				needed=True
# 				# if row_index < r: #Top half
# 				# 	hex_verts[4][1]-=SHORE_DROP
# 				# 	hex_verts[5][1]-=SHORE_DROP
# 				# 	hex_verts[0][1]-=SHORE_DROP
# 				# if row_index > r: #Bottom Half
# 				# 	hex_verts[3][1]-=SHORE_DROP
# 				# 	hex_verts[4][1]-=SHORE_DROP
# 				# 	hex_verts[5][1]-=SHORE_DROP

# 			if index == len(ro)-1:#If in the last column
# 				needed=True
# 				# if row_index < r: #Top half
# 				# 	hex_verts[0][1]-=SHORE_DROP
# 				# 	hex_verts[1][1]-=SHORE_DROP
# 				# 	hex_verts[2][1]-=SHORE_DROP
# 				# if row_index > r: #Bottom Half
# 				# 	hex_verts[1][1]-=SHORE_DROP
# 				# 	hex_verts[2][1]-=SHORE_DROP
# 				# 	hex_verts[3][1]-=SHORE_DROP

# 			if row_index == len(rows)-1:#If in the bottom row
# 				needed=True
# 				# hex_verts[2][1]-=SHORE_DROP
# 				# hex_verts[3][1]-=SHORE_DROP
# 				# hex_verts[4][1]-=SHORE_DROP
# 			if needed:
# 				perimeter_hexagons.append(ShoreTile(position, (hex_verts,((0,5,4),(0,4,3),(0,3,2),(0,2,1),(0,1,0)))))
# 			index +=1
# 		row_index +=1
# 	return perimeter_hexagons

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
	Generator.regen()
	origin_x, origin_z = position
	points = calc_hex_grid_points_from_radius(radius)
	tiles=[]
	for row in points:
		for x,z in row:
			position=((origin_x+x*scale),0,(origin_z+z*scale))
			color = get_resource_color(pick_random_resource_type())
			p = calc_hexagon_verts_from_center_point((x, 0, z), scale, (scale+.5)*radius, terrain_amplification=terrain_amplification,terrain_scale=terrain_scale)
			linepoints = calc_hexagon_outline_verts_from_center_point((x, 0, z), scale, (scale+.5)*radius, terrain_amplification=terrain_amplification,terrain_scale=terrain_scale)
			t = Tile(position, p, ursina.color.colors[color])
			t.outline = ursina.Entity(model=ursina.Mesh(vertices=(linepoints[0]), triangles=linepoints[1], mode='line', thickness=int(3*min(1,scale))), position=position, color=ursina.color.rgb(0,0,0), y = 0.02)
			tiles.append(t)
	
	#Calculate shore
	rows = calc_hex_grid_points_from_radius(radius+1)
	shoretiles = []
	row_index = 0
	for row in rows:
		index = 0
		for x,z in row:
			position=((origin_x+x*scale),0,(origin_z+z*scale))
			hex_verts, tris = calc_hexagon_verts_from_center_point((x, 0, z), scale, (scale+.5)*radius, terrain_amplification=terrain_amplification,terrain_scale=terrain_scale)

			needed = False
			#N, NE, SE, S, SW, NW

			verts_to_cliffdrop = set()

			if row_index == 0:#If in the top row
				needed=True
				verts_to_cliffdrop.update({5,0,1})

			if row_index == radius: verts_to_cliffdrop.update({0})
			if row_index == radius+1: verts_to_cliffdrop.update({0})

			if index == 0:
				needed=True
				if row_index < radius: verts_to_cliffdrop.update({4,5,0})#Top half
				if row_index == radius: verts_to_cliffdrop.update({4,5})#Top half
				if row_index > radius: verts_to_cliffdrop.update({3,4,5})#Bottom Half

			if index == len(row)-1:#If in the last column
				needed=True
				if row_index < radius: verts_to_cliffdrop.update({0,1,2})#Top half
				if row_index == radius: verts_to_cliffdrop.update({1,2})#Top half
				if row_index > radius: verts_to_cliffdrop.update({1,2,3})#Bottom Half

			if row_index == len(rows)-1:#If in the bottom row
				needed=True
				verts_to_cliffdrop.update({2,3,4})
			if needed:
				for v in verts_to_cliffdrop:
					hex_verts[v][1] =-SHORE_DROP
				shoretiles.append(ShoreTile(position, (hex_verts,((0,5,4),(0,4,3),(0,3,2),(0,2,1),(0,1,0)))))
				
			index += 1
		row_index += 1

	#Draw Water
	p = _calc_water_hexagon_verts(radius, scale)
	water = WaterTile((0,-0.3*scale,0), p)

	return tiles

#Horribly slow but constructs the hexagon grid
# def draw_honeycomb_new(position,radius,scale,terrain_amplification,terrain_scale):
# 	origin_x, origin_z = position
# 	points = calc_hex_grid_points_from_radius(radius)

# 	tiles=[]
# 	unique_edges = set()
# 	for row in points:
# 		for x,z in row:
# 			color = get_resource_color(pick_random_resource_type())
# 			p = calc_hexagon_verts_from_center_point(origin_x, origin_z, x, z, scale, 0, terrain_amplification=terrain_amplification,terrain_scale=terrain_scale)
# 			linepoints = calc_hexagon_outline_verts_from_center_point(origin_x, origin_z, x, z, scale, 0, terrain_amplification=terrain_amplification,terrain_scale=terrain_scale)
# 			t = Tile(p, ursina.color.colors[color])

# 			line_verts, line_tris = linepoints
# 			for i in range(0, len(line_verts)-1):
# 				if line_verts[i][0] > line_verts[i+1][0]:
# 					unique_edges.add((line_verts[i], line_verts[i+1]))
# 				else:
# 					unique_edges.add((line_verts[i+1], line_verts[i]))
# 			if line_verts[len(line_verts)-1][0] > line_verts[0][0]:
# 				unique_edges.add((line_verts[len(line_verts)-1], line_verts[0]))
# 			else:
# 				unique_edges.add((line_verts[0], line_verts[len(line_verts)-1]))
# 			# t.outline = ursina.Entity(model=ursina.Mesh(vertices=(linepoints[0]), triangles=linepoints[1], mode='line', thickness=int(3*min(1,scale))), color=ursina.color.rgb(0,0,0), y = 0.02)
# 			tiles.append(t)
# 	for e in unique_edges:
# 		print(e)

# 	verts = []
# 	tris = []
# 	for e in unique_edges:
# 		first_index = 0
# 		second_index = 0
# 		e0, e1 =e
# 		if e0 in verts:
# 			first_index = verts.index(e0)
# 		else:
# 			verts.append(e0)
# 			first_index = len(verts)-1
# 		if e1 in verts:
# 			second_index = verts.index(e1)
# 		else:
# 			verts.append(e1)
# 			second_index = len(verts)-1
# 		tris.append((first_index, second_index))
# 		gridmesh = ursina.Entity(model=ursina.Mesh(vertices=verts, triangles=tris, mode='line', thickness=3), color=ursina.color.rgb(0,0,0), y = 0.02)

# 	print(f"Counted {len(unique_edges)} verts")
# 	return tiles

class Tile(ursina.Button):
	def __init__(self, position, points, color):
		self.verts, self.tris = points
		ursina.Button.__init__(
			self,
			parent=ursina.scene,
			model=ursina.Mesh(vertices=self.verts, triangles=self.tris, mode='ngon', thickness=2),
			color=color,
			texture="white_cube",
			origin=0,
			position=position,
		)
		self.outline = None

	def input(self, key):
		if self.hovered:
			if key == 'left mouse down':
				self.color = ursina.rgb(0,0,255)
				self.animate_color(self.color, duration=.1, interrupt='finish')

			# if key == 'right mouse down':
			#     destroy(self)

	# def update(self):
	# 	if self.hovered:
	# 		self.color = ursina.rgb(0,0,255)
	# 		self.animate_color(self.color, duration=.1, interrupt='finish')

class ShoreTile(ursina.Entity):
	def __init__(self, position, points):
		self.verts, self.tris = points
		ursina.Entity.__init__(
			self,
			parent=ursina.scene,
			model=ursina.Mesh(vertices=self.verts, triangles=self.tris, mode='ngon', thickness=2),
			# color=ursina.color.colors["blue"],
			# texture="white_cube",
			origin=0,
			position=position,
		)
		self.outline = None
		self.texture = ursina.Texture("textures/sand.png")

class WaterTile(ursina.Entity):
	def __init__(self, position, points):
		self.verts, self.tris = points
		ursina.Entity.__init__(
			self,
			parent=ursina.scene,
			model=ursina.Mesh(vertices=self.verts, triangles=self.tris, mode='ngon', thickness=2),
			color=ursina.color.rgb(20,50,140),
			# texture="white_cube",
			origin=0,
			position=position,
		)
		self.outline = None
class MenuButton(ursina.Button):
	def __init__(self, text='', **kwargs):
		super().__init__(text, scale=(.25, .075), highlight_color=color.azure, **kwargs)

		for key, value in kwargs.items():
			setattr(self, key ,value)

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
ursina.camera.mode = "orthoganol"
app.run()

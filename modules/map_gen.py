import math, random, json
from PIL import Image, ImageOps
import numpy as np
import ursina
from .settings import settings
from HexplorationEngine import get_resource_color
from .texture_gen import BoardTexturer
from .entities import WaterTile, ShoreTile, LandMasses, Edge, Node, Tile
from .UrsinaLighting import LitObject, LitPointLight, LitInit
from opensimplex import OpenSimplex

#These get calculated a lot
sqrt3 = math.sqrt(3.0)
halfsqrt3 = math.sqrt(3.0)/2.0

def _calc_hexagon_verts(map_radius = 1):
	return [[0,0,0],[0,0,1],[halfsqrt3,0,0.5],[halfsqrt3,0,-0.5],[0,0,-1],[-halfsqrt3,0,-0.5],[-halfsqrt3,0,0.5]]
#Draws a 'circle' of tris around a center point
def calc_hexagon_verts_from_center_point(*args, **kwargs):
	return _calc_hexagon_verts(*args,**kwargs),  (0,6,5,0,5,4,0,4,3,0,3,2,0,2,1,0,1,6)
#Ignores the center vert and just draws the shape with lines
def calc_hexagon_outline_verts_from_center_point(*args, **kwargs):
	return _calc_hexagon_verts(*args,**kwargs)[1:],  ((0,1,2,3,4,5,0),)
#Calculates all the centerpoints for hexagons in a given radius with r=0 being just the center hexagon
def calc_hex_grid_points_from_radius(r = 1):
	num_rows = 2*r + 1
	rows = []
	for row_num in range(num_rows):
		if row_num <= r:
			num_hexagons = r + row_num + 1
		else:
			num_hexagons = r + (num_rows - row_num)
		if row_num >= r:
			x_offset = (row_num * halfsqrt3)
		else:
			x_offset = -((row_num - 2 * r) * halfsqrt3)
		x_offset -= sqrt3 * 1.5 * r
		z_offset = ((r - row_num) * 1.5)
		column = []
		for h in range(num_hexagons):
			column.append(((x_offset + (sqrt3*h)), z_offset))
		rows.append(column)
	return rows

#Prevents island from spawning near the center of the map
def apply_decorative_island_clamp_function(pos_x,pos_z):
	half_settings_res = float(settings.island_resolution)/2
	fifth_settings_res = float(settings.island_resolution)*0.2
	rel_x = float(pos_x) - half_settings_res
	rel_z = float(pos_z) - half_settings_res
	if abs(rel_x) < fifth_settings_res and abs(rel_z) < fifth_settings_res:
		rx = rel_x/(fifth_settings_res)
		rz = rel_z/(fifth_settings_res)
		ratio = math.sqrt(rx*rx+rz*rz)
	else:
		ratio = 1.0
	return min(1.0, ratio)

class noise_generator_object:
	def __init__(self, seed = None):
		self.regen(seed)
	def regen(self, seed): #Randomizes the generator seeds again
		self.seed = seed or random.uniform(0,1)
		random.seed(random.random())
		self.generator = OpenSimplex(seed=3*int(random.uniform(0,50))).noise2
		self.generator_2 = OpenSimplex(seed=17*int(random.uniform(0,50))).noise2
		self.generator_3 = OpenSimplex(seed=27*int(random.uniform(0,50))).noise2
	def get_heightmap(self,x,z):
		return abs((self.generator(x/5, z/5) + self.generator_2(x/9, z/9))/(2*settings.heightmap_noise_dampening))
	def get_scaled_heightmap(self,x,z,scale):
		return abs((self.generator(x/scale, z/scale) + self.generator_2(x/scale, z/scale))/2)
noise_generator = noise_generator_object(seed = 3)

def generate_island_mesh(scale):
	resolution = settings.island_resolution
	arr = np.full([resolution, resolution, 3], settings.sand_color, dtype=np.uint8)
	heightmap=[]
	for x in range(resolution):
		row=[]
		for z in range(resolution):
			y=noise_generator.get_scaled_heightmap(float(x),float(z),resolution/settings.island_scale)
			y*=apply_decorative_island_clamp_function(x,z)
			row.append(y)
			if y > settings.grass_cutoff: arr[x][z] = settings.grass_color
			elif y > settings.dirt_cutoff: arr[x][z] = settings.dirt_color
			elif y > settings.mud_cutoff: arr[x][z] = settings.mud_color
		heightmap.append(row)
	texname = f"textures/temp/island_mesh.png"
	ImageOps.flip(Image.fromarray(np.swapaxes(np.uint8(arr),0,1)).convert('RGB').rotate(90)).save(texname)
	return LandMasses(heightmap, scale, texname)

class MapMaker(ursina.Entity):
	def __init__(self, game, position, radius):
		ursina.Entity.__init__(self, parent=ursina.scene, eternal=True)
		#object lists
		self.tiles,self.grid,self.shore,self.water=[],[],[],[]
		self.lighting,self.islands,self.lights = [],[],[]
		self.origin_x, self.origin_z = position
		self.game, self.map_radius = game, radius

	def generate_map(self):
		print(f"Generating Map")
		noise_generator.regen(random.uniform(0,1))
		island_center_points = calc_hex_grid_points_from_radius(self.map_radius+1) #Outer edge is water tiles
		self.light_controller = LitInit() #Enable lighting shader
		self.make_board(island_center_points)
		self.generate_tile_grid(calc_hex_grid_points_from_radius(self.map_radius))
		# self.generate_island_shores(calc_hex_grid_points_from_radius(self.map_radius+1))
		self.generate_scenery_islands()
		self.generate_water()
		self.generate_sky()
		self.generate_lighting()
		objects = []
		[objects.extend(l) for l in [self.tiles,self.water,self.lights]] #self.grid
		return objects

	def generate_tile_grid(self, grid_points):
		print("Generating Tile Grid")
		self.grid=[]
		for row in grid_points:
			for x,z in row:
				position=((self.origin_x+x)*settings.board_scale,0,(self.origin_z+z)*settings.board_scale)
				p = calc_hexagon_outline_verts_from_center_point(.5*self.map_radius)
				p = ([[i[0],settings.island_height_above_water,i[2]] for i in p[0]], p[1])
				t = ursina.Entity(parent=self, scale=settings.board_scale, position=position, model=ursina.Mesh(vertices=(p[0]), triangles=p[1], mode='line', thickness=settings.tile_grid_thickness), color=ursina.color.rgb(0,0,0), y = 0.02)
				self.grid.append(t)

	# def generate_island_shores(self, grid_points):
	# 	print("Generating Island Shores")
	# 	#Calculate shore
	# 	#Systematically generate the hexagons we need
	# 	#and then drop their outermost points to
	# 	#create a bank
	# 	shore_parent = ursina.Entity(parent=self) 
	# 	self.shore = []
	# 	row_index = 0
	# 	r = self.map_radius + 1
	# 	for row in grid_points:
	# 		index = 0
	# 		for x,z in row:
	# 			position=((self.origin_x+x),0,(self.origin_z+z))
	# 			hex_verts, tris = calc_hexagon_verts_from_center_point(.5*self.map_radius)
	# 			needed = False #If the hexagon is one of the needed ones (edges)
	# 			#Sets to ensure vertex translations are only applied once
	# 			verts_to_cliffdrop = set()
	# 			verts_to_increase_x = set()
	# 			verts_to_increase_z = set()
	# 			verts_to_decrease_x = set()
	# 			verts_to_decrease_z = set()
	# 			if row_index == r:
	# 				verts_to_cliffdrop.update({1}) #Only flag needed if on either end, will flag below
	# 			if row_index == 0:#If in the top row
	# 				needed=True
	# 				verts_to_cliffdrop.update({6,1,2})
	# 				verts_to_increase_z.update({0,6,1,2})
	# 			if index == 0:
	# 				needed=True
	# 				if row_index < r:
	# 					verts_to_cliffdrop.update({5,6,1})#Top half
	# 					verts_to_decrease_x.update({0,5,6,1})
	# 					verts_to_increase_z.update({0,5,6,1})
	# 				elif row_index == r:
	# 					verts_to_cliffdrop.update({4,5,6,1})
	# 					verts_to_decrease_x.update({0,4,5,6,1})
	# 					verts_to_increase_z.update({0,5,6,1})
	# 					verts_to_decrease_z.update({4})
	# 				elif row_index > r:
	# 					verts_to_cliffdrop.update({4,5,6})#Bottom Half
	# 					verts_to_decrease_x.update({0,4,5,6})
	# 					verts_to_decrease_z.update({0,4,5,6})

	# 			elif index == len(row)-1:#If in the last column
	# 				needed=True
	# 				if row_index < r:
	# 					verts_to_cliffdrop.update({1,2,3})#Top half
	# 					verts_to_increase_x.update({0,1,2,3})
	# 					verts_to_increase_z.update({0,1,2,3})
	# 				elif row_index == r:
	# 					verts_to_cliffdrop.update({1,2,3,4})#Top half
	# 					verts_to_increase_x.update({0,1,2,3,4})
	# 					verts_to_decrease_z.update({0,2,3,4})
	# 					verts_to_increase_z.update({1})
	# 				elif row_index > r:
	# 					verts_to_cliffdrop.update({2,3,4})#Bottom Half
	# 					verts_to_increase_x.update({0,2,3,4})
	# 					verts_to_decrease_z.update({0,2,3,4})

	# 			if row_index == len(grid_points)-1:#If in the bottom row
	# 				needed=True
	# 				verts_to_cliffdrop.update({3,4,5})
	# 				verts_to_decrease_z.update({0,3,4,5})

	# 			if needed:
	# 				for v in verts_to_cliffdrop:
	# 					hex_verts[v][1] =-settings.shore_drop
	# 				for v in verts_to_increase_z:
	# 					mult = settings.shore_spread
	# 					if v == 0: mult *= 0.5
	# 					hex_verts[v][2] += mult
	# 				for v in verts_to_decrease_z:
	# 					mult = settings.shore_spread
	# 					if v == 0: mult *= 0.5
	# 					hex_verts[v][2] -= mult
	# 				for v in verts_to_increase_x:
	# 					mult = settings.shore_spread
	# 					if v == 0: mult *= 0.5
	# 					hex_verts[v][0] += mult
	# 				for v in verts_to_decrease_x:
	# 					mult = settings.shore_spread
	# 					if v == 0: mult *= 0.5
	# 					hex_verts[v][0] -= mult

	# 				hex_verts[0][1] =-settings.shore_drop/3.0 #Drop center of hexagon for slope
	# 				self.shore.append(ShoreTile(shore_parent, position, (hex_verts,((0,6,5),(0,5,4),(0,4,3),(0,3,2),(0,2,1),(0,1,6)))))
	# 			index += 1
	# 		row_index += 1
	# 	for s in self.shore:
	# 		s.enabled = False

	# 	ignorelist = []
	# 	for l in [self.grid]:
	# 		for i in l: ignorelist.append(i)
	# 	shore_parent.combine(ignore=ignorelist)

	def generate_water(self):
		print("Generating Water")
		rscale = 2*self.map_radius
		self.water = []
		for _x in range(-settings.water_subdivisions_per_axis_radius,settings.water_subdivisions_per_axis_radius+1):
			for _z in range(-settings.water_subdivisions_per_axis_radius,settings.water_subdivisions_per_axis_radius+1):
				self.water.append(
					LitObject(
						position=(
							_x*rscale*settings.water_scale+self.origin_x,
							0,
							_z*rscale*settings.water_scale+self.origin_z,
							),
						model='quad',
						rotation=(90,0,90),
						scale=rscale*settings.water_scale,
						color=ursina.color.rgb(120,160,200),
						water=True,
						cubemapIntensity = 0.75,
						ambientStrength = 0.75,
					)
				)

	def generate_sky(self):
		print("Generating Sky")
		self.sky = ursina.Sky(model = "sphere", double_sided = True, texture = "textures/skybox.jpg", rotation = (0, 90, 0))

	def generate_lighting(self):
		print("Generating Lighting")
		self.lights = [
			LitPointLight(
				position = ursina.Vec3(settings.water_scale*10,5*(2*settings.water_subdivisions_per_axis_radius+1)*settings.water_scale,settings.water_scale*10),
				color = ursina.color.colors["white"],
				range=10000,
				intensity = 8),
		]

	def generate_scenery_islands(self):
		print("Generating Islands")
		self.islands = generate_island_mesh(2*self.map_radius*(2*settings.water_subdivisions_per_axis_radius+1)*settings.water_scale)

	def make_board(self, grid_points):
		print("Generating game board")

		edges = []
		edgedict = {}
		nodes = []
		nodedict = {}
		tiles = []
		offsets = calc_hexagon_outline_verts_from_center_point(.5*self.map_radius)
		
		hexes = []
		tile_rows = []

		width, height = len(grid_points), max((len(r) for r in grid_points))
		bt = BoardTexturer(width, height)
		bt.generate_board()

		middle = (len(grid_points)-1)/2	
		for row_index in range(len(grid_points)):
			hexrow = []
			tile_row = []
			for col_index in range(len(grid_points[row_index])):
				x,z=grid_points[row_index][col_index]
				p = offsets
				verts = p[0]
				verts = list((v[0]+self.origin_x+x,v[2]+self.origin_z+z) for v in verts)
				if row_index==0: #If in top row
					if col_index == 0:
						edgeverts = [(verts[0],verts[1]),(verts[1],verts[2]),(verts[2],verts[3]),(verts[3],verts[4]),(verts[4],verts[5]),(verts[5],verts[0])]
					else:
						prevverts = hexrow[col_index-1]
						edgeverts = [
							(verts[0],verts[1]),
							(verts[1],verts[2]),
							(verts[2],verts[3]),
							(verts[3],prevverts[2]),
							(prevverts[2],verts[5]),
							(verts[5],verts[0])
						]
				else:
					#top verts can be obtained from previous row
					prev_row = hexes[row_index-1]				
					if row_index < middle:
						if col_index == 0:
							above_left_hex = None
							above_right_hex = prev_row[col_index]
						elif col_index == len(grid_points[row_index]) - 1:
							above_left_hex = prev_row[col_index-1]
							above_right_hex = None
						else:
							above_left_hex = prev_row[col_index-1]
							if row_index == middle:
								above_right_hex = None
							else:
								above_right_hex = prev_row[col_index]
					elif row_index == middle:
						if col_index == 0:
							above_left_hex = None
							above_right_hex = prev_row[0]
						elif col_index == len(grid_points[row_index]) - 1:
							above_left_hex = prev_row[col_index-1]
							above_right_hex = None
						else:
							above_left_hex = prev_row[col_index-1]
							above_right_hex = prev_row[col_index]
					else:
						if col_index == len(grid_points[row_index]) - 1:
							above_left_hex = prev_row[col_index]
							above_right_hex = None
						else:
							above_left_hex = prev_row[col_index]
							above_right_hex = prev_row[col_index+1]

					v0 = above_left_hex[2] if above_left_hex else above_right_hex[4]
					v1 = above_right_hex[3] if above_right_hex else verts[1]
					prevverts = hexrow[col_index-1] if col_index else None
					v4 = prevverts[2] if prevverts else verts[4]
					v5 = prevverts[1] if prevverts else verts[5]

					edgeverts = [(v0,v1),(v1,verts[2]),(verts[2],verts[3]),(verts[3],v4),(v4,v5),(v5,v0)]
				hexrow.append(verts)
				
				tile_edges = []
				tile_nodes = set()
				for e in edgeverts: #Get edges, we are cheating and using float precision to check if they already exist...
					center = (float("{:0.4f}".format((e[0][0]+e[1][0])/2))),(float("{:0.4f}".format((e[0][1]+e[1][1])/2)))
					if edgedict.get(center):
						tile_edges.append(edgedict.get(center))
						continue
					else:
						node_a = nodedict.get((float("{:0.4f}".format(e[0][0])), float("{:0.4f}".format(e[0][1]))))
						if not node_a:
							node_a = Node(self.game, e[0])
							nodedict[(float("{:0.4f}".format(e[0][0])), float("{:0.4f}".format(e[0][1])))] = node_a
							nodes.append(node_a)
						node_b = nodedict.get((float("{:0.4f}".format(e[1][0])), float("{:0.4f}".format(e[1][1]))))
						if not node_b:
							node_b = Node(self.game, e[1])
							nodedict[(float("{:0.4f}".format(e[1][0])), float("{:0.4f}".format(e[1][1])))] = node_b
							nodes.append(node_b)
					edg = Edge(self.game, center, e, node_a, node_b)
					tile_edges.append(edg)
					edges.append(edg)
					edgedict[center] = edg
				for e in tile_edges: tile_nodes.update((e.node_a, e.node_b))
				position=((self.origin_x+x),0,(self.origin_z+z))
				texture=bt.get_image_piece(row_index,col_index),
				if col_index == 0 or col_index == len(grid_points[row_index])-1 or row_index == 0 or row_index == len(grid_points)-1:
					t = WaterTile(self.game, position, tile_edges, tile_nodes)
				else:
					t = Tile(self.game, position, tile_edges, tile_nodes, map_center=row_index==middle and col_index==middle)
				t.enabled = False
				tiles.append(t)
				tile_row.append(t)
			tile_rows.append(tile_row)
			hexes.append(hexrow)
		edgescopy = edges.copy()
		for e in edges: #Link Edges
			edgescopy.remove(e)
			for e2 in edges:
				#If any of the nodes match
				if any((e.node_a is e2.node_a,
						e.node_a is e2.node_b,
						e.node_b is e2.node_a,
						e.node_b is e2.node_b)):
					e.add_neighbor_edge(e2)
					e2.add_neighbor_edge(e)
		for n in nodes: #Link tiles
			ts = n.neighbor_tiles
			for t in ts:
				for t2 in ts:
					if t is t2: continue
					t.add_neighbor_tile(t2)
		tile_parent = ursina.Entity()
		#Make hexagon tiles
		self.board_tiles = []
		for z in range(len(tile_rows)):
			for x in range(len(tile_rows[z])):
				t = tile_rows[z][x]
				if type(t) is Tile:
					tile = LitObject(
						parent = tile_parent,
						color=t.get_resource_color(),
						texture=bt.get_image_piece(t.x,t.z),
						model="hexagon",
						position=(t.x,settings.board_scale*settings.island_height_above_water,t.z),
						scale=settings.board_scale,
						)
					t.tile_entity = tile
					self.board_tiles.append(tile)
				elif type(t) is WaterTile:
					tile = LitObject(
						parent = tile_parent,
						color=ursina.rgb(60,100,230),
						texture=bt.get_image_piece(t.x,t.z),
						model="hexagon",
						position=(t.x,0.5*settings.board_scale*settings.island_height_above_water,t.z),
						scale=settings.board_scale,
						cubemapIntensity=0.75,
						)
					t.tile_entity = tile
					self.board_tiles.append(tile)
		self.game.create(tiles,edges,nodes)

		for e in edges: #Determine water edges
			if all(type(t) is WaterTile for t in e.neighbor_tiles):
				e.water_edge = True

		shore_edges = []
		for e in edges: #Run through again to spawn random numbers of ports
			#Check if edge touches both water and land
			if len({type(t) for t in e.neighbor_tiles}) > 1: #Both land and water
				shore_edges.append(e)

		#Randomly assign ports
		for _ in range(self.game.number_of_trading_port_attempts):
			if not shore_edges: break
			edge = random.choice(shore_edges)
			shore_edges.remove(edge) #Remove it from list 
			if not any(e.port for e in edge.neighbor_edges):
				if random.uniform(0,1) < self.game.port_chance:
					edge.enable_port()


		for n in nodes: #Determine water nodes
			if all(type(t) is WaterTile for t in n.neighbor_tiles):
				n.water_node = True

	def toggle_water(self):
		for e in self.water: e.enabled = not e.enabled
		print("Toggled Water")
	def toggle_grid(self):
		for e in self.grid: e.enabled = not e.enabled
		print("Toggled Grid")
	def toggle_skybox(self):
		self.sky.enabled = not self.sky.enabled
		print("Toggled Skybox")
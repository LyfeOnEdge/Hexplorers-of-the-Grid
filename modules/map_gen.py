import math
import ursina
from .settings import settings
from .catanengine import get_resource_color, pick_random_resource_type
from .noise_gen import noiseGenerator
from .entities import Tile, ShoreTile, WaterTile
from .UrsinaLighting import LitObject, LitPointLight

sqrt3 = math.sqrt(3)

#My "Volcano Island" layout secret sauce
def apply_island_clamp_function(height, scale, max_radius, current_radius, x):
	if max_radius and max_radius > 2:
		numerator = (current_radius - max_radius)**3
		denomenator = (current_radius - (max_radius+3*scale)**2)
		result = math.sqrt(abs(numerator**0.8/denomenator))
		result -= 0.15 * (current_radius/max_radius) 
		result *= settings.island_height_multiplier
		result = abs(result)
		result *= height
	else:
		result = 1
	return result

def _calc_hexagon_verts(position,r,map_radius, terrain_amplification = 1,terrain_scale=1):
	x,y,z=position
	hr = r*0.5
	sqrt3hr = sqrt3*hr
	#N, NE, SE, S, SW, NW
	hex_verts = [[0,0],[0, r],[sqrt3hr, hr],[sqrt3hr, -hr],[0, -r],[-sqrt3hr, -hr],[-sqrt3hr, hr]]
	verts = []
	for v in hex_verts:
		height = noiseGenerator.get_heightmap((v[0]+x*r)/terrain_scale,(v[1]+z*r)/terrain_scale)*terrain_amplification*2.5
		current_radius = math.sqrt((v[0]+x*r)*(v[0]+x*r)+(v[1]+z*r)*(v[1]+z*r))
		verts.append(
			[float("{:.5f}".format(v[0])),
			float("{:.5f}".format(apply_island_clamp_function(height, r, map_radius, current_radius,v[0]+x*r))),
			float("{:.5f}".format(v[1]))]
		)
	return verts

def calc_hexagon_verts_from_center_point(*args, **kwargs):
	return (_calc_hexagon_verts(*args,**kwargs),((0,6,5),(0,5,4),(0,4,3),(0,3,2),(0,2,1),(0,1,6)))

def calc_hexagon_outline_verts_from_center_point(*args, **kwargs): #Ignores the center vert and just draws the shape with lines
	return (_calc_hexagon_verts(*args,**kwargs)[1:],((0,1,2,3,4,5,0),)) 

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
	noiseGenerator.regen()
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
			t.outline = ursina.Entity(position=position, model=ursina.Mesh(vertices=(linepoints[0]), triangles=linepoints[1], mode='line', thickness=int(3*min(1,scale))), color=ursina.color.rgb(0,0,0), y = 0.02)
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
				verts_to_cliffdrop.update({6,1,2})

			if row_index == radius: verts_to_cliffdrop.update({1})
			if row_index == radius+1: verts_to_cliffdrop.update({1})

			if index == 0:
				needed=True
				if row_index < radius: verts_to_cliffdrop.update({5,6,1})#Top half
				if row_index == radius: verts_to_cliffdrop.update({5,6})#Top half
				if row_index > radius: verts_to_cliffdrop.update({4,5,6})#Bottom Half

			if index == len(row)-1:#If in the last column
				needed=True
				if row_index < radius: verts_to_cliffdrop.update({1,2,3})#Top half
				if row_index == radius: verts_to_cliffdrop.update({2,3})#Top half
				if row_index > radius: verts_to_cliffdrop.update({2,3,4})#Bottom Half

			if row_index == len(rows)-1:#If in the bottom row
				needed=True
				verts_to_cliffdrop.update({3,4,5})
			if needed:
				for v in verts_to_cliffdrop:
					hex_verts[v][1] =-SHORE_DROP*scale
				hex_verts[0][1] =-0.5*SHORE_DROP #Drop center of hexagon half way for slope
				shoretiles.append(ShoreTile(position, (hex_verts,((0,6,5),(0,5,4),(0,4,3),(0,3,2),(0,2,1),(0,1,6)))))
				
			index += 1
		row_index += 1

	#Draw Water
	p = _calc_water_hexagon_verts(radius, scale)
	# water = WaterTile((0,-0.3*scale,0), p)

	rscale = 2*radius*scale
	square = [(-rscale,-0.2,rscale),(rscale,-0.2,rscale),(rscale,-0.2,-rscale),(-rscale,-0.2,-rscale)]
	tris = [(3,2,1),(3,1,0)]

	water_tiles = []
	water_scale = 8
	for _x in range(-2,3):
		for _z in range(-2,3):
			water_tiles.append(LitObject(position=(_x*rscale*water_scale,-0.25*scale,_z*rscale*water_scale),model='quad',rotation=(90,0,90),scale=rscale*water_scale, color=ursina.color.rgb(60,100,240),water=True))

	lightsource_centered = LitPointLight(position = ursina.Vec3(0,scale,0), color = ursina.color.colors["white"], range = 40*scale, intensity = 1)
	lightsource_centered = LitPointLight(position = ursina.Vec3(0,2*scale,0), color = ursina.color.colors["white"], range = 80*scale, intensity = 2)
	skyboxTexture = ursina.Texture("textures/skybox.jpg")

	#skybox
	skybox = ursina.Sky(model = "sphere", double_sided = True, texture = skyboxTexture, rotation = (0, 90, 0))

	return tiles

def generate_island_tiles(position, scale, radius, grid_points, terrain_amplification, terrain_scale):
	# noiseGenerator.regen()
	origin_x, origin_z = position
	tiles=[]
	for row in grid_points:
		for x,z in row:
			position=((origin_x+x*scale),0,(origin_z+z*scale))
			p = calc_hexagon_verts_from_center_point((x, 0, z), scale, (scale+.5)*radius, terrain_amplification=terrain_amplification,terrain_scale=terrain_scale)
			t = Tile((x,z), position, p, ursina.color.colors[get_resource_color(pick_random_resource_type())])
			tiles.append(t)
	return tiles

def generate_tile_grid(position, scale, radius, grid_points, terrain_amplification, terrain_scale):
	origin_x, origin_z = position
	tiles=[]
	for row in grid_points:
		for x,z in row:
			position=((origin_x+x*scale),0,(origin_z+z*scale))
			p = calc_hexagon_outline_verts_from_center_point((x, 0, z), scale, (scale+.5)*radius, terrain_amplification=terrain_amplification,terrain_scale=terrain_scale)
			t = ursina.Entity(position=position, model=ursina.Mesh(vertices=(p[0]), triangles=p[1], mode='line', thickness=int(3*min(1,scale))), color=ursina.color.rgb(0,0,0), y = 0.02)
			tiles.append(t)
	return tiles

def generate_island_shores(position, scale, radius, grid_points, terrain_amplification, terrain_scale):
	#Calculate shore
	#Systematically generate the hexagons we need
	#and then drop their outermost points to
	#create a "bank"
	origin_x, origin_z = position
	shoretiles = []
	row_index = 0
	for row in grid_points:
		index = 0
		for x,z in row:
			position=((origin_x+x*scale),0,(origin_z+z*scale))
			hex_verts, tris = calc_hexagon_verts_from_center_point((x, 0, z), scale, (scale+.5)*radius, terrain_amplification=terrain_amplification,terrain_scale=terrain_scale)
			needed = False #If the hexagon is one of the needed ones
			verts_to_cliffdrop = set()
			if row_index == radius or row_index == radius+1: verts_to_cliffdrop.update({1}) #Only flag needed if on either end, will flag below
			if row_index == 0:#If in the top row
				needed=True
				verts_to_cliffdrop.update({6,1,2})
			if index == 0:
				needed=True
				if row_index < radius: verts_to_cliffdrop.update({5,6,1})#Top half
				elif row_index == radius: verts_to_cliffdrop.update({5,6})#Top half
				elif row_index > radius: verts_to_cliffdrop.update({4,5,6})#Bottom Half
			elif index == len(row)-1:#If in the last column
				needed=True
				if row_index < radius: verts_to_cliffdrop.update({1,2,3})#Top half
				elif row_index == radius: verts_to_cliffdrop.update({2,3})#Top half
				elif row_index > radius: verts_to_cliffdrop.update({2,3,4})#Bottom Half
			if row_index == len(grid_points)-1:#If in the bottom row
				needed=True
				verts_to_cliffdrop.update({3,4,5})
			if needed:
				for v in verts_to_cliffdrop:
					hex_verts[v][1] =-settings.shore_drop*scale
				hex_verts[0][1] =-0.5*settings.shore_drop #Drop center of hexagon half way for slope
				shoretiles.append(ShoreTile(position, (hex_verts,((0,6,5),(0,5,4),(0,4,3),(0,3,2),(0,2,1),(0,1,6)))))
			index += 1
		row_index += 1
	return shoretiles

def generate_water(position, scale, radius):
	x,z=position
	rscale = 2*radius*scale
	water_tiles = []
	for _x in range(-2,3):
		for _z in range(-2,3):
			water_tiles.append(
				LitObject(
					position=(
						_x*rscale*settings.water_scale+x,
						-0.25*scale,
						_z*rscale*settings.water_scale+z,
						),
					model='quad',
					rotation=(90,0,90),
					scale=rscale*settings.water_scale,
					color=ursina.color.rgb(60,100,240),
					water=True
				)
			)
	return water_tiles

def generate_lighting(scale):
	lighting = [
		LitPointLight(position = ursina.Vec3(0,scale,0), color = ursina.color.colors["white"], range = 40*scale, intensity = 2),
		LitPointLight(position = ursina.Vec3(0,2*scale,0), color = ursina.color.colors["white"], range = 80*scale, intensity = 3)
	]
	return lighting

def generate_map(position,scale,radius,terrain_amplification,terrain_scale):
	center_points = calc_hex_grid_points_from_radius(radius+1)
	island_center_points = calc_hex_grid_points_from_radius(radius)
	tiles = generate_island_tiles(position,scale,radius,island_center_points,terrain_amplification,terrain_scale)
	grid = generate_tile_grid(position,scale,radius,island_center_points,terrain_amplification,terrain_scale)
	shore = generate_island_shores(position,scale,radius, center_points,terrain_amplification,terrain_scale)
	water = generate_water(position,scale,radius)
	lighting = generate_lighting(scale)
	skybox = ursina.Sky(model = "sphere", double_sided = True, texture = ursina.Texture("textures/skybox.jpg"), rotation = (0, 90, 0))
	return tiles, grid, shore, water, lighting, [skybox]















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
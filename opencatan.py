import math, json, random
import numpy as np
import ursina

def get_random_color():
	return ursina.color.rgb(random.randint(0,255),random.randint(0,255),random.randint(0,255))

sqrt3 = math.sqrt(3)
def calc_hexagon_verts_from_center_point(x_offset, y_offset, x,y,r,z=0):
	x*=r #Scale
	y*=r
	a = (x, r + y, z)
	b = (sqrt3*r*0.5 + x, r*0.5 + y, z)
	c = (sqrt3*r*0.5 + x, -r*0.5 + y, z)
	d = (x, -r + y, z)
	e = (-sqrt3*r*0.5 + x, -r*0.5 + y, z)
	f = (-sqrt3*r*0.5 + x, r*0.5 + y, z)
	verts = [
		a,b,c,d,e,f
	]
	verts = [(v[0]+x_offset,v[1]+y_offset,0) for v in verts]
	tris = ((0,1,2,3,4,5,0),)
	return (verts, tris)

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
			x_offset = (row_num * (sqrt3 - sqrt3/2))
		else:
			x_offset = -((row_num - 2 * r) * (sqrt3 - sqrt3/2))
		x_offset -= (sqrt3) * 1.5 * r
		y_offset = ((r - row_num + 1) * 1.5) - 1.5
		for h in range(num_hexagons):
			column.append(((x_offset + (sqrt3*h)), y_offset))

		rows.append(column)
	return rows

def draw_honeycomb(position,radius,scale):
	origin_x, origin_y = position
	points = calc_hex_grid_points_from_radius(radius)
	tiles=[]
	for row in points:
		for x,y in row:
			points = calc_hexagon_verts_from_center_point(origin_x, origin_y, x, y, scale, 0)
			tiles.append(Tile(points, get_random_color()))

class Tile(ursina.Entity):
	def __init__(self, points, color):
		verts, tris = points
		ursina.Entity.__init__(self, model=ursina.Mesh(vertices=verts, triangles=tris, mode='line', thickness=1), color=color, z=-1)
		
app = ursina.Ursina()

center = ursina.Entity(model='sphere', color=ursina.color.orange, scale=0.1, origin = (0,0), y = 0)



#This is the actual draw function
POSX = 0
POSY = 0
RADIUS = 25
SCALE = 0.1

draw_honeycomb((POSX, POSY), RADIUS, SCALE)

app.run()
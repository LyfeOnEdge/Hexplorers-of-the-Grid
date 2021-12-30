import ursina

# #Temp tile with a cricle for testing
# class Tile(ursina.Button):
# 	def __init__(self, tile_id, scale, position, points, color):
# 		self.id = tile_id
# 		self.verts, self.tris = points
# 		self.mesh = ursina.Mesh(vertices=self.verts, triangles=self.tris, mode='triangle', thickness=2)
# 		ursina.Button.__init__(
# 			self,
# 			parent=ursina.scene,
# 			model="circle",
# 			color=color,
# 			texture="white_cube",
# 			origin=0,
# 			position=position,
# 			rotation=(90,0,90),
# 			scale = scale,
# 			collider=self.mesh,
# 		)
# 		self.outline = None

# 	def input(self, key):
# 		if self.hovered:
# 			if key == 'left mouse down':
# 				self.color = ursina.rgb(0,0,255)
# 				self.animate_color(self.color, duration=.1, interrupt='finish')

# 			# if key == 'right mouse down':
# 			#     destroy(self)



class Tile(ursina.Button):
	def __init__(self,parent, tile_id, scale, position, points, color):
		self.id = tile_id
		self.scale = scale
		self.verts, self.tris = points
		self.mesh = ursina.Mesh(vertices=self.verts, triangles=self.tris, mode='triangle', thickness=2)
		ursina.Button.__init__(
			self,
			parent=parent,
			model=self.mesh,
			color=color,
			texture="white_cube",
			origin=0,
			position=position,
			# collider='circle',
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
	def __init__(self,parent, position, points):
		self.verts, self.tris = points
		ursina.Entity.__init__(
			self,
			parent=parent,
			model=ursina.Mesh(vertices=self.verts, triangles=self.tris, mode='ngon', thickness=2),
			color=ursina.rgb(220,190,140),
			# texture="white_cube",
			origin=0,
			position=position,
		)
		self.outline = None
		# self.texture = ursina.Texture("textures/sand.png")

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
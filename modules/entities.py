import ursina
import numpy as np
from .settings import settings

class HeightMesh(ursina.Mesh): #Based on terrain.py found in Ursina, adopted to work with a heightmap array rather than an image
	def __init__(self, heightmap):
		self.heightmap = heightmap
		w, h = len(self.heightmap), len(self.heightmap[0])
		self.w, self.h = w, h
		self.heightmap = np.swapaxes(np.flip(self.heightmap, axis=0), 0, 1)
		self.vertices, self.triangles = list(), list()
		self.uvs = list()
		self.normals = list()
		min_dim=min(w,h)
		# create the plane
		i = 0
		for z in range(h+1):
			for x in range(w+1):
				y = self.heightmap[x-(x==w)][z-(z==h)] # do -1 if the coordinate is not in range
				self.vertices.append(ursina.Vec3((x/min_dim), y, (z/min_dim)))
				self.uvs.append((x/w, z/h))
				if x > 0 and z > 0:
					self.triangles.append((i, i-1, i-w-2, i-w-1))
				# normals
				if x > 0 and z > 0 and x < w-1 and z < h-1:
					rl =  self.heightmap[x+1][z] - self.heightmap[x-1][z]
					fb =  self.heightmap[x][z+1] - self.heightmap[x][z-1]
					self.normals.append(ursina.Vec3(rl, 1, fb).normalized())
				else:
					self.normals.append(ursina.Vec3(0,1,0))
				i += 1
		super().__init__(vertices=self.vertices, triangles=self.triangles, uvs=self.uvs, normals=self.normals)

class LandMasses(ursina.Entity):
	def __init__(self, heightmap, scale, texture, **kwargs):
		self.heightmap = heightmap
		ursina.Entity.__init__(
			self,
			position=(-0.5*scale,-0.0625*scale,-0.5*scale),
			# texture_offset=(0.5,0.5,0.5),
			scale=scale,
			scale_y=0.25*scale,
			texture = texture,
			model=HeightMesh(heightmap),
			**kwargs,
			)


class BoardTile(ursina.Entity):
	def __init__(self,parent,position, points, color):
		self.verts, self.tris = points, (0,6,5,0,5,4,0,4,3,0,3,2,0,2,1,0,1,6)
		self.mesh = ursina.Mesh(vertices=self.verts, triangles=self.tris, mode='triangle', thickness=2)
		ursina.Entity.__init__(
			self,
			parent=parent,
			model=self.mesh,
			color=color,
			origin=0,
			position=(position[0],0,position[1]),
		)
		self.outline = None

	def input(self, key):
		if self.hovered:
			if key == 'left mouse down':
				self.color = ursina.rgb(0,0,255)
				self.animate_color(self.color, duration=.1, interrupt='finish')

class ShoreTile(ursina.Entity):
	def __init__(self,parent, position, points):
		self.verts, self.tris = points
		ursina.Entity.__init__(
			self,
			parent=parent,
			model=ursina.Mesh(vertices=self.verts, triangles=self.tris, mode='ngon', thickness=2),
			color=ursina.rgb(220,190,140),
			origin=0,
			position=position,
		)
		self.outline = None


from .catanengine import TileMixin, EdgeMixin, NodeMixin


class BoardElement(ursina.Button):
	def __init__(self, game, center, **kwargs):
		ursina.Button.__init__(
			self,
			parent=ursina.scene,
			model="sphere",
			position=(center[0],1.05,center[1]),
			scale=0.1,
			on_click = self.on_click_action,
			*kwargs
		)
	def on_click_action(self):
		pass

	def activate(self):
		self.blink(
			value=ursina.color.rgb(settings.activated_color[0],settings.activated_color[1],settings.activated_color[2]),
			duration=1,
			delay=0,
			curve=ursina.curve.in_expo_boomerang,
			interrupt='finish'
		)  

class Edge(BoardElement, EdgeMixin):
	def __init__(self, game, center, verts, node_a, node_b):
		BoardElement.__init__(self, game, center)
		EdgeMixin.__init__(self, game, node_a, node_b)
		self.color = ursina.rgb(255,0,0)
	def on_click_action(self):
		self.game.select(self)
	def activate(self):
		BoardElement.activate(self)
		EdgeMixin.activate(self)

class Node(BoardElement, NodeMixin):
	def __init__(self, game, center, tile_edges = [], tile_nodes = [], tiles = []):
		BoardElement.__init__(self, game, center)
		NodeMixin.__init__(self,game,tile_edges=tile_edges,tile_nodes=tile_nodes,tiles=tiles)
		self.color = ursina.rgb(0,0,255)
	def on_click_action(self):
		self.game.select(self)
	def activate(self):
		BoardElement.activate(self)
		NodeMixin.activate(self)

class Tile(BoardElement, TileMixin):
	def __init__(self, game, center, tile_edges, tile_nodes, value = 0):
		BoardElement.__init__(self,game, (center[0],center[2]))
		TileMixin.__init__(self,game, tile_edges, tile_nodes, value)
		self.color = ursina.rgb(255,0,255)
	def on_click_action(self):
		self.game.select(self)
	def activate(self):
		BoardElement.activate(self)
		TileMixin.activate(self)
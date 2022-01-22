import ursina
import numpy as np
from .settings import settings
from HexplorationEngine import TileMixin, EdgeMixin, NodeMixin, WaterTileMixin
from .UrsinaLighting import LitObject

class HeightMesh(ursina.Mesh): #Based on terrain.py found in Ursina, adopted to work with a numpy array directly rather than an image
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
			scale=scale,
			scale_y=0.25*scale,
			texture = texture,
			model=HeightMesh(heightmap),
			add_to_scene_entities=False,
			eternal=True,
			**kwargs,
			)

class ShoreTile(LitObject):
	def __init__(self,parent, position, points):
		self.verts, self.tris = points
		LitObject.__init__(
			self,
			parent=parent,
			model=ursina.Mesh(vertices=self.verts, triangles=self.tris, mode='ngon', thickness=2),
			color=ursina.rgb(*settings.island_skirt_color),
			origin=0,
			position=(
				position[0]*settings.board_scale,
				settings.island_height_above_water*settings.board_scale,
				position[2]*settings.board_scale
			),
			scale=settings.board_scale,
			texture="textures/sand.png",
			ambientStrength=0.5,
			smoothness = 2,
			cubemapIntensity=0.15,
			water=True
		)
		self.outline = None


class BoardElement(ursina.Button):
	def __init__(self, game, center, **kwargs):
		self.center = center
		ursina.Button.__init__(
			self,
			parent=ursina.scene,
			model="sphere",
			position=(center[0]*settings.board_scale,1.05*settings.board_scale*settings.island_height_above_water,center[1]*settings.board_scale),
			scale=settings.board_selector_scale,
			on_click = self.on_click_action,
			eternal = True,
			*kwargs
		)
		self.enabled = False
	def on_click_action(self):
		pass

	def activate(self):
		self.blink(
			value=ursina.color.rgb(*settings.activated_color),
			duration=1,
			delay=0,
			curve=ursina.curve.in_expo_boomerang,
			interrupt='finish'
		)  

class Edge(BoardElement, EdgeMixin):
	def __init__(self, game, center, verts, node_a, node_b, flip_port=False):
		BoardElement.__init__(self, game, center)
		EdgeMixin.__init__(self, game, node_a, node_b)
		self.color = ursina.rgb(255,0,0)
		self.flip_port = flip_port
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
	def set_owner(self, *args, **kwargs):
		self.scale *= 2
		NodeMixin.set_owner(self, *args, **kwargs)		

class Tile(BoardElement, TileMixin):
	def __init__(self, game, center, tile_edges, tile_nodes, map_center=False,**kwargs):
		BoardElement.__init__(self,game, (center[0],center[2]),**kwargs)
		TileMixin.__init__(self,game, tile_edges, tile_nodes, map_center = map_center)
		self.color = ursina.rgb(255,0,255)
		self.tile_entity = None #To hold an entity for rendering
		
	def on_click_action(self):
		self.game.select(self)
	def activate(self):
		BoardElement.activate(self)
		TileMixin.activate(self)

class WaterTile(BoardElement, WaterTileMixin):
	def __init__(self, game, center, tile_edges, tile_nodes, flip_port=False, **kwargs):
		BoardElement.__init__(self,game, (center[0],center[2]),**kwargs)
		TileMixin.__init__(self,game, tile_edges, tile_nodes)
		self.tile_entity = None #To hold an entity for rendering
		if flip_port:
			for e in tile_edges:
				e.flip_port = True

class Divider(ursina.Entity):
	def __init__(self, *args, **kwargs):
		ursina.Entity.__init__(
			self,
			*args,
			model='quad',
			**kwargs,
			color = ursina.color.white,
			add_to_scene_entities=False,
		 )
		self.z-=0.7
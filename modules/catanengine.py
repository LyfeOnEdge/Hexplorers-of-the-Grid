import random
DICE = [2,3,3,4,4,4,5,5,5,5,6,6,6,6,6,7,7,7,7,7,7,8,8,8,8,8,9,9,9,9,10,10,10,11,11,12]
#PHASES
PHASE_SETUP	= -1
PHASE_DEAL	= 0
PHASE_BUILD	= 1

#Resource Types
RESOURCE_SHEEP	= 0
RESOURCE_WHEAT	= 1
RESOURCE_ORE	= 2
RESOURCE_WOOD	= 3
RESOURCE_BRICK	= 4

RESOURCES = [
	RESOURCE_SHEEP,
	RESOURCE_WHEAT,
	RESOURCE_ORE,
	RESOURCE_WOOD,
	RESOURCE_BRICK,
]

RESOURCE_MAP_INT_TO_NAME = {
	RESOURCE_SHEEP : "Sheep",
	RESOURCE_WHEAT : "Wheat",
	RESOURCE_ORE : "Ore",
	RESOURCE_WOOD : "Wood",
	RESOURCE_BRICK : "Brick",
}

RESOURCE_MAP_INT_TO_COLOR = {
	RESOURCE_SHEEP : "white",
	RESOURCE_WHEAT : "yellow",
	RESOURCE_ORE : "gray",
	RESOURCE_WOOD : "green",
	RESOURCE_BRICK : "orange",
}

RESOURCE_MAP_NAME_TO_INT = {RESOURCE_MAP_INT_TO_NAME[k]:k for k in RESOURCE_MAP_INT_TO_NAME.keys()}

PLAYER_COLOR_CHOICES = [
	"Red",
	"Green",
	"Blue",
	"Yellow",
	"Orange",
	"Brown",
	"Pink",
	"Black",
	"Gray",
	"White",
	"Lime",
	"Indigo",
	"Purple",
	"Deeppink",
	"Dodgerblue",
	"Lightgreen",
	"Crimson"
]

def get_dice_roll(): return random.choice(DICE)
def pick_random_resource_type(): return random.choice(RESOURCES)
def get_resource_color(resource): return RESOURCE_MAP_INT_TO_COLOR[resource]

class ResourceCard:
	def __init__(self):
		pass

class Player:
	def __init__(self):
		self.board_pieces = None
		self.inventory = {
			RESOURCE_SHEEP	:0,
			RESOURCE_ORE	:0,
			RESOURCE_WOOD	:0,
			RESOURCE_BRICK	:0,
			RESOURCE_WHEAT	:0,
		}
		self.owned_edges, self.owned_nodes = [], []
		self.resource_cards = []

class Game:
	def __init__(self):
		self.turn, self.phase = 0, 0
		self.players = []
		self.tiles, self.edges, self.nodes = None, None, None

		self.started = False
		self.phase = PHASE_SETUP
		self.awaiting_selection = False
		self.selection = None
		self.placement_order = []
		self.multiple_placement_flag = False

	def create(self, tiles, edges, nodes):
		self.tiles, self.edges, self.nodes = tiles, edges, nodes

	def select(self, entity):
		self.selection = entity
		# entity.activate()
		# entity.activate_neighbors()

	def start(self, players):
		self.started = True
		self.players = players
		self.turn_order = []
		players_to_chose_from = self.players.copy()
		for i in range(len(self.players)): #get turn order and placement order
			c = random.choice(players_to_chose_from)
			players_to_chose_from.remove(c)
			self.turn_order.append(c)
		#Get initial placement turn order
		self.placement_order = self.turn_order.copy()
		self.placement_order.extend(reversed(self.placement_order))

		for t in self.tiles: t.enabled = False
		for e in self.edges: e.enabled = False
		for n in self.nodes: n.enabled = False

	def get_player_victory_point_count(self, player):
		pass

	def find_player_with_longest_road(self):
		pass

	def gameloop(self):
		#Skip if still waiting for selection
		if self.awaiting_selection:
			if not self.selection:
				return
		
		if self.phase == PHASE_SETUP:
			# print("In setup phase")
			if self.placement_order: #List is depleted as it is used
				current_player = self.placement_order[0]
				if self.selection: #Player has made selection
					if not self.multiple_placement_flag: #Settlement has been placed
						print(f"{current_player} has placed setup settlement")
						self.selection.set_owner(current_player)
						self.multiple_placement_flag = True
						self.show_available_edges(current_player)
						self.awaiting_selection = True
						self.selection = None
					else: #Road has been placed, advance to next player
						print(f"{current_player} has placed setup road")
						self.selection.set_owner(current_player)
						self.awaiting_selection = False #Reset
						self.selection = None #Reset
						self.multiple_placement_flag = False #Reset
						self.placement_order.pop(0)
						if not self.placement_order: #Nobody left
							print("Advancing to deal phase")
							self.phase == PHASE_DEAL
							self.hide_all_points()
				else:
					print(f"Waiting for {current_player} to select settlement location")
					self.show_available_nodes(current_player)
					self.awaiting_selection = True
					self.selection = None

		elif self.phase == PHASE_DEAL:
			print("Reached phase deal")
		elif self.phase == PHASE_BUILD:
			pass
	def show_available_edges(self, player):
		self.hide_all_points()

		available = []

		for n in player.owned_nodes: #if a node doesn't have any roads it must have one added now
			if not any((e.owner is player for e in n.neighbor_edges)):
				for e in n.neighbor_edges:
					if not e.owner:
						e.enabled = True
						available.append(e)
				return available
		
		for n in player.owned_nodes:
			for e in n.neighbor_edges:
				if not e.owner:
					available.append(e)
		for e in player.owned_edges:
			for _e in e.neighbor_edges:
				if not _e.owner:
					available.append(_e)
		for e in available: e.enabled = True
		return available

	def show_available_nodes(self, player, require_connected = False):
		self.hide_all_points()
		if not require_connected:
			for n in self.nodes:
				if not n.owner and not any(nn.owner for nn in n.neighbor_nodes):
					n.enabled = True
				else:
					n.enabled = False
		else: #Find available nodes
			available = []
			for n in player.owned_nodes():
				for e in n.neighbor_edges:
					if e.owner is player:
						for e2 in e.neighbor_edges:
							if e2 not in n.neighbor_edges:
								if e2.owner is player:
									for e2n in e2.neighbor_nodes:
										if e2n not in n.neighbor_nodes:
											if e2n not in available:
												available.append(e2n)
			for a in available:
				available.show()


	def show_all_nodes(self):
		for n in self.nodes: n.enabled = True
	def hide_all_nodes(self):
		for n in self.nodes: n.enabled = False
	def show_all_tiles(self):
		for t in self.tiles: t.enabled = True
	def hide_all_tiles(self):
		for t in self.tiles: t.enabled = False
	def show_all_edges(self):
		for e in self.edges: e.enabled = True
	def hide_all_edges(self):
		for e in self.edges: e.enabled = False
	def show_all_points(self):
		for n in self.nodes: n.enabled = True
		for t in self.tiles: t.enabled = True
		for e in self.edges: e.enabled = True
	def hide_all_points(self):
		for n in self.nodes: n.enabled = False
		for t in self.tiles: t.enabled = False
		for e in self.edges: e.enabled = False

class BoardElement:
	def __init__(self, game):
		self.game = game
		self.neighbor_edges, self.neighbor_tiles, self.neighbor_nodes = set(), set(), set()
		self.owner = None
	def add_neighbor_tile(self,t):self.neighbor_tiles.update({t})
	def add_neighbor_edge(self,e):self.neighbor_edges.update({e})
	def add_neighbor_node(self,n):self.neighbor_nodes.update({n})
	def select(self): self.game.select(self)
	def activate(self): pass #To be redefined in mixed object
	def activate_neighbors(self, exclude = []):
		print(f"Activating {type(self)} - {self}")
		for t in self.neighbor_tiles: t.activate()
		for e in self.neighbor_edges: e.activate()
		for n in self.neighbor_nodes: n.activate()

class TileMixin(BoardElement):
	def __init__(self, game, tile_edges, tile_nodes, value = 0):
		super().__init__(game)
		for e in tile_edges: self.add_neighbor_edge(e)
		for n in tile_nodes: self.add_neighbor_node(e)
		self.value = value

	def add_neighbor_tile(self,t):
		self.neighbor_tiles.update({t})
		if not self in t.neighbor_tiles: t.add_neighbor_tile(self)
	def add_neighbor_edge(self,e):
		self.neighbor_edges.update({e})
		if not self in e.neighbor_tiles: e.add_neighbor_tile(self)
	def add_neighbor_node(self,n):
		self.neighbor_nodes.update({n})
		if not self in n.neighbor_tiles: n.add_neighbor_tile(self)

class EdgeMixin(BoardElement):
	def __init__(self, game, node_a, node_b):
		super().__init__(game)
		self.add_neighbor_node(node_a)
		self.add_neighbor_node(node_b)
		self.node_a, self.node_b = node_a, node_b
		node_a.add_neighbor_node(node_b) #B adds A back automatically
	def add_neighbor_edge(self, e):
		self.neighbor_edges.update({e})
		if not self in e.neighbor_edges:
			e.add_neighbor_edge(self)
	def add_neighbor_node(self,n):
		self.neighbor_nodes.update({n})
		if not self in n.neighbor_edges:
			n.add_neighbor_edge(self)
	def add_neighbor_tile(self,t):
		self.neighbor_tiles.update({t})
		if not self in t.neighbor_edges:
			t.add_neighbor_edge(self)
		t.add_neighbor_node(self.node_a)
		t.add_neighbor_node(self.node_b)
	def set_owner(self, owner):
		if self.owner:
			raise ValueError(f"Attempted to set owner on {type(self)} that already has an owner - {owner}")
		self.owner = owner
		self.owner.owned_edges.append(self)

class NodeMixin(BoardElement):
	def __init__(self, game, tile_edges = [], tile_nodes = [], tiles = [], owner=None):
		super().__init__(game)
		for t in tiles: self.add_neighbor_tile(t)
		for e in tile_edges: self.add_neighbor_edge(e)
		for n in tile_nodes: self.add_neighbor_nodes(n)
		self.upgraded = False

	def upgrade(self):
		if not self.owner: raise ValueError("Attempted upgrade on node with no owner")
		if self.upgraded: raise ValueError("Attempted upgrade on previously upgraded node")
		self.upgraded = True 

	def add_neighbor_node(self,n):
		self.neighbor_nodes.update({n})
		if not self in n.neighbor_nodes:
			n.add_neighbor_node(self)
	def set_owner(self, owner):
		if self.owner: raise ValueError(f"Attempted to set owner on {type(self)} that already has an owner")
		self.owner = owner
		self.owner.owned_nodes.append(self)
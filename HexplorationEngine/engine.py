import time
from modules.settings import settings
from .constants import * 
import ursina

import random
DICE = [2,3,3,4,4,4,5,5,5,5,6,6,6,6,6,7,7,7,7,7,7,8,8,8,8,8,9,9,9,9,10,10,10,11,11,12]
CHIPS = []
for d in DICE:
	if not d == 7:
		CHIPS.append(d)









def get_dice_roll():return random.randint(0,7), random.randint(0,7) #Simulate 2xD6 Roll
def get_chip_number(): return random.choice(CHIPS)

def get_resource_color(resource): return RESOURCE_MAP_INT_TO_COLOR[resource]




class Exchanger: #Object to get lowet 
	def __init__(self, exchange_rates=DEFAULT_EXCHANGE_RATES):
		self.exchange_rates = exchange_rates
	def get_exchange_rates(self, player):
		rates = {}
		for r in RESOURCES:
			if player.exchange_rates.get(r):
				rates[r] = min(player.exchange_rates.get(r), self.exchange_rates.get(r) or self.exchange_rates.get("*"))
			else:
				rates[r] = self.exchange_rates.get(r) or self.exchange_rates.get("*")
		return rates

# Uncapped settlements
# Uncapped Cities
# Uncapped Roads 
# Infinite Board
# Change minimum card count to trade
# Trade some tiles pay out different amounts
# Tiles that get rolled less frequently pay out more
#
#
# DEFAULT_RULES = {
# 	"robber_enabled":True,
# 	"desert_enabled":True,
# 	"board_radius":4,
# 	"gold_enabled":False,
# 	"gold_rush_enabled":False,
# }

# class Ruleset:
# 	def __init__(self, *args, **kwargs):
# 		self.robber_enabled = True
# 		self.rules = kwargs

# class DefaultRules(Ruleset):
# 	def __init__(self, *args, **kwargs):
# 		rules = {
# 			"robber_enabled":True,
# 			"desert_enabled":True,
# 		}
# 		Ruleset.__init__(self, *args, **kwargs)

# class HexplorationRules(Ruleset):
# 	def __init__(self, *args, **kwargs):
# 		rules = {
# 			"robber_enabled":False,
# 			"desert_enabled":False,
# 			"board_radius":4,
# 			"gold_enabled":True,
# 			"gold_rush_enabled":True,
# 		}
# 		Ruleset.__init__(self, *args, **kwargs)

class Player:
	def __init__(self):
		self.board_pieces = None
		self.inventory = {
			RESOURCE_SHEEP	:10,
			RESOURCE_ORE	:10,
			RESOURCE_WOOD	:10,
			RESOURCE_BRICK	:10,
			RESOURCE_WHEAT	:10,
		}
		self.owned_edges, self.owned_nodes = [], []
		self.resource_cards = []
		self.color = (0,0,0)
		self.placed_first_settlement = False
		self.exchange_rates = {}

class redPlayer(Player):
	def __init__(self):
		Player.__init__(self)
		r,g,b = settings.player_color_red
		self.color = ursina.rgb(r,g,b)
class bluePlayer(Player):
	def __init__(self):
		Player.__init__(self)
		r,g,b = settings.player_color_blue
		self.color = ursina.rgb(r,g,b)
class greenPlayer(Player):
	def __init__(self):
		Player.__init__(self)
		r,g,b = settings.player_color_green
		self.color = ursina.rgb(r,g,b)
class yellowPlayer(Player):
	def __init__(self):
		Player.__init__(self)
		r,g,b = settings.player_color_yellow
		self.color = ursina.rgb(r,g,b)
class purplePlayer(Player):
	def __init__(self):
		Player.__init__(self)
		r,g,b = settings.player_color_purple
		self.color = ursina.rgb(r,g,b)
class pinkPlayer(Player):
	def __init__(self):
		Player.__init__(self)
		r,g,b = settings.player_color_pink
		self.color = ursina.rgb(r,g,b)
class brownPlayer(Player):
	def __init__(self):
		Player.__init__(self)
		r,g,b = settings.player_color_brown
		self.color = ursina.rgb(r,g,b)
class grayPlayer(Player):
	def __init__(self):
		Player.__init__(self)
		r,g,b = settings.player_color_gray
		self.color = ursina.rgb(r,g,b)

PLAYER_FRIENDLY_NAMES = {
	redPlayer	: "Red Player",
	bluePlayer	: "Blue Player",
	greenPlayer	: "Green Player",
	yellowPlayer: "Yellow Player",
	purplePlayer: "Purple Player",
	pinkPlayer	: "Pink Player",
	brownPlayer	: "Brown Player",
	grayPlayer	: "Gray Player",
}

def get_player_friendly_name(player): return PLAYER_FRIENDLY_NAMES[type(player)]

def get_available_upgrades(player):
	"""Check if player is able to upgrade a settlement"""
	for n in player.owned_nodes:
		if not n.upgraded:
			yield n

def get_available_nodes(nodes, player, require_connected=True):
	"""Get available settlement nodes for given player"""
	available = []
	if not require_connected:
		for n in nodes:
			if not n.owner and not any(nn.owner for nn in n.neighbor_nodes):
				yield n
	else: #Find available nodes
		for e in player.owned_edges:
			for n in e.neighbor_nodes:
				if not n.owner:
					if not any(nn.owner for nn in n.neighbor_nodes):
						available.append(n)
						yield n #Node is available

def get_available_edges(player):
	"""Get available edges for given player"""
	available = []
	for n in player.owned_nodes: #if a node doesn't have any roads it must have one added now
		if not any((e.owner is player for e in n.neighbor_edges)):
			for e in n.neighbor_edges:
				if not e.owner:
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
	return available

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
		self.current_player = None
		self.animation = False
		self.animation_start = None
		self.dice = None
		self.dealt = False
		self.round = 0
		self.limited_tile_pool = False

		self.build_flag = None

		self.ui_needs_update = True

		self.recipes = RECIPES

	def set_current_message(self, current_message):
		print(f"USERMESSAGE - {current_message}")
		self.current_message = current_message

	def create(self, tiles, edges, nodes):
		self.tiles, self.edges, self.nodes = tiles, edges, nodes

	def select(self, entity):
		self.selection = entity
		# entity.activate()
		# entity.activate_neighbors()

	def start(self, players):
		self.started = True
		turn_order = []
		players_to_chose_from = players.copy()
		for i in range(len(players)): #get turn order and placement order
			c = random.choice(players_to_chose_from)
			players_to_chose_from.remove(c)
			turn_order.append(c)
		self.players = turn_order
		#Get initial placement turn order
		self.placement_order = turn_order.copy()
		self.placement_order.extend(reversed(self.placement_order))
		self.current_player = self.placement_order[0]

		for t in self.tiles: t.enabled = False
		for e in self.edges: e.enabled = False
		for n in self.nodes: n.enabled = False

	def get_rendered_objects(self):
		rendered = []
		for e in self.tiles:
			if e.owner:
				rendered.append(e)
		for e in self.edges:
			if e.owner:
				rendered.append(e)
		for e in self.nodes:
			if e.owner:
				rendered.append(e)
		return rendered

	def do_payouts(self):
		print(f"Doing payout for {self.dice}")
		self.ui_needs_update=True
		roll_value = sum(self.dice)
		for t in self.tiles:
			if not t.has_robber:
				if t.value == roll_value:
					for n in t.neighbor_nodes:
						if n.owner:
							print(f"{1 + n.upgraded} X {RESOURCE_MAP_INT_TO_NAME[t.resource_type]} for {get_player_friendly_name(n.owner)}")
							n.owner.inventory[t.resource_type] += 1 + n.upgraded

	def get_player_victory_point_count(self, player):
		pass

	def find_player_with_longest_road(self):
		pass

	def gameloop(self):
		"""Main Gameloop"""
		"""Must always return a list of game pieces for the renderer to render"""
		if self.awaiting_selection: #Skip if still waiting for user selection
			if not self.selection:
				return self.get_rendered_objects()		
		############
		#SETUP PHASE
		############
		if self.phase == PHASE_SETUP:
			# print("In setup phase")
			if self.placement_order: #List is depleted as it is used
				self.current_player = self.placement_order[0]
				if self.selection: #Player has made selection
					if not self.multiple_placement_flag: #Settlement has been placed
						if not self.current_player.placed_first_settlement:
							self.current_player.placed_first_settlement = True
							for t in self.selection.neighbor_tiles:
								self.current_player.inventory[t.resource_type] += 1

						self.set_current_message(f"{get_player_friendly_name(self.current_player)} has placed setup settlement")
						self.selection.set_owner(self.current_player)
						self.multiple_placement_flag = True
						self.show_current_player_available_edges()
						self.awaiting_selection = True
						self.selection = None
						self.set_current_message(f"Waiting for {get_player_friendly_name(self.current_player)} to select road location")
					else: #Road has been placed, advance to next player
						self.set_current_message(f"{get_player_friendly_name(self.current_player)} has placed setup road")
						self.selection.set_owner(self.current_player)
						self.awaiting_selection = False #Reset
						self.selection = None #Reset
						self.multiple_placement_flag = False #Reset
						self.placement_order.pop(0)
						if not self.placement_order: #Nobody left
							self.set_current_message("Advancing to deal phase")
							self.phase = PHASE_ROLL
							self.hide_all_points()
							self.selection  = None
				else:
					s_o_r = "road" if self.multiple_placement_flag else "settlement"
					self.set_current_message(f"Waiting for {get_player_friendly_name(self.current_player)} to select {s_o_r} location")
					self.show_current_player_available_nodes(require_connected=False)
					self.awaiting_selection = True
					self.selection = None
				self.ui_needs_update=True

		############
		#ROLL PHASE
		############
		elif self.phase == PHASE_ROLL:
			if self.animation:
				if self.animation_start + 0.25 < time.time():
					self.animation = False
					self.animation_start = None
				else:
					return self.get_rendered_objects()

			if not self.dice:
				self.set_current_message(f"Rolling dice for {get_player_friendly_name(self.current_player)}'s turn")
				self.dice = get_dice_roll() #Must set before doing payouts
				
				#Handle dice roll animation elements here
				self.animation = True
				self.animation_start = time.time()
				self.ui_needs_update=True
			else:
				self.set_current_message(f"Finished roll for {get_player_friendly_name(self.current_player)}'s turn.")
				self.set_current_message("Advancing to deal phase")
				self.phase = PHASE_DEAL
				self.ui_needs_update=True

		############
		#DEAL PHASE
		############
		elif self.phase == PHASE_DEAL:
			if self.animation:
				if self.animation_start + 0.25 < time.time():
					self.animation = False
					self.animation_start = None
				else:
					return self.get_rendered_objects()

			if not self.dealt:
				self.set_current_message(f"Dealing cards for {get_player_friendly_name(self.current_player)}'s turn")
				#Handle payouts and generate animation elements here
				self.animation = True
				self.animation_start = time.time()
				self.dealt = True
				self.do_payouts()
				self.ui_needs_update=True

			else:
				self.set_current_message(f"Finished deal phase for {get_player_friendly_name(self.current_player)}'s turn.")
				self.set_current_message("Advancing to build phase")
				self.set_current_message("Build Phase")
				self.phase = PHASE_BUILD_AND_TRADE
				self.ui_needs_update=True

		elif self.phase == PHASE_BUILD_AND_TRADE:
			if self.awaiting_selection:
				if self.selection:
					if self.selection==OPTION_CANCEL: #If the user pushed the cancel button reset selection state
						self.selection=None
						self.awaiting_selection=False
						self.build_flag=None
						self.ui_needs_update=True
						self.hide_all_points()

			# if self.animation:
			# 	if self.animation_start + 3 < time.time():
			# 		self.animation = False
			# 		self.animation_start = None
			# else:
			# 	self.animation = True
			# 	self.animation_start = time.time()
			if self.build_flag:
				if self.build_flag==OPTION_BUILD_ROAD:
					if self.awaiting_selection:
						if self.selection:
							self.current_player_make_purchase_road(self.selection)
							self.hide_all_points()
							self.awaiting_selection = False
							self.build_flag = None
							self.selection = None
							self.ui_needs_update=True
					else:
						self.show_current_player_available_edges()
						self.awaiting_selection = True
						self.selection = None
						self.ui_needs_update=True
				elif self.build_flag==OPTION_BUILD_SETTLEMENT:
					if self.awaiting_selection:
						if self.selection:
							self.current_player_make_purchase_settlement(self.selection)
							self.hide_all_points()
							self.awaiting_selection = False
							self.build_flag = None
							self.selection = None
							self.ui_needs_update=True
					else:
						self.show_current_player_available_nodes()
						self.awaiting_selection = True
						self.selection = None
						self.ui_needs_update=True
				elif self.build_flag==OPTION_BUILD_CITY:
					if self.awaiting_selection:
						if self.selection:
							print(f"{get_player_friendly_name(self.current_player)} upgraded {self.selection}")
							self.current_player_make_purchase_city(self.selection)
							self.hide_all_points()
							self.awaiting_selection = False
							self.build_flag = None
							self.selection = None
							self.ui_needs_update=True
					else:
						self.show_current_player_available_upgrades()
						self.awaiting_selection = True
						self.selection = None
						self.ui_needs_update=True
				elif self.build_flag==OPTION_BUILD_DEVELOPMENT:
					self.current_player_make_purchase_development()
					self.build_flag = None
					self.ui_needs_update=True
				elif self.build_flag==OPTION_REQUEST_TRADE:
					self.build_flag=None
					pass
				elif self.build_flag==OPTION_END_TURN:
					self.phase=PHASE_END_TURN #Advance to next phase
					self.build_flag=None
				
				# self.build_flag=None #Reset build flag to wait for user input

		elif self.phase == PHASE_END_TURN:
			if self.animation:
				if self.animation_start + 0.25 < time.time():
					self.animation = False
					self.animation_start = None
					self.dice = None
					self.phase = PHASE_ROLL
					self.dealt = False
					self.round += 1
					self.current_player = self.players[self.round % len(self.players)]
					self.ui_needs_update=True
			else:
				self.set_current_message(f"Reached end of turn for {get_player_friendly_name(self.current_player)}")
				self.animation = True
				self.animation_start = time.time()
				self.ui_needs_update=True

		return self.get_rendered_objects()

	def set_build_road_flag(self):
		print("Road flag set")
		self.build_flag = OPTION_BUILD_ROAD
	def set_build_settlement_flag(self):		self.build_flag = OPTION_BUILD_SETTLEMENT
	def set_build_city_flag(self):				self.build_flag = OPTION_BUILD_CITY
	def set_build_development_flag(self):		self.build_flag = OPTION_BUILD_DEVELOPMENT
	def set_build_trade_requested_flag(self):	self.build_flag = OPTION_REQUEST_TRADE
	def set_build_end_turn_flag(self):			self.build_flag = OPTION_END_TURN
	def set_cancel_selection_flag(self):		self.selection = OPTION_CANCEL
	def check_player_build_road(self, player):
		"""Check if player can build a road"""
		return bool(get_available_edges(player))
	def check_player_build_settlement(self, player):
		"""Check if player can build a settlement"""
		return bool(get_available_nodes(self.nodes,player,True))
	def check_player_build_city(self, player):
		"""Check if player is able to upgrade a settlement"""
		return bool(get_available_upgrades(player))
	def check_player_can_afford_purchase(self, player, purchase):
		recipe = RECIPES[purchase]
		for resource in recipe.keys():
			if player.inventory[resource] < recipe[resource]:
				return False #can't afford recipe
		return True
	def check_player_option_availability_road(self, player):
		if all((
				self.check_player_can_afford_purchase(player, RECIPE_KEY_ROAD), #Check if player can afford to build
				self.check_player_build_road(player), #Check if player has a place to build a road
				self.phase is PHASE_BUILD_AND_TRADE,
			)):
			return True
		else:
			return False
	def check_player_option_availability_settlement(self, player):
		"""Check if player is able to build a settlement"""
		if all((
				self.check_player_can_afford_purchase(player, RECIPE_KEY_SETTLEMENT), #Check if player can afford to build
				self.check_player_build_settlement(player), #Check if player has a place to build a settlement
				self.phase is PHASE_BUILD_AND_TRADE,
			)):
			return True
		else:
			return False
	def check_player_option_availability_city(self, player):
		"""Check if player is able to upgrade a settlement"""
		if all((
				self.check_player_can_afford_purchase(player, RECIPE_KEY_CITY), #Check if player can afford to build
				self.check_player_build_city(player), #Check if player has a place to build a city
				self.phase is PHASE_BUILD_AND_TRADE,
			)):
			return True
		else:
			return False
	def check_player_option_availability_development(self, player):
		return False #Not implemented
		"""Check if player is able to build a development card"""
		if all((
				self.check_player_can_afford_purchase(player, RECIPE_KEY_DEVELOPMENT), #Check if player can afford to build
				self.phase is PHASE_BUILD_AND_TRADE,
			)):
			return True
		else:
			return False
	def check_player_option_availability_trade(self, player):
		"""Check if player is able to trade"""
		return False
	def check_player_option_availability_end_turn(self, player):
		"""Check if player is able to end turn"""
		if not self.phase == PHASE_BUILD_AND_TRADE: return False
		if self.animation: return False
		if self.awaiting_selection: return False
		return True
	def check_player_option_availability_cancel(self, player):
		"""Check if player is able to press cancel button"""
		if not self.phase == PHASE_BUILD_AND_TRADE: return False
		if self.animation: return False
		if not self.awaiting_selection: return False
		return True
	def show_player_available_edges(self, player):
		self.hide_all_points()
		for a in get_available_edges(player): a.enabled = True
	def show_player_available_nodes(self, player, require_connected = True):
		self.hide_all_points()
		for a in get_available_nodes(self.nodes, player, require_connected): a.enabled = True
	def show_player_available_upgrades(self, player):
		self.hide_all_points()
		for a in get_available_upgrades(player): a.enabled = True
	def check_current_player_build_road(self): 						return self.check_player_build_road(self.current_player)
	def check_current_player_build_settlement(self):				return self.check_player_build_settlement(self.current_player)
	def check_current_player_build_city(self): 						return self.check_player_build_city(self.current_player)
	def check_current_player_can_afford_purchase(self, purchase): 	return self.check_player_can_afford_purchase(self.current_player, purchase)
	def check_current_player_option_availability_road(self): 		return self.check_player_option_availability_road(self.current_player)
	def check_current_player_option_availability_settlement(self): 	return self.check_player_option_availability_settlement(self.current_player)
	def check_current_player_option_availability_city(self): 		return self.check_player_option_availability_city(self.current_player)
	def check_current_player_option_availability_development(self): return self.check_player_option_availability_development(self.current_player)
	def check_current_player_option_availability_trade(self): 		return self.check_player_option_availability_trade(self.current_player)
	def check_current_player_option_availability_end_turn(self): 	return self.check_player_option_availability_end_turn(self.current_player)
	def check_current_player_option_availability_cancel(self):		return self.check_player_option_availability_cancel(self.current_player)
	def show_current_player_available_edges(self):
		print("Showing available edges")
		return self.show_player_available_edges(self.current_player)
	def show_current_player_available_nodes(self, require_connected = True): 
		print("Showing available nodes")
		return self.show_player_available_nodes(self.current_player, require_connected)
	def player_make_purchase(self, player, purchase):
		recipe = RECIPES[purchase]
		for resource in recipe.keys():
			if player.inventory[resource] < recipe[resource]:
				raise ValueError(f"{get_player_friendly_name(player)} is trying to make purchase but cannot afford it.\nNeed {recipe[resource]} {RESOURCE_MAP_INT_TO_NAME[resource]} but player only has {inventory[resource]}")
			player.inventory[resource] -= recipe[resource] #Take the resources from the player's inventory
		return True
	def show_current_player_available_upgrades(self): return self.show_player_available_upgrades(self.current_player)
	def player_make_purchase_road(self, player, edge):
		self.player_make_purchase(player, RECIPE_KEY_ROAD)
		edge.set_owner(player)
	def player_make_purchase_settlement(self, player, node):
		self.player_make_purchase(player, RECIPE_KEY_SETTLEMENT)
		node.set_owner(player)
	def player_make_purchase_city(self, player, node):
		self.player_make_purchase(player, RECIPE_KEY_CITY)
		node.upgrade()
	def player_make_purchase_development(self, player):
		self.player_make_purchase(player, RECIPE_KEY_DEVELOPMENT)
		raise(ValueError("Not Implemented"))
	def current_player_make_purchase(self,purchase):		self.player_make_purchase(self.current_player,purchase)
	def current_player_make_purchase_road(self,edge):		self.player_make_purchase_road(self.current_player,edge)
	def current_player_make_purchase_settlement(self,node):	self.player_make_purchase_settlement(self.current_player,node)
	def current_player_make_purchase_city(self,node):		self.player_make_purchase_city(self.current_player,node)
	def current_player_make_purchase_development(self):		self.player_make_purchase_development(self.current_player)
	def show_all_nodes(self):
		for n in self.nodes: n.enabled = True
	def hide_all_nodes(self):
		for n in self.nodes: n.enabled = False
	def show_all_edges(self):
		for e in self.edges: e.enabled = True
	def hide_all_edges(self):
		for e in self.edges: e.enabled = False
	def show_all_tiles(self):
		for t in self.tiles: t.enabled = True
	def hide_all_tiles(self):
		for t in self.tiles: t.enabled = False
	def show_all_points(self):
		for n in self.nodes: n.enabled = True
		for e in self.edges: e.enabled = True
		for t in self.tiles: t.enabled = True
	def hide_all_points(self):
		for n in self.nodes: n.enabled = False
		for e in self.edges: e.enabled = False
		for t in self.tiles: t.enabled = False
	def pick_random_resource_tile_type(self):
		if self.limited_tile_pool:
			raise ValueError("Not Implemented")
		else:
			return random.choice(RESOURCES_TILE_TYPES)
	def pick_random_resource_type(self):
		return random.choice(RESOURCES)

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
	def __init__(self, game, tile_edges, tile_nodes):
		super().__init__(game)
		for e in tile_edges: self.add_neighbor_edge(e)
		for n in tile_nodes: self.add_neighbor_node(n)
		self.value = get_chip_number()
		self.resource_type=self.game.pick_random_resource_type()
		self.owner=None
		self.has_robber=False
	def add_neighbor_tile(self,t):
		self.neighbor_tiles.update({t})
		if not self in t.neighbor_tiles: t.add_neighbor_tile(self)
	def add_neighbor_edge(self,e):
		self.neighbor_edges.update({e})
		if not self in e.neighbor_tiles: e.add_neighbor_tile(self)
	def add_neighbor_node(self,n):
		self.neighbor_nodes.update({n})
		if not self in n.neighbor_tiles: n.add_neighbor_tile(self)
	def get_resource_color(self):
		return ursina.rgb(*RESOURCE_MAP_INT_TO_COLOR[self.resource_type])
	def set_owner(self, val=None):
		self.owner = True
	def set_robber(self):
		self.has_robber = True
	def remove_robber(self):
		self.has_robber = False

class EdgeMixin(BoardElement):
	def __init__(self, game, node_a, node_b):
		super().__init__(game)
		self.add_neighbor_node(node_a)
		self.add_neighbor_node(node_b)
		self.node_a, self.node_b = node_a, node_b
		node_a.add_neighbor_node(node_b) #B adds A back automatically
	def add_neighbor_edge(self, e):
		self.neighbor_edges.update({e})
		if not self in e.neighbor_edges: e.add_neighbor_edge(self)
	def add_neighbor_node(self,n):
		self.neighbor_nodes.update({n})
		if not self in n.neighbor_edges: n.add_neighbor_edge(self)
	def add_neighbor_tile(self,t):
		self.neighbor_tiles.update({t})
		if not self in t.neighbor_edges: t.add_neighbor_edge(self)
		t.add_neighbor_node(self.node_a)
		t.add_neighbor_node(self.node_b)
	def set_owner(self, owner):
		if self.owner: raise ValueError(f"Attempted to set owner on {type(self)} that already has an owner - {owner}")
		self.owner = owner
		self.owner.owned_edges.append(self)
		for t in self.neighbor_tiles:
			if not t.owner: t.set_owner(True)

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
		print("upgraded ", self)
	def add_neighbor_node(self,n):
		self.neighbor_nodes.update({n})
		if not self in n.neighbor_nodes: n.add_neighbor_node(self)
	def set_owner(self, owner):
		if self.owner: raise ValueError(f"Attempted to set owner on {type(self)} that already has an owner")
		self.owner = owner
		self.owner.owned_nodes.append(self)
		for t in self.neighbor_tiles:
			if not t.owner: t.set_owner(True)
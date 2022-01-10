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
	def __init__(self, color):
		self.color = color
		self.board_pieces = None
		self.inventory = {
			RESOURCE_SHEEP	:0,
			RESOURCE_IRON	:100,
			RESOURCE_WOOD	:100,
			RESOURCE_BRICK	:100,
			RESOURCE_WHEAT	:100,
		}
		self.owned_edges, self.owned_nodes = [], []
		self.resource_cards = []
		self.placed_first_town = False
		self.longest_road_length = 0
		self.army_size = 0
		self.harbor_count = 0
		self.played_resource_card_this_turn = False

class redPlayer(Player):
	def __init__(self): Player.__init__(self, settings.player_color_red)
class bluePlayer(Player):
	def __init__(self): Player.__init__(self, settings.player_color_blue)
class greenPlayer(Player):
	def __init__(self): Player.__init__(self, settings.player_color_green)
class yellowPlayer(Player):
	def __init__(self): Player.__init__(self, settings.player_color_yellow)
class purplePlayer(Player):
	def __init__(self): Player.__init__(self, settings.player_color_purple)
class pinkPlayer(Player):
	def __init__(self): Player.__init__(self, settings.player_color_pink)
class brownPlayer(Player):
	def __init__(self): Player.__init__(self, settings.player_color_brown)
class grayPlayer(Player):
	def __init__(self): Player.__init__(self, settings.player_color_gray)

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
	"""Check if player is able to upgrade a town"""
	for n in player.owned_nodes:
		if not n.upgraded:
			yield n

# def get_available_nodes(nodes, player, require_connected=True):
# 	"""Get available town nodes for given player"""
# 	if not require_connected:
# 		for n in nodes:
# 			if not n.owner and not any(nn.owner for nn in n.neighbor_nodes):
# 				yield n
# 	else: #Find available nodes
# 		for e in player.owned_edges:
# 			for n in e.neighbor_nodes:
# 				if not n.owner:
# 					if not any(nn.owner for nn in n.neighbor_nodes):
# 						available.append(n)
# 						yield n #Node is available

def get_available_land_nodes(nodes, player, require_connected=True):
	"""Get available town nodes for given player"""
	if not require_connected:
		for n in nodes:
			if not n.owner and not any(nn.owner for nn in n.neighbor_nodes):
				if not n.water_node:
					yield n
	else: #Find available nodes
		for e in player.owned_edges:
			for n in e.neighbor_nodes:
				if not n.owner:
					if not any(nn.owner for nn in n.neighbor_nodes):
						if not n.water_node:
							yield n #Node is available

#All edges if no flags set
#Only roads if only_roads_or_water is set
#Only water edges if only_roads_or_water and water_flag is set
#Only Water if water flag is set
def get_available_edges(player, only_roads_or_water = False, water_flag = False):
	"""Get available edges for given player"""
	available = []
	for n in player.owned_nodes: #if a node doesn't have any roads it must have one added now
		if not any((e.owner is player for e in n.neighbor_edges)):
			for e in n.neighbor_edges:
				if not e.owner:
					if only_roads_or_water:
						if e.water_edge == water_flag:
							available.append(e)
					else:
						available.append(e)
			return available
	for n in player.owned_nodes:
		for e in n.neighbor_edges:
			if not e.owner:
				if only_roads_or_water:
					if e.water_edge == water_flag:
						available.append(e)
				else:
					available.append(e)
	for e in player.owned_edges:
		for _e in e.neighbor_edges:
			if not _e.owner:
				if only_roads_or_water:
					if _e.water_edge == water_flag:
						available.append(_e)
				else:
					available.append(_e)
	return available
def get_available_roads(player): return get_available_edges(player, only_roads_or_water=True, water_flag=False)
def get_available_water_edges(player): return get_available_edges(player, only_roads_or_water=True, water_flag=True)

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
		self.limited_tile_pool = True

		self.longest_road_owner = None
		self.longest_road_size = 0
		self.largest_army_owner = None
		self.largest_army_size = 0
		self.harbormaster_owner = None
		self.harbormaster_size = 0

		self.robber_enabled = True
		self.desert_in_center = True

		self.exchange_rates = DEFAULT_BANK_EXCHANGE_RATES
		self.port_exchange_rates = DEFAULT_PORT_EXCHANGE_RATES
		self.number_of_trading_port_attempts = DEFAULT_NUMBER_OF_TRADING_PORT_ATTEMPTS
		self.port_chance = DEFAULT_PORT_CHANCE

		self.build_flag = None

		self.ui_needs_update = True

		self.recipes = RECIPES

		self.current_message = None

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
			if e.owner or issubclass(type(e), WaterTileMixin): rendered.append(e)
		for e in self.edges:
			if e.owner or e.port: rendered.append(e)
		for e in self.nodes:
			if e.owner: rendered.append(e)
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
							if not t.resource_type == RESOURCE_WASTELAND:
								if not t.has_robber:
									print(f"{1 + n.upgraded} X {RESOURCE_MAP_INT_TO_NAME[t.resource_type]} for {get_player_friendly_name(n.owner)}")
									n.owner.inventory[t.resource_type] += 1 + n.upgraded

	def update_scores(self):
		def get_longest_road(player):
			pass
		pass
	def get_player_victory_point_count(self, player):
			vp = 0
			for n in player.owned_nodes: vp += 1 + n.upgraded
			return vp

	def get_current_player_victory_point_count(self):
		return self.get_player_victory_point_count(self.current_player)

	def find_player_with_longest_road(self):
		pass

	def gameloop(self):
		self.update_scores()
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
					if not self.multiple_placement_flag: #Town has been placed
						if not self.current_player.placed_first_town:
							self.current_player.placed_first_town = True
							for t in self.selection.neighbor_tiles:
								if not t.resource_type is RESOURCE_WASTELAND:
									self.current_player.inventory[t.resource_type] += 1

						self.set_current_message(f"{get_player_friendly_name(self.current_player)} has placed setup town")
						self.selection.set_owner(self.current_player)
						self.multiple_placement_flag = True
						self.show_current_player_available_roads()
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
					s_o_r = "road" if self.multiple_placement_flag else "town"
					self.set_current_message(f"Waiting for {get_player_friendly_name(self.current_player)} to select {s_o_r} location")
					self.show_current_player_available_land_nodes(require_connected=False)
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

			if not self.awaiting_selection:
				if not self.dice:
					self.set_current_message(f"Rolling dice for {get_player_friendly_name(self.current_player)}'s turn")
					self.dice = get_dice_roll() #Must set before doing payouts
					if sum(self.dice) == 7:
						print("Rolled 7!")
						if self.robber_enabled:
							self.set_current_message(f"{get_player_friendly_name(self.current_player)} has rolled a 7!")
							self.set_current_message(f"Waiting for {get_player_friendly_name(self.current_player)} to select new robber location")
							self.current_robber_tile = self.get_robber_location()
							self.show_player_available_robber_tiles()
							self.awaiting_selection = True
							self.selection = None
							self.ui_needs_update = True
					#Handle dice roll animation elements here
					self.animation = True
					self.animation_start = time.time()
					self.ui_needs_update=True
				else:
					self.set_current_message(f"Finished roll for {get_player_friendly_name(self.current_player)}'s turn.")
					self.set_current_message("Advancing to deal phase")
					self.phase = PHASE_DEAL
					self.ui_needs_update=True
			else:
				#We end up here again if the player needs to select someone to steal from
				if issubclass(type(self.selection), TileMixin):
					self.selection.has_robber = True
					if self.current_robber_tile: self.current_robber_tile.has_robber = False
					self.current_robber_tile = self.selection
					self.hide_all_tiles()
					if any(n.owner and not n.owner is self.current_player for n in self.selection.neighbor_nodes):
						for n in self.selection.neighbor_nodes:
							if n.owner and not n.owner is self.current_player:
								n.enabled = True
						self.set_current_message(f"Waiting for {get_player_friendly_name(self.current_player)} to select town to steal from")
					else:
						self.awaiting_selection = False
					self.selection = None
				elif issubclass(type(self.selection), NodeMixin):
					self.steal_random_resource(self.current_player, self.selection.owner)
					self.selection = None
					self.awaiting_selection = False
					self.hide_all_nodes()
				else:
					raise ValueError("Selected invalid type")
				self.ui_needs_update = True


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
						self.show_current_player_available_roads()
						self.awaiting_selection = True
						self.selection = None
						self.ui_needs_update=True
				elif self.build_flag==OPTION_BUILD_SETTLEMENT:
					if self.awaiting_selection:
						if self.selection:
							self.current_player_make_purchase_town(self.selection)
							self.hide_all_points()
							self.awaiting_selection = False
							self.build_flag = None
							self.selection = None
							self.ui_needs_update=True
					else:
						self.show_current_player_available_land_nodes()
						self.awaiting_selection = True
						self.selection = None
						self.ui_needs_update=True
				elif self.build_flag==OPTION_BUILD_CITY:
					if self.awaiting_selection:
						if self.selection:
							print(f"{get_player_friendly_name(self.current_player)} upgraded {self.selection}")
							self.current_player_make_purchase_capital(self.selection)
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
				elif self.build_flag==OPTION_BUILD_ACHIEVEMENT:
					self.current_player_make_purchase_achievement()
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
	def set_build_town_flag(self):		self.build_flag = OPTION_BUILD_SETTLEMENT
	def set_build_capital_flag(self):				self.build_flag = OPTION_BUILD_CITY
	def set_build_achievement_flag(self):		self.build_flag = OPTION_BUILD_ACHIEVEMENT
	def set_build_trade_requested_flag(self):	self.build_flag = OPTION_REQUEST_TRADE
	def set_build_end_turn_flag(self):			self.build_flag = OPTION_END_TURN
	def set_cancel_selection_flag(self):		self.selection = OPTION_CANCEL
	def check_player_build_road(self, player):
		"""Check if player can build a road"""
		return bool(get_available_roads(player))
	def check_player_build_town(self, player):
		"""Check if player can build a town"""
		return bool(get_available_land_nodes(self.nodes,player,True))
	def check_player_build_capital(self, player):
		"""Check if player is able to upgrade a town"""
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
	def check_player_option_availability_town(self, player):
		"""Check if player is able to build a town"""
		if all((
				self.check_player_can_afford_purchase(player, RECIPE_KEY_SETTLEMENT), #Check if player can afford to build
				self.check_player_build_town(player), #Check if player has a place to build a town
				self.phase is PHASE_BUILD_AND_TRADE,
			)):
			return True
		else:
			return False
	def check_player_option_availability_capital(self, player):
		"""Check if player is able to upgrade a town"""
		if all((
				self.check_player_can_afford_purchase(player, RECIPE_KEY_CITY), #Check if player can afford to build
				self.check_player_build_capital(player), #Check if player has a place to build a capital
				self.phase is PHASE_BUILD_AND_TRADE,
			)):
			return True
		else:
			return False
	def check_player_option_availability_achievement(self, player):
		return False #Not implemented
		"""Check if player is able to build a achievement card"""
		if all((
				self.check_player_can_afford_purchase(player, RECIPE_KEY_ACHIEVEMENT), #Check if player can afford to build
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
		for e in get_available_edges(player): e.enabled = True
	def show_player_available_roads(self, player):
		self.hide_all_points()
		for e in get_available_roads(player): e.enabled = True
	def show_player_available_water_edges(self, player):
		self.hide_all_points()
		for e in get_available_water_edges(player): e.enabled = True
	def show_player_available_roads(self, player):
		self.hide_all_points()
		for e in get_available_roads(player): e.enabled = True
	def show_player_available_water_edges(self, player):
		self.hide_all_points()
		for e in get_available_water_edges(player): e.enabled = True
	# def show_player_available_nodes(self, player, require_connected = True):
	# 	self.hide_all_points()
	# 	for e in get_available_nodes(self.nodes, player, require_connected): e.enabled = True
	def show_player_available_land_nodes(self, player, require_connected = True, exclude = []):
		self.hide_all_points()
		for e in get_available_land_nodes(self.nodes, player, require_connected):
			if not e in exclude:
				e.enabled = True
	def show_player_available_upgrades(self, player):
		self.hide_all_points()
		for e in get_available_upgrades(player): e.enabled = True
	def check_current_player_build_road(self): 						return self.check_player_build_road(self.current_player)
	def check_current_player_build_town(self):				return self.check_player_build_town(self.current_player)
	def check_current_player_build_capital(self): 						return self.check_player_build_capital(self.current_player)
	def check_current_player_can_afford_purchase(self, purchase): 	return self.check_player_can_afford_purchase(self.current_player, purchase)
	def check_current_player_option_availability_road(self): 		return self.check_player_option_availability_road(self.current_player)
	def check_current_player_option_availability_town(self): 	return self.check_player_option_availability_town(self.current_player)
	def check_current_player_option_availability_capital(self): 		return self.check_player_option_availability_capital(self.current_player)
	def check_current_player_option_availability_achievement(self): return self.check_player_option_availability_achievement(self.current_player)
	def check_current_player_option_availability_trade(self): 		return self.check_player_option_availability_trade(self.current_player)
	def check_current_player_option_availability_end_turn(self): 	return self.check_player_option_availability_end_turn(self.current_player)
	def check_current_player_option_availability_cancel(self):		return self.check_player_option_availability_cancel(self.current_player)
	def show_current_player_available_edges(self):
		return self.show_player_available_edges(self.current_player)
	def show_current_player_available_roads(self):
		return self.show_player_available_roads(self.current_player)
	def show_current_player_available_water_edges(self):
		return self.show_player_available_water_edges(self.current_player)
	# def show_current_player_available_nodes(self, require_connected = True): 
	# 	return self.show_player_available_nodes(self.current_player, require_connected)
	def show_current_player_available_land_nodes(self, require_connected = True, exclude = []): 
		return self.show_player_available_land_nodes(self.current_player, require_connected, exclude)
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
	def player_make_purchase_town(self, player, node):
		self.player_make_purchase(player, RECIPE_KEY_SETTLEMENT)
		node.set_owner(player)
	def player_make_purchase_capital(self, player, node):
		self.player_make_purchase(player, RECIPE_KEY_CITY)
		node.upgrade()
	def player_make_purchase_achievement(self, player):
		self.player_make_purchase(player, RECIPE_KEY_ACHIEVEMENT)
		raise(ValueError("Not Implemented"))
	def current_player_make_purchase(self,purchase):		self.player_make_purchase(self.current_player,purchase)
	def current_player_make_purchase_road(self,edge):		self.player_make_purchase_road(self.current_player,edge)
	def current_player_make_purchase_town(self,node):	self.player_make_purchase_town(self.current_player,node)
	def current_player_make_purchase_capital(self,node):		self.player_make_purchase_capital(self.current_player,node)
	def current_player_make_purchase_achievement(self):		self.player_make_purchase_achievement(self.current_player)
	def show_all_nodes(self, exclude=[]):
		for n in self.nodes: n.enabled = not n in exclude
	def hide_all_nodes(self, exclude=[]):
		for n in self.nodes: n.enabled = n in exclude
	def show_all_edges(self, exclude=[]):
		for e in self.edges: e.enabled = not e in exclude
	def hide_all_edges(self, exclude=[]):
		for e in self.edges: e.enabled = e in exclude
	def show_all_road_edges(self, exclude=[]):
		for e in self.edges: e.enabled = not e in exclude and not e.water_edge
	def hide_all_road_edges(self, exclude=[]):
		for e in self.edges: e.enabled = e in exclude and not e.water_edge
	def show_all_water_edges(self, exclude=[]):
		for e in self.edges: e.enabled = not e in exclude and e.water_edge
	def hide_all_water_edges(self, exclude=[]):
		for e in self.edges: e.enabled = e in exclude and e.water_edge
	def show_all_tiles(self, exclude=[]):
		for t in self.tiles: t.enabled = not t in exclude
	def hide_all_tiles(self, exclude=[]):
		for t in self.tiles: t.enabled = t in exclude
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
	def pick_random_resource_type(self, map_center = False):
		if map_center and self.desert_in_center:
			return RESOURCE_WASTELAND
		return random.choice(RESOURCES)
	def get_player_exchange_rates(self, player):
		exchange_rates = {}
		for n in player.owned_nodes:
			for e in n.neighbor_edges:
				if e.port:
					exchange_rates[e.port] = self.port_exchange_rates[e.port]
		rates = {}
		for r in RESOURCES:
			if exchange_rates.get(r):
				rates[r] = min(exchange_rates.get(r) or exchange_rates.get("*"), self.exchange_rates.get(r) or self.exchange_rates.get("*"))
			else:
				rates[r] = exchange_rates.get("*") or self.exchange_rates.get(r) or self.exchange_rates.get("*")
		return rates
	def get_current_player_exchange_rates(self):
		return self.get_player_exchange_rates(self.current_player)
	def make_player_exchange(self, player, source_resource, target_resource):
		print(RESOURCE_MAP_INT_TO_NAME[source_resource], RESOURCE_MAP_INT_TO_NAME[target_resource])
		#Ensure player has enough of source_resource to make transaction
		count = player.inventory[source_resource]
		rate = self.get_player_exchange_rates(player)[source_resource]
		if not count >= rate: raise ValueError("Player called for exchange with insufficient resources")
		player.inventory[source_resource] = player.inventory[source_resource]-rate
		player.inventory[target_resource] = player.inventory[target_resource]+1
		print(f"{get_player_friendly_name(player)} traded {rate} {RESOURCE_MAP_INT_TO_NAME[source_resource]} for {1} {RESOURCE_MAP_INT_TO_NAME[target_resource]}")
		self.ui_needs_update = True
	def make_current_player_exchange(self, *args):
		return self.make_player_exchange(self.current_player, *args)
	def get_robber_location(self):
		for t in self.tiles:
			if t.has_robber:
				return t
	def steal_random_resource(self,robber_player,victim_player):
		inventory = []
		for r in RESOURCES:
			for i in range(victim_player.inventory[r]):
				inventory.append(r)
		if inventory:
			resource_to_steal = random.choice(inventory)
			victim_player.inventory[resource_to_steal] = victim_player.inventory[resource_to_steal] - 1
			robber_player.inventory[resource_to_steal] = robber_player.inventory[resource_to_steal] + 1
			self.set_current_message(f"{get_player_friendly_name(robber_player)} stole {RESOURCE_MAP_INT_TO_NAME[resource_to_steal]} from {get_player_friendly_name(victim_player)}")
		else:
			self.set_current_message(f"There was nothing for {get_player_friendly_name(robber_player)} to steal from {get_player_friendly_name(victim_player)}")
	def show_player_available_robber_tiles(self):
		for t in self.tiles:
			if not issubclass(type(t), WaterTileMixin):
				if t.owner:
					if not t.has_robber:
						t.enabled = True
	def get_random_port_trade_deal(self): return random.choice(list(self.port_exchange_rates.keys()))
	

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

#Minimize duplicated code between water and edge tiles
class _BaseTileMixin(BoardElement):
	def __init__(self,game,tile_edges,tile_nodes,owner=None):
		BoardElement.__init__(self, game)
		for e in tile_edges: self.add_neighbor_edge(e)
		for n in tile_nodes: self.add_neighbor_node(n)
		self.owner=owner #Serves as a "Discovered" flag for tiles
	def add_neighbor_tile(self,t):
		self.neighbor_tiles.update({t})
		if not self in t.neighbor_tiles: t.add_neighbor_tile(self)
	def add_neighbor_edge(self,e):
		self.neighbor_edges.update({e})
		if not self in e.neighbor_tiles:
			e.add_neighbor_tile(self)
	def add_neighbor_node(self,n):
		self.neighbor_nodes.update({n})
		if not self in n.neighbor_tiles: n.add_neighbor_tile(self)
	def set_owner(self, val=None):
		self.owner = True

class TileMixin(_BaseTileMixin):
	def __init__(self,game,tile_edges,tile_nodes,owner=None,map_center=False,has_robber=False):
		_BaseTileMixin.__init__(self, game, tile_edges, tile_nodes, owner)
		self.value = get_chip_number()
		self.has_robber=has_robber
		self.map_center=map_center
		self.resource_type=self.game.pick_random_resource_type(self.map_center)
		if self.resource_type is RESOURCE_WASTELAND:
			self.has_robber = True
			self.owner = True #Set discovered so tile gets rendered by mainloop
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
	def set_owner(self, val=None):self.owner = True
	def set_robber(self):self.has_robber = True
	def remove_robber(self):self.has_robber = False

class WaterTileMixin(_BaseTileMixin):
	def __init__(self,game,tile_edges,tile_nodes,owner=None):
		_BaseTileMixin.__init__(self, game,tile_edges,tile_nodes,owner=None)
		
class EdgeMixin(BoardElement):
	def __init__(self, game, node_a, node_b, water_edge=False):
		BoardElement.__init__(self, game)
		self.add_neighbor_node(node_a)
		self.add_neighbor_node(node_b)
		self.node_a, self.node_b = node_a, node_b
		node_a.add_neighbor_node(node_b) #B adds A back automatically
		self.water_edge = water_edge #Track if edge is water-only (boats only)
		self.port = False #Track if port enabled on tile or not
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
	def enable_port(self):
		self.port = self.game.get_random_port_trade_deal()

class NodeMixin(BoardElement):
	def __init__(self, game, tile_edges = [], tile_nodes = [], tiles = [], owner=None, water_node=False):
		BoardElement.__init__(self, game)
		for t in tiles: self.add_neighbor_tile(t)
		for e in tile_edges: self.add_neighbor_edge(e)
		for n in tile_nodes: self.add_neighbor_nodes(n)
		self.upgraded = False
		self.water_node = water_node

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

	class _BaseAchievementCard:
		def __init__(self, text):
			self.text = text
	class KnightCard(_BaseAchievementCard):
		def __init__(self):_BaseAchievementCard.__init__(self)
	class _BaseProgressCard(_BaseAchievementCard):
		def __init__(self):_BaseAchievementCard.__init__(self)
	class NaturalPavimentum (_BaseProgressCard):#Build Two Roads
		def __init__(self):_BaseProgressCard.__init__(self)
	class BountifulHarvest (_BaseProgressCard):#Pick Two Cards
		def __init__(self):_BaseProgressCard.__init__(self)
	class ClaimedProduct (_BaseProgressCard):#Steal all of one resource from everyone
		def __init__(self):_BaseProgressCard.__init__(self)
	# class CollectedTax (_BaseProgressCard): #Steal one random resource from each person
	# 	def __init__(self): _BaseProgressCard.__init__(self)
	# class RapidAdvancement (_BaseProgressCard): #Instantly upgrade a town
	# 	def __init__(self): _BaseProgressCard.__init__(self)
	# class MaritimeEstablishment (_BaseProgressCard): #Create a port on an owned shore edge if in a valid location
	# 	def __init__(self): _BaseProgressCard.__init__(self)
	# class ReformedLand (_BaseProgressCard): #Reroll a tile value for a tile you own at least one node on
	# 	def __init__(self): _BaseProgressCard.__init__(self)
	class _BaseVictoryPointCard(_BaseAchievementCard):
		def __init__(self, text):_BaseAchievementCard.__init__(self, text)
	class Colosseum(_BaseVictoryPointCard):
		def __init__(self):_BaseVictoryPointCard.__init__(self,"Colosseum")
	class CapitalHall(_BaseVictoryPointCard):
		def __init__(self):_BaseVictoryPointCard.__init__(self,"Capital Hall")
	# class Church(_BaseVictoryPointCard):
	# 	def __init__(self):_BaseVictoryPointCard.__init__(self,"Church")
	class Bazaar(_BaseVictoryPointCard):
		def __init__(self):_BaseVictoryPointCard.__init__(self,"Bazaar")
	class Academy(_BaseVictoryPointCard):
		def __init__(self):_BaseVictoryPointCard.__init__(self,"Academy")
	# class Tower(_BaseVictoryPointCard):
	# 	def __init__(self):_BaseVictoryPointCard.__init__(self,"Tower")
	# class Tunnel(_BaseVictoryPointCard):
	# 	def __init__(self):_BaseVictoryPointCard.__init__(self,"Tunnel")
	# class Observatory(_BaseVictoryPointCard):
	# 	def __init__(self):_BaseVictoryPointCard.__init__(self,"Observatory")
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
# 	"bandit_enabled":True,
# 	"desert_enabled":True,
# 	"board_radius":4,
# 	"gold_enabled":False,
# 	"gold_rush_enabled":False,
# }

# class Ruleset:
# 	def __init__(self, *args, **kwargs):
# 		self.bandit_enabled = True
# 		self.rules = kwargs

# class DefaultRules(Ruleset):
# 	def __init__(self, *args, **kwargs):
# 		rules = {
# 			"bandit_enabled":True,
# 			"desert_enabled":True,
# 		}
# 		Ruleset.__init__(self, *args, **kwargs)

# class HexplorationRules(Ruleset):
# 	def __init__(self, *args, **kwargs):
# 		rules = {
# 			"bandit_enabled":False,
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
			RESOURCE_CATTLE	:100,
			RESOURCE_IRON	:100,
			RESOURCE_WOOD	:100,
			RESOURCE_BRICK	:100,
			RESOURCE_WHEAT	:100,
		}
		self.owned_edges, self.owned_nodes = [], []
		self.resource_cards = []
		self.placed_first_town = False
		self.longest_road_length = 0
		self.patrol_count = 0
		self.port_count = 0
		self.played_action_card_this_turn = False
		self.action_cards = []
		self.achievement_cards = []

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
		self.build_flag = None
		self.selection = None
		self.awaiting_selection = False
		self.multiple_placement_flag = False
		self.placement_order = []
		self.current_player = None
		self.animation = False
		self.animation_start = None
		self.dice = None
		self.dealt = False
		self.round = 0
		self.limited_tile_pool = True
		self.ui_needs_update = True

		self.min_roads_for_via_domini = DEFAULT_MIN_ROADS_FOR_VIA_DOMINI
		self.min_ports_for_portum_domini = DEFAULT_MIN_PORTS_FOR_PORTUM_DOMINI
		self.min_patrols_for_militum_dominus = DEFAULT_MIN_PATROLS_FOR_MILITUM_DOMINUS
		self.via_domini = None #Tracks current via domini holder
		self.portum_domini = None #Tracks current portum domini holder
		self.militum_dominus = None #Tracks current militum domini holder

		self.bandit_enabled = True
		self.desert_enabled = True
		self.desert_in_center = True
		self.current_bandit_tile = None

		self.discard_on_7 = False

		self.exchange_rates = DEFAULT_BANK_EXCHANGE_RATES
		self.port_exchange_rates = DEFAULT_PORT_EXCHANGE_RATES
		self.number_of_trading_port_attempts = DEFAULT_NUMBER_OF_TRADING_PORT_ATTEMPTS
		self.port_chance = DEFAULT_PORT_CHANCE
		self.unlimited_achievement_cards = False

		self.recipes = RECIPES

		self.current_message = None

		self.default_achievement_card_deck = get_achievement_deck()
		self.achievement_card_deck = self.default_achievement_card_deck.copy()

	def set_current_message(self, current_message):
		print(f"USERMESSAGE - {current_message}")
		self.current_message = current_message

	def create(self, tiles, edges, nodes):
		self.tiles, self.edges, self.nodes = tiles, edges, nodes

	def select(self, entity):
		if not self.selection: self.selection = entity
		self.hide_all_points()
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
			if not t.has_bandit:
				if t.value == roll_value:
					for n in t.neighbor_nodes:
						if n.owner:
							if not t.resource_type == RESOURCE_WASTELAND:
								if not t.has_bandit:
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

	def get_player_port_count(self, player):
		port_count = 0
		for n in player.owned_nodes:
			for e in n.neighbor_edges:
				if e.port:
					port_count += 1
		return port_count
	def get_current_player_port_count(self):
		return get_player_port_count(self.current_player)

	def gameloop(self):
		self.update_scores()
		"""Main Gameloop"""
		"""Must always return a list of game pieces for the renderer to render"""
		"""The renderer only updates the UI if the rendered objects list changes
		"""##AND OR## if self.ui_needs_update is set to true"""
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
						self.clear_selection()
						self.set_current_message(f"Waiting for {get_player_friendly_name(self.current_player)} to select road location")
					else:
						self.set_current_message(f"{get_player_friendly_name(self.current_player)} has placed setup road")
						self.selection.set_owner(self.current_player)
						self.clear_selection()
						self.multiple_placement_flag = False #Reset
						self.placement_order.pop(0)
						if not self.placement_order: #Nobody left
							self.set_current_message("Advancing to deal phase")
							self.phase = PHASE_ROLL
							self.selection  = None
				else:
					s_o_r = "road" if self.multiple_placement_flag else "town"
					self.set_current_message(f"Waiting for {get_player_friendly_name(self.current_player)} to select {s_o_r} location")
					if self.multiple_placement_flag:
						self.show_current_player_available_roads()
					else:
						self.show_current_player_available_land_nodes(require_connected=False)
					self.await_selection()
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
						if self.bandit_enabled:
							self.set_current_message(f"{get_player_friendly_name(self.current_player)} has rolled a 7!")
							self.set_current_message(f"Waiting for {get_player_friendly_name(self.current_player)} to select new bandit location")
							self.current_bandit_tile = self.get_bandit_location()
							self.show_player_available_bandit_tiles()
							self.await_selection()
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
					self.selection.has_bandit = True
					if self.current_bandit_tile: self.current_bandit_tile.has_bandit = False
					self.current_bandit_tile = self.selection
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
					self.clear_selection()
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

		############
		#BUILD PHASE
		############
		elif self.phase == PHASE_BUILD_AND_TRADE:
			if self.selection==OPTION_CANCEL: #If the user pushed the cancel button reset selection state
				self.clear_build_selection()
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
							self.clear_build_selection()
					else:
						self.show_current_player_available_roads()
						self.await_selection()
				elif self.build_flag==OPTION_BUILD_SETTLEMENT:
					if self.awaiting_selection:
						if self.selection:
							self.current_player_make_purchase_town(self.selection)
							self.clear_build_selection()
					else:
						self.show_current_player_available_land_nodes()
						self.await_selection()
				elif self.build_flag==OPTION_BUILD_CITY:
					if self.awaiting_selection:
						if self.selection:
							print(f"{get_player_friendly_name(self.current_player)} upgraded {self.selection}")
							self.current_player_make_purchase_capitol(self.selection)
							self.clear_build_selection()
					else:
						self.show_current_player_available_upgrades()
						self.await_selection()
				elif self.build_flag==OPTION_BUILD_ACHIEVEMENT:
					self.current_player_make_purchase_achievement()
					self.build_flag = None
					self.ui_needs_update=True
				elif self.build_flag==OPTION_REQUEST_TRADE:
					self.build_flag=None
					pass
				elif self.build_flag==OPTION_USE_PATROL:
					if self.selection:
						self.selection.has_bandit = True
						if self.current_bandit_tile: self.current_bandit_tile.has_bandit = False
						self.current_bandit_tile = self.selection
						self.clear_build_selection()
					else:
						self.show_player_available_bandit_tiles()
						self.await_selection()
				elif self.build_flag==OPTION_NATURAL_PAVIMENTUM:
					if self.selection:
						self.selection.set_owner(self.current_player)
						if not self.multiple_placement_flag:
							self.multiple_placement_flag = True
							self.show_current_player_available_roads()
						else:
							self.multiple_placement_flag = False
							self.clear_build_selection()
						self.ui_needs_update = True
						self.selection = None
					else:
						self.show_current_player_available_roads()
						self.await_selection()
				elif self.build_flag==OPTION_BOUNTIFUL_HARVEST:
					if self.selection:
						print("Resource selected")
						self.current_player.inventory[self.selection] = self.current_player.inventory[self.selection] + 2
						self.clear_build_selection()
					else:
						self.await_selection()
				elif self.build_flag==OPTION_CLAIMED_PRODUCT:
					if self.selection:
						print("Resource selected")
						self.current_player_steal_all_of_one_resource(self.selection)
						self.clear_build_selection()
					else:
						self.await_selection()
				elif self.build_flag==OPTION_END_TURN:
					self.phase=PHASE_END_TURN #Advance to next phase
					self.build_flag=None
		############
		#END TURN PHASE
		############
		elif self.phase == PHASE_END_TURN:
			#Make recently purchased action cards playable next turn
			for c in self.current_player.action_cards:
				c.playable = True
			self.current_player.played_action_card_this_turn = False

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

		elif self.phase == PHASE_END_GAME:
			raise ValueError("NOT IMPLEMENTED")

		return self.get_rendered_objects()

	def await_selection(self):
		self.selection = None
		self.awaiting_selection = True
		self.ui_needs_update = True
	def clear_selection(self):
		self.selection = None
		self.awaiting_selection = False
		self.ui_needs_update = True
	def clear_build_selection(self):
		self.clear_selection()
		self.build_flag = None

	def set_build_road_flag(self):
		print("Road flag set")
		self.build_flag = OPTION_BUILD_ROAD
	def set_build_town_flag(self):				self.build_flag = OPTION_BUILD_SETTLEMENT
	def set_build_capitol_flag(self):			self.build_flag = OPTION_BUILD_CITY
	def set_build_achievement_flag(self):		self.build_flag = OPTION_BUILD_ACHIEVEMENT
	def set_build_trade_requested_flag(self):	self.build_flag = OPTION_REQUEST_TRADE
	def set_build_end_turn_flag(self):			self.build_flag = OPTION_END_TURN
	def set_use_natural_pavimentum_flag(self):	self.build_flag = OPTION_NATURAL_PAVIMENTUM
	def set_use_bountiful_harvest_flag(self):	self.build_flag = OPTION_BOUNTIFUL_HARVEST
	def set_use_claimed_product_flag(self):		self.build_flag = OPTION_CLAIMED_PRODUCT
	def set_use_patrol_flag(self):				self.build_flag = OPTION_USE_PATROL
	def set_cancel_selection_flag(self):		self.selection = OPTION_CANCEL
	def check_player_build_road(self, player):
		"""Check if player can build a road"""
		return bool(get_available_roads(player))
	def check_player_build_town(self, player):
		"""Check if player can build a town"""
		return bool(get_available_land_nodes(self.nodes,player,True))
	def check_player_build_capitol(self, player):
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
	def check_player_option_availability_capitol(self, player):
		"""Check if player is able to upgrade a town"""
		if all((
				self.check_player_can_afford_purchase(player, RECIPE_KEY_CITY), #Check if player can afford to build
				self.check_player_build_capitol(player), #Check if player has a place to build a capitol
				self.phase is PHASE_BUILD_AND_TRADE,
			)):
			return True
		else:
			return False
	def check_player_option_availability_achievement(self, player):
		"""Check if player is able to build a achievement card"""
		if all((
				self.check_achievement_deck_has_cards(),
				self.check_player_can_afford_purchase(player, RECIPE_KEY_ACHIEVEMENT), #Check if player can afford to build
				self.phase is PHASE_BUILD_AND_TRADE,
			)):
			return True
		else:
			return False
	def check_player_option_availability_use_action_card(self, player):
		"""Check if player is able to use an action card"""
		return not player.played_action_card_this_turn
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
		if self.build_flag in [OPTION_USE_PATROL,OPTION_NATURAL_PAVIMENTUM,OPTION_CLAIMED_PRODUCT,OPTION_BOUNTIFUL_HARVEST]:return False
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
	def check_current_player_build_capitol(self): 						return self.check_player_build_capitol(self.current_player)
	def check_current_player_can_afford_purchase(self, purchase): 	return self.check_player_can_afford_purchase(self.current_player, purchase)
	def check_current_player_option_availability_road(self): 		return self.check_player_option_availability_road(self.current_player)
	def check_current_player_option_availability_town(self): 	return self.check_player_option_availability_town(self.current_player)
	def check_current_player_option_availability_capitol(self): 		return self.check_player_option_availability_capitol(self.current_player)
	def check_current_player_option_availability_achievement(self): return self.check_player_option_availability_achievement(self.current_player)
	def check_current_player_option_availability_use_action_card(self): return self.check_player_option_availability_use_action_card(self.current_player)
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
		if len(player.owned_nodes) >= self.min_roads_for_via_domini:
			if self.via_domini and not player is self.via_domini:
				if len(player.owned_nodes) > len(self.via_domini.owned_nodes):
					self.via_domini = player
					print(f"{get_player_friendly_name(player)} now holds Via Domini")
			else:
				self.via_domini = player
				print(f"{get_player_friendly_name(player)} now holds Via Domini")
	def player_make_purchase_town(self, player, node):
		self.player_make_purchase(player, RECIPE_KEY_SETTLEMENT)
		node.set_owner(player)

		if any([e.port for e in n.neighbor_edges]): #If the settlement was built on a port
			if self.get_player_port_count(player) >= self.min_ports_for_portum_domini:
				if self.portum_domini and not player is self.portum_domini:

					if self.get_player_port_count(player) > self.get_player_port_count(self.portum_domini):
						print(f"{get_player_friendly_name(player)} now holds Portum Domini")
						self.portum_domini = player
				else:
					print(f"{get_player_friendly_name(player)} now holds Portum Domini")
					self.portum_domini = player



	def player_make_purchase_capitol(self, player, node):
		self.player_make_purchase(player, RECIPE_KEY_CITY)
		node.upgrade()
	def player_make_purchase_achievement(self, player):
		self.player_make_purchase(player, RECIPE_KEY_ACHIEVEMENT)
		c = self.draw_achievement_card()
		if issubclass(type(c), PatrolCard): 		player.action_cards.append(c)
		elif issubclass(type(c), _BaseActionCard): 	player.action_cards.append(c)
		elif issubclass(type(c), _BaseGoalPointCard): player.achievement_cards.append(c)
	def current_player_make_purchase(self,purchase):		self.player_make_purchase(self.current_player,purchase)
	def current_player_make_purchase_road(self,edge):		self.player_make_purchase_road(self.current_player,edge)
	def current_player_make_purchase_town(self,node):	self.player_make_purchase_town(self.current_player,node)
	def current_player_make_purchase_capitol(self,node):		self.player_make_purchase_capitol(self.current_player,node)
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
	def get_bandit_location(self):
		for t in self.tiles:
			if t.has_bandit:
				return t
	def steal_random_resource(self,bandit_player,victim_player):
		inventory = []
		for r in RESOURCES:
			for i in range(victim_player.inventory[r]):
				inventory.append(r)
		if inventory:
			resource_to_steal = random.choice(inventory)
			victim_player.inventory[resource_to_steal] = victim_player.inventory[resource_to_steal] - 1
			bandit_player.inventory[resource_to_steal] = bandit_player.inventory[resource_to_steal] + 1
			self.set_current_message(f"{get_player_friendly_name(bandit_player)} stole {RESOURCE_MAP_INT_TO_NAME[resource_to_steal]} from {get_player_friendly_name(victim_player)}")
		else:
			self.set_current_message(f"There was nothing for {get_player_friendly_name(bandit_player)} to steal from {get_player_friendly_name(victim_player)}")
	def show_player_available_bandit_tiles(self):
		for t in self.tiles:
			if not issubclass(type(t), WaterTileMixin):
				t.enabled = t.owner and not t.has_bandit or t.resource_type is RESOURCE_WASTELAND
	def get_random_port_trade_deal(self): return random.choice(list(self.port_exchange_rates.keys()))
	def check_achievement_deck_has_cards(self):
		if self.unlimited_achievement_cards: return True
		if self.achievement_card_deck: return True
		return False
	def draw_achievement_card(self):
		if self.unlimited_achievement_cards:
			return random.choice(self.default_achievement_card_deck)
		else:
			if not self.achievement_card_deck: raise ValueError("Tried to draw an achievement card from an empty deck")
			choice = random.choice(self.achievement_card_deck)
			self.achievement_card_deck.remove(choice)
			return choice
	def player_use_action_card(self, player, action_card):
		if player.played_action_card_this_turn: raise ValueError(f"{player} attempted to use action card {action_card} despite already having used an action card this turn")
		if not action_card in player.action_cards: raise ValueError(f"{player} attempted to use action card {action_card} not currently in their inventory.")
		player.action_cards.remove(action_card)

		if issubclass(type(action_card), PatrolCard):
			self.set_use_patrol_flag()
			player.patrol_count+=1 #Increment the player's used patrol count
			if player.patrol_count > self.min_patrols_for_militum_dominus:
				if all(player.patrol_count > p for p in self.players if p):
					print(f"{get_player_friendly_name(player)} now holds Militum Dominus")
					self.militum_dominus = player
		elif issubclass(type(action_card), _BaseActionCard): 
			if type(action_card) is NaturalPavimentum: self.set_use_natural_pavimentum_flag()
			elif type(action_card) is BountifulHarvest:
				print("Bountiful Harvest flag set")
				self.set_use_bountiful_harvest_flag()
			elif type(action_card) is ClaimedProduct: self.set_use_claimed_product_flag()
		elif issubclass(type(action_card), _BaseGoalPointCard):
			raise ValueError(f"{player} attempted to use Goal Point card {action_card} as Action Card")
		player.played_action_card_this_turn = True
		self.ui_needs_update = True
	def current_player_use_action_card(self, action_card):
		return self.player_use_action_card(self.current_player, action_card)
	def player_steal_all_of_one_resource(self, player, resource):
		resource_count = 0
		for p in self.players:
			if not p is player:
				resource_count += p.inventory[resource]
				p.inventory[resource]=0
		player.inventory[resource] = player.inventory[resource] + resource_count
		self.set_current_message(f"{get_player_friendly_name(player)} collected {resource_count} {RESOURCE_MAP_INT_TO_NAME[resource]}")
	def current_player_steal_all_of_one_resource(self, resource):
		self.player_steal_all_of_one_resource(self.current_player, resource)

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
	def __init__(self,game,tile_edges,tile_nodes,owner=None,map_center=False,has_bandit=False):
		_BaseTileMixin.__init__(self, game, tile_edges, tile_nodes, owner)
		self.value = get_chip_number()
		self.has_bandit=has_bandit
		self.map_center=map_center
		self.resource_type=self.game.pick_random_resource_type(self.map_center)
		if self.resource_type is RESOURCE_WASTELAND:
			self.has_bandit = True
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
	def set_bandit(self):self.has_bandit = True
	def remove_bandit(self):self.has_bandit = False

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

#These are classes for program control
#And because later I want to implement
#A plugin system where action cards
#can have an on_play method that 
#allow the cards to do actions on the
#Game without modifying core parts
class _BaseAchievementCard:
	def __init__(self, name, text):
		self.name = name
		self.text = text
		self.playable = False #Flag so card can't be played same turn
		self.actionable = True #Actionable cards can be 'played' like a patrol card or action card

class _BaseActionCard(_BaseAchievementCard):
	def __init__(self, name, text):_BaseAchievementCard.__init__(self, name, text)
class PatrolCard(_BaseActionCard):
	def __init__(self):_BaseActionCard.__init__(self, "Patrol", "Move the bandit.")
class NaturalPavimentum (_BaseActionCard):
	def __init__(self):_BaseActionCard.__init__(self, "Natural Pavimentum", "Build two roads at no cost.")
class BountifulHarvest (_BaseActionCard):
	def __init__(self):_BaseActionCard.__init__(self, "Bountiful Harvest", "Receive two cards of your choice.")
class ClaimedProduct (_BaseActionCard):
	def __init__(self):_BaseActionCard.__init__(self, "Claimed Product", "Collect all of a selected resource from all players.")
# class CollectedTax (_BaseActionCard): #Steal one random resource from each person
# 	def __init__(self): _BaseActionCard.__init__(self)
# class RapidAdvancement (_BaseActionCard): #Instantly upgrade a town
# 	def __init__(self): _BaseActionCard.__init__(self)
# class MaritimeEstablishment (_BaseActionCard): #Create a port on an owned shore edge if in a valid location
# 	def __init__(self): _BaseActionCard.__init__(self)
# class ReformedLand (_BaseActionCard): #Reroll a tile value for a tile you own at least one node on
# 	def __init__(self): _BaseActionCard.__init__(self)
class _BaseGoalPointCard(_BaseAchievementCard):
	def __init__(self, name, text):
		_BaseAchievementCard.__init__(self, name, text)
		self.playable = True
		self.actionable = False
class Colosseum(_BaseGoalPointCard):
	def __init__(self):_BaseGoalPointCard.__init__(self,"Colosseum","Old School TV. +1 Goal Point.")
class CapitalHall(_BaseGoalPointCard):
	def __init__(self):_BaseGoalPointCard.__init__(self,"Capital Hall","Lotta big letters here. +1 Goal Point")
# class Church(_BaseGoalPointCard):
# 	def __init__(self):_BaseGoalPointCard.__init__(self,"Church")
class Bazaar(_BaseGoalPointCard):
	def __init__(self):_BaseGoalPointCard.__init__(self,"Bazaar","How Bazaar, how Bazaar. +1 Goal Point.")
class Academy(_BaseGoalPointCard):
	def __init__(self):_BaseGoalPointCard.__init__(self,"Academy","Get Learnt. +1 Goal Point")
# class Tower(_BaseGoalPointCard):
# 	def __init__(self):_BaseGoalPointCard.__init__(self,"Tower")
# class Tunnel(_BaseGoalPointCard):
# 	def __init__(self):_BaseGoalPointCard.__init__(self,"Tunnel")
class Observatory(_BaseGoalPointCard):
	def __init__(self):_BaseGoalPointCard.__init__(self,"Observatory","Why are there never any problems at an observatory?.. 'Cause things are always looking up. +1 Goal Point")

def get_achievement_deck():
	deck = [PatrolCard() for i in range(DEFAULT_ACHIEVEMENT_PATROL_COUNT)]
	for i in range(DEFAULT_NUM_EACH_TYPE_ACTION_CARDS):
		deck.extend([NaturalPavimentum(), BountifulHarvest(), ClaimedProduct()])
	for i in range(DEFAULT_NUM_EACH_TYPE_GOAL_CARDS):
		deck.extend([Colosseum(), CapitalHall(), Bazaar(), Academy(), Observatory()])
	return deck
import random

#PHASES
PHASE_SETUP	= 0
PHASE_DEAL	= 1
PHASE_BUILD	= 2

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


def pick_random_resource_type():
	return random.choice(RESOURCES)

def get_resource_color(resource):
	return RESOURCE_MAP_INT_TO_COLOR[resource]

class player:
	def __init__(self):
		self.board_pieces = None
		self.cards = None


class game:
	def __init__(self, radius):
		self.turn = 0
		self.phase = 0
		self.players = []
#PHASES
0 = SETUP
1 = ROLL
2 = BUILD




class player:
	def __init__(self):
		self.board_pieces = None
		self.cards = None


class game:
	def __init__(self, radius):
		self.turn = 0
		self.phase = 0
		self.players = []
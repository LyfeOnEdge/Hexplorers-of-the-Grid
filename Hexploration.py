import os, math, json, random
import ursina
from collections import deque

from modules.map_gen import MapMaker
from modules.settings import settings
from modules.entities import Node, Tile, Edge, Divider
from modules.UrsinaLighting import LitObject
from HexplorationEngine import Game, bluePlayer, greenPlayer, yellowPlayer,\
	purplePlayer, pinkPlayer, brownPlayer, redPlayer, grayPlayer, RESOURCES,\
	RESOURCE_MAP_INT_TO_NAME, PLAYER_FRIENDLY_NAMES, RECIPE_MAP_INT_TO_NAME

ursina.camera.mode = "orthoganol"
ursina.Text.default_resolution = 1080 * ursina.Text.size
ursina.Text.default_font = "assets/fonts/OpenSans-Bold.ttf"

os.makedirs("textures/temp", exist_ok = True)

class App(ursina.Ursina):
	def __init__(self, *args, **kwargs):
		ursina.Ursina.__init__(self, *args, **kwargs)

		self.game = Game()
		self.ui = UI(self)
		
		self.map = MapMaker(self.game, (0,0), settings.default_radius)
		self.map.generate_map()

		self.scene_objects = [] #List to track which 'pieces' need to be rendered on the board
		self.scene_entities = [] #List to hold rendered entities representing the objects

		self.origin = ursina.Entity(model='sphere', color=ursina.color.rgb(0,0,0), scale=0.000001, origin = (0,0), x=0,y=0,z=0)
		self.editor_camera = ursina.EditorCamera(enabled=True, ignore_paused=True, rotation=(55,0,0))

		# self.toggle_water_button = ursina.Button(
		# 	parent=ursina.camera.ui,
		# 	position = (-0.85,0),
		# 	on_click = self.map.toggle_water,
		# 	scale=0.035
		# )
		# self.toggle_grid_button = ursina.Button(
		# 	parent=ursina.camera.ui, 
		# 	position = (-0.85,-0.1),
		# 	on_click = self.map.toggle_grid,
		# 	scale=0.035
		# )
		# self.toggle_skybox_button = ursina.Button(
		# 	parent=ursina.camera.ui,
		# 	position = (-0.85,-0.2),
		# 	on_click = self.map.toggle_skybox,
		# 	scale=0.035
		# )

		# players = [bluePlayer(), greenPlayer(), redPlayer(), yellowPlayer(), purplePlayer(), pinkPlayer(), brownPlayer(), grayPlayer()]
		players = [bluePlayer(), greenPlayer()]
		self.game.start(players)

	def update(self):
		scene_objects = self.game.gameloop() #Function to be called every loop
		if self.game.ui_needs_update:
			self.scene_objects = scene_objects
			self.update_board_pieces()
			if not self.game.current_message == self.ui.displayed_message: self.ui.set_displayed_message(self.game.current_message)
			if not self.game.current_player == self.ui.current_player: self.ui.set_current_player(self.game.current_player)
			self.ui.update_inventory_display()
			self.game.ui_needs_update = False

	def update_board_pieces(self):
		for e in self.scene_entities: ursina.destroy(e)
		scene_objs = []
		for o in self.scene_objects:
			if o.owner:
				if type(o) is Node:
					model = "city" if o.upgraded else "settlement"
					e = LitObject(
						position=o.position-(0,0.1,0),
						model=model,
						color=o.owner.color,
						scale = settings.board_model_scale,
						ambientStrength=0.05,
						smoothness = 2,
						)
				elif type(o) is Edge:
					x_0, _, z_0 = o.node_a.position
					x_1, _, z_1 = o.node_b.position
					e = LitObject(
						position=o.position,
						model='road',
						color=o.owner.color,
						scale = settings.board_model_scale,
						ambientStrength=0.05,
						smoothness = 2,
						rotation_y = math.degrees(math.atan2(x_0-x_1,z_0-z_1))+90,
						y=settings.board_scale
						)
				elif type(o) is Tile:
					e = LitObject(
						position=o.position-(0,0.1,0),
						model='chip_beveled',
						color=ursina.rgb(200,200,200),
						scale = settings.board_model_scale*8,
						ambientStrength=0.05,
						smoothness = 2,
						)
					chip_text = ursina.Text(
						parent=ursina.scene,
						text=str(o.value),
						scale=22,
						size=40,
						position = o.position-(0,0.05,0),
						color=ursina.rgb(0,0,0),
						rotation_x = 90,
						origin=(0,0)
					)
					self.scene_entities.append(chip_text)
				self.scene_entities.append(e)		

class UI:
	def __init__(self, app):
		self.app = app
		self.message_que = deque()
		self.displayed_message = "Started"
		self.current_player = None
		self.player_menu_entities = []
		self.inventory_entities = []
		c = ursina.camera
		self.yscale = yscale = 0.15
		message_box_scale = 4
		minute_adjust = 0.01
		self.top_menu_box = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.1, aspect = c.aspect_ratio/2/yscale),
			color=ursina.color.black66,
			position=(0,0.5-minute_adjust),
			scale=(c.aspect_ratio/2,yscale),
			origin=(0,0.5)
		)
		self.message_box = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.1, aspect = c.aspect_ratio/3/(yscale/message_box_scale)),
			color=ursina.color.black50,
			position=(0,0.5-2*minute_adjust-yscale),
			scale=(c.aspect_ratio/3,yscale/message_box_scale),
			origin=(0,0.5)
		)
		self.bottom_menu_box = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.1, aspect = c.aspect_ratio/2/(yscale)),
			color=ursina.color.black66,
			position=(0,-0.5+minute_adjust),
			scale=(c.aspect_ratio/2,yscale),
			origin=(0,-0.5)
		)
		self.bottom_menu_box.z+=1
		self.item_box = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.1, aspect=ursina.camera.aspect_ratio/2/(yscale)*0.35),
			position = (-0.5*ursina.camera.aspect_ratio/2,self.bottom_menu_box.y),
			color= ursina.color.black50,
			scale=(ursina.camera.aspect_ratio/2*0.35,self.yscale),
			origin=(-0.5,-0.5)
		)

		recipe_card_width = c.aspect_ratio/2/3
		recipe_card_height = c.aspect_ratio/2/2

		self.recipe_card = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.1, aspect = 2/3),
			color=ursina.color.black66,
			position=(-(c.aspect_ratio*(1-minute_adjust))/2,0.5-minute_adjust),
			scale=(recipe_card_width,recipe_card_height),
			origin=(-0.5,0.5)
		)

		self.recipe_card_label = ursina.Text(
			parent=ursina.camera.ui,
			text="Recipes",
			origin=(0,-0.5),
			position=self.recipe_card.position,
			scale=0.75,
		)
		self.recipe_card_label.x += recipe_card_width/2
		self.recipe_card_label.y -= 4*minute_adjust
		self.recipe_card_label.z -= 0.2

		divider_w = 0.25
		divider_h = 0.0035

		self.recipe_divider = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.5, aspect=divider_w/divider_h),
			position = self.recipe_card_label.position,
			color= ursina.color.white66,
			scale=(divider_w,divider_h),
			origin=(0,-0.5),
		)
		self.recipe_divider.y -= 2*minute_adjust

		recipes = self.app.game.recipes
		recipes_keys = list(recipes.keys())
		for y in range(len(recipes_keys)):
			k = recipes_keys[y]
			recipe = recipes[k]
			recipe_keys = list(recipe.keys())

			recipe_name_text = ursina.Text(
				parent=ursina.camera.ui,
				text=RECIPE_MAP_INT_TO_NAME[k],
				origin=(0,0),
				position=self.recipe_card.position,
				color=ursina.rgb(255,255,255),
				scale = 0.5,
				rotation_z = -7,
				z = -0.2	
			)
			recipe_name_text.x += 0.15 * recipe_card_width 
			recipe_name_text.y -= (y+0.5)/len(recipes_keys) * recipe_card_height * 0.8 + 0.25*((recipe_card_height)/len(recipes_keys)) + 0.1 * recipe_card_height

			for x in range(len(recipe_keys)):
				r = recipe_keys[x]

				r_text = ursina.Text(
					parent=ursina.camera.ui,
					text=RESOURCE_MAP_INT_TO_NAME[r],
					origin=(0,0),
					position=self.recipe_card.position,
					color=ursina.rgb(*settings.ui_recipe_text_color),
					scale = 0.5,
					rotation_z = -7,
					z = -0.2	
				)
				r_text.x += (x+0.5)/len(recipe_keys) * recipe_card_width * 0.7 + 0.3 * recipe_card_width 
				r_text.y -= (y+0.5)/len(recipes_keys) * recipe_card_height * 0.8 + 0.1 * recipe_card_height
				r_x = ursina.Text(
					parent=ursina.camera.ui,
					text="X",
					origin=(0,0),
					position=r_text.position-ursina.Vec3(0,0.25*((recipe_card_height)/len(recipes_keys)),0),
					color=ursina.rgb(*settings.ui_recipe_text_color),
					scale = 0.75,
					rotation_z = 0,	
				)
				r_v = ursina.Text(
					parent=ursina.camera.ui,
					text=str(recipe[r]),
					origin=(0,0),
					position=r_x.position-ursina.Vec3(0,0.25*((recipe_card_height)/len(recipes_keys)),0),
					color=ursina.rgb(*settings.ui_recipe_text_color),
					scale = 1,
					rotation_z = -7,
				)

		self.item_box.z = 1
		self.resource_texts = {}
		self.resource_exes = {}
		self.resource_values = {}
		for i in range(len(RESOURCES)):
			r = RESOURCES[i]
			resource_text = ursina.Text(
				parent=ursina.camera.ui,
				text=RESOURCE_MAP_INT_TO_NAME[r],
				origin=(0,-0.5),
				position=self.item_box.position,
				color=ursina.rgb(*settings.ui_resource_color),
				scale = 0.75,
				rotation_z = -7,
				z = -0.2	
			)
			resource_text.x += (i+0.5) * (ursina.camera.aspect_ratio/2*0.35)/len(RESOURCES)
			resource_text.y += 1.0/ursina.camera.aspect_ratio/2*0.35
			self.resource_texts[r]=resource_text

			resource_x = ursina.Text(
				parent=ursina.camera.ui,
				text="X",
				origin=(0,-0.5),
				position=self.item_box.position,
				color=ursina.rgb(*settings.ui_resource_color),
				scale = 0.75,
				rotation_z = 0,
				z = -0.2	
			)
			resource_x.x += (i+0.5) * (ursina.camera.aspect_ratio/2*0.35)/len(RESOURCES)
			resource_x.y += 0.6/ursina.camera.aspect_ratio/2*0.35
			self.resource_exes[r]=resource_x

			resource_v = ursina.Text(
				parent=ursina.camera.ui,
				text="0",
				origin=(0,-0.5),
				position=self.item_box.position,
				color=ursina.rgb(*settings.ui_resource_color),
				scale = 1,
				rotation_z = -7,
				z = -0.2	
			)
			resource_v.x += (i+0.5) * (ursina.camera.aspect_ratio/2*0.35)/len(RESOURCES)
			resource_v.y += 0.2/ursina.camera.aspect_ratio/2*0.35
			self.resource_values[r]=resource_v

		self.message_ticker = ursina.Text(
			parent=self.message_box,
			text=self.displayed_message,
			origin=(0,0),
			position=(0,-0.5),
			scale_y=c.aspect_ratio/3/(yscale/message_box_scale),
			size=0.025,			
		)
		self.message_ticker.z -= 0.1
		self.player_name = ursina.Text(
			parent=ursina.camera.ui,
			text="#PLAYER_NAME",
			origin=(0,1),
			position=self.bottom_menu_box.position+(0,yscale,-0.2),
			scale=0.75,
		)
		self.divider = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.5, aspect=divider_w/divider_h),
			position = self.bottom_menu_box.position+(0,10*self.yscale/13,-0.2),
			color= ursina.color.white66,
			scale=(divider_w,divider_h),
			origin=(0,0),
		)
		self.action_box = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.1, aspect=ursina.camera.aspect_ratio/2/(yscale)*0.35),
			position = (0.5*ursina.camera.aspect_ratio/2,self.bottom_menu_box.y,1),
			color= ursina.color.black50,
			scale=(ursina.camera.aspect_ratio/2*0.35,self.yscale),
			origin=(0.5,-0.5)
		)
		self.action_box.disable()
		self.button_actions = {
			settings.end_turn_string : self.set_build_end_turn_flag,
			settings.build_road_string : self.set_build_road_flag,
			settings.build_settlement_string :self.set_build_settlement_flag,
			settings.build_city_string : self.set_build_city_flag,
			settings.build_dev_card_string: self.set_build_development_flag,
			settings.request_trade_string: self.set_build_trade_requested_flag,
		}
		self.button_check_functions = {
			settings.end_turn_string : self.app.game.check_current_player_option_availability_end_turn,
			settings.build_road_string : self.app.game.check_current_player_option_availability_road,
			settings.build_settlement_string :self.app.game.check_current_player_option_availability_settlement,
			settings.build_city_string : self.app.game.check_current_player_option_availability_city,
			settings.build_dev_card_string: self.app.game.check_current_player_option_availability_development,
			settings.request_trade_string: self.app.game.check_current_player_option_availability_trade,
		}
		self.action_buttons = {}
		self.dummy_buttons = {}
		self.button_texts = {}
		buttonkeys=list(self.button_actions.keys())
		for i in range(len(buttonkeys)):
			k = buttonkeys[i]
			b = ursina.Button(
				parent=ursina.camera.ui,
				position = self.action_box.position,
				on_click = self.button_actions[k],
				origin=(0,0),
				scale = (ursina.camera.aspect_ratio/2*0.35,self.yscale/(len(buttonkeys)+1)),
				radius=0.5,
			)
			b.y += (i+0.5)/(len(buttonkeys))*self.yscale
			b.x -= (ursina.camera.aspect_ratio/2*0.35)/2
			b.z -= 0.2
			db = ursina.Button(
				parent=ursina.camera.ui,
				position = b.position,
				origin=(0,0),
				scale=b.scale,
				# scale = (ursina.camera.aspect_ratio/2*0.35,self.yscale/(len(buttonkeys)+1)),
				radius=0.5,
				enabled=False
			)
			db.color = ursina.color.black66
			db.highlight_color = db.color
			t = ursina.Text(
				parent=ursina.camera.ui,
				position=b.position,
				scale =0.5,
				size=0.020,
				color=ursina.rgb(*settings.ui_inactive_color),
				text=k,
				origin=(0,0),
			)
			t.z -= 0.1
			self.action_buttons[k]=b
			self.dummy_buttons[k]=db
			self.button_texts[k]=t

		self.cancel_button = ursina.Button(
				parent=ursina.camera.ui,
				text="CANCEL",
				position = self.action_box.position,
				on_click = self.app.game.set_cancel_selection_flag,
				origin=(0.5,-0.5),
				scale = self.action_box.scale,
				radius=0.1,
				color=ursina.color.black66,
				enabled=False
			)

	def set_displayed_message(self, message):
		self.displayed_message = message
		self.message_ticker.text=message

	def set_current_player(self, player):
		self.current_player = player
		self.update_player_display()
		self.player_name.text=PLAYER_FRIENDLY_NAMES[type(player)]

	def update_player_display(self):
		for e in self.player_menu_entities: ursina.destroy(e)
		players = self.app.game.players
		for i in range(len(players)):
			if players[i] is self.current_player:
				color = ursina.color.white33
			else:
				color = ursina.color.black50
			player_box = ursina.Entity(
				parent=self.top_menu_box,
				model=ursina.Quad(radius=0.1, aspect=ursina.camera.aspect_ratio/2/self.yscale/len(players)*0.98/0.9),
				color=color,
				position=((i+0.5)/len(players)-0.5,-0.05),
				scale=(0.9/len(players),.9),
				origin=(0,0.5)
			)
			inner_box = ursina.Entity(
				parent=self.top_menu_box,
				model='settlement',
				color=players[i].color,
				position=player_box.position,
				scale=(0.025,0.025/self.yscale,0.025),
				origin=(0,0.5),
				rotation=(2,2,2),
			)
			inner_box.z -= 0.3
			inner_box.y -= 0.5
			self.player_menu_entities.append(player_box)
			self.player_menu_entities.append(inner_box)

	def set_build_end_turn_flag(self):	 self.app.game.set_build_end_turn_flag()
	def set_build_road_flag(self):		 self.app.game.set_build_road_flag()
	def set_build_settlement_flag(self): self.app.game.set_build_settlement_flag()
	def set_build_city_flag(self):		 self.app.game.set_build_city_flag()
	def set_build_development_flag(self):self.app.game.set_build_development_flag()
	def set_build_trade_requested_flag(self):self.app.game.set_build_trade_requested_flag()

	def update_inventory_display(self): #Update inventory counts
		for r in RESOURCES: self.resource_values[r].text = str(self.current_player.inventory[r])
		text_colors = [settings.ui_inactive_color, settings.ui_active_color]
		self.cancel_button.enabled = cancel_active = self.app.game.check_current_player_option_availability_cancel()
		for k in self.action_buttons.keys(): #update action buttons
			button_active = not self.app.game.build_flag and self.button_check_functions[k]()
			self.action_buttons[k].enabled = button_active and not cancel_active
			self.dummy_buttons[k].enabled = not button_active and not cancel_active	
			self.button_texts[k].color = ursina.rgb(*text_colors[button_active])
			self.button_texts[k].enabled = not cancel_active
app = App()
update = app.update #Set this so app.update gets called every loop, usually you would define a function
app.run()
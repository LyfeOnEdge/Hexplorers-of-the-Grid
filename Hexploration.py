import os, sys, math, json, random
import ursina
from collections import deque

from modules.map_gen import MapMaker
from modules.settings import settings
from modules.entities import Node, Tile, WaterTile, Edge, Divider
from modules.UrsinaLighting import LitObject
from modules.game_camera import EditorCamera
from modules.scrolled_menu import ScrolledMenu
from HexplorationEngine import Game, bluePlayer, greenPlayer, yellowPlayer,\
	purplePlayer, pinkPlayer, brownPlayer, redPlayer, grayPlayer, RESOURCES,\
	RESOURCE_MAP_INT_TO_NAME, PLAYER_FRIENDLY_NAMES, RECIPE_MAP_INT_TO_NAME,\
	PHASE_BUILD_AND_TRADE, RESOURCE_WASTELAND, ALL_TILE_TYPES, \
	RESOURCE_MAP_INT_TO_COLOR, BountifulHarvest, ClaimedProduct, \
	OPTION_NATURAL_PAVIMENTUM, OPTION_BOUNTIFUL_HARVEST, OPTION_CLAIMED_PRODUCT,\
	OPTION_USE_PATROL
ursina.window.vsync = False
ursina.window.center_on_screen()
ursina.camera.mode = "orthoganol"
ursina.Text.default_resolution = 1080 * ursina.Text.size
ursina.Text.default_font = "assets/fonts/OpenSans-Bold.ttf"

os.makedirs("textures/temp", exist_ok = True)

sqrt3 = math.sqrt(3)

from time import perf_counter
start_time = perf_counter()

class App(ursina.Ursina):
	def __init__(self, *args, **kwargs):
		ursina.Ursina.__init__(self, *args, **kwargs)

		self.last_update = self.app_start_time = perf_counter()

		self.game = Game()
		self.ui = UI(self)
		
		self.map = MapMaker(self.game, (0,0), settings.default_radius)
		self.map.generate_map()

		self.scene_objects = [] #List to track which 'pieces' need to be rendered on the board
		self.scene_entities = [] #List to hold rendered entities representing the objects

		self.editor_camera = EditorCamera(enabled=True, ignore_paused=True, rotation=(55,0,0))

		# self.toggle_water_button = ursina.Button(parent=ursina.camera.ui,position = (-0.85,-.2),on_click = self.map.toggle_water,scale=0.035)
		# # self.toggle_grid_button = ursina.Button(parent=ursina.camera.ui, position = (-0.85,-0.3),on_click = self.map.toggle_grid,scale=0.035)
		# self.toggle_skybox_button = ursina.Button(parent=ursina.camera.ui,position = (-0.85,-0.4),on_click = self.map.toggle_skybox,scale=0.035)
		players = [bluePlayer(), greenPlayer(), redPlayer(), yellowPlayer(), purplePlayer(), pinkPlayer(), brownPlayer(), grayPlayer()]
		# players = [bluePlayer(), greenPlayer()]
		num_players = 3

		self.game.start([players[p] for p in range(num_players)])

		self.bandit = LitObject(
			position=(0,-9999,0),
			model='bandit',
			color=ursina.rgb(50,50,50),
			scale=settings.board_scale,
			ambientStrength=1,
			smoothness = 2,
			cubemapIntensity=0.15,
			eternal=True,
			)

	def update(self):
		scene_objects = self.game.gameloop() #Function to be called every loop
		if self.game.ui_needs_update:
			print("Updating")
			# ursina.scene.clear()
			for e in ursina.scene.entities.copy():

				if not e.eternal:
					del e.model
					ursina.destroy(e)
			self.scene_objects = scene_objects
			self.update_board_pieces()
			if not self.game.current_message == self.ui.displayed_message: self.ui.set_displayed_message(self.game.current_message)
			if not self.game.current_player == self.ui.current_player: self.ui.set_current_player(self.game.current_player)
			self.ui.update_ui()
			self.game.ui_needs_update = False

	def update_board_pieces(self):
		board_parent = ursina.Entity(parent=ursina.scene)
		for o in self.scene_objects:
			if o.owner:
				if type(o) is Node:
					model = "capitol" if o.upgraded else "town"
					LitObject(
						parent=board_parent,
						position=o.position-(0,0.01,0),
						model=model,
						color=ursina.rgb(*o.owner.color),
						scale = settings.board_model_scale,
						ambientStrength=0.05,
						smoothness = 2,
						cubemapIntensity=0.15,
						)
				elif type(o) is Edge:
					x_0, _, z_0 = o.node_a.position
					x_1, _, z_1 = o.node_b.position
					LitObject(
						parent=board_parent,
						position=o.position-(0,0.01,0),
						model='road',
						color=ursina.rgb(*o.owner.color),
						scale = settings.board_model_scale,
						ambientStrength=0.05,
						smoothness = 2,
						rotation_y = math.degrees(math.atan2(x_0-x_1,z_0-z_1))+90,
						cubemapIntensity=0.15,
						)
				elif type(o) is Tile:
					if not o.resource_type is RESOURCE_WASTELAND:
						LitObject(
							parent=board_parent,
							position=o.position-(0,0.01,0),
							model='chip_beveled',
							color=ursina.rgb(200,200,200),
							scale = settings.board_model_scale*8,
							ambientStrength=0.05,
							smoothness = 2,
							cubemapIntensity=0.15,
							)
						ursina.Text(
							parent=board_parent,
							text=str(o.value),
							scale=22,
							size=40,
							position = o.position+(0,0.01+0.01*settings.board_scale,0),
							color=ursina.rgb(0,0,0),
							rotation_x = 90,
							origin=(0,0),
							cubemapIntensity=0.15,
							)

					if o.has_bandit:
						self.bandit.position = o.position-(0,0.1,0)
			if type(o) is WaterTile:
				for e in o.neighbor_edges:
					if e.port:
						x_0, _, z_0 = o.position
						x_1, _, z_1 = e.position
						pos = ursina.Vec3(e.position[0],1.05*settings.board_scale*settings.island_height_above_water,e.position[2])-(0,0.01,0)
						angle = math.degrees(math.atan2(x_0-x_1,z_0-z_1))
						LitObject(
							parent=board_parent,
							position=pos,
							model='port_chip',
							# color=ursina.rgb(*settings.port_color),
							texture="textures/sand.png",
							scale = settings.board_scale,
							ambientStrength=0.05,
							smoothness = 2,
							rotation_y = angle,
							cubemapIntensity=0.15,
							)
						ursina.Text(
							parent=board_parent,
							text=str(RESOURCE_MAP_INT_TO_NAME[e.port]),
							scale=13,
							size=40,
							position = ((x_0+x_1+x_1)/3,pos[1]+0.01+0.01*settings.board_scale,(z_0+z_1+z_1)/3), #Place text shifted towards land
							color=ursina.rgb(0,0,0),
							rotation_x = 90,
							origin=(0,0),
							rotation_y = angle,
						)
						ursina.Text(
							parent=board_parent,
							text=f"{self.game.port_exchange_rates[e.port]}:1",
							scale=14,
							size=40,
							position = ((x_0+x_0+x_1)/3,pos[1]+0.01+0.01*settings.board_scale,(z_0+z_0+z_1)/3), #Place text shifted towards tile
							color=ursina.rgb(0,0,0),
							rotation_x = 90,
							origin=(0,0),
							rotation_y = angle,
						)
		# merged_scene = merge_models(self.scene_entities, ignore_types=[ursina.Text])
		# model = combine(board_parent)
		# board_parent.combine()

	def exit(self):
		print("exiting")
		ursina.application.quit()


class UI:
	def __init__(self, app):
		self.app = app
		self.message_que = deque()
		self.displayed_message = "Started"
		self.current_player = None
		self.player_menu_entities = []
		self.inventory_entities = []
		c = ursina.camera
		self.yscale = yscale = settings.ui_menu_y_scale
		message_box_scale = 4
		self.minute_adjust=minute_adjust = 0.01
		self.top_menu_box = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.1, aspect = c.aspect_ratio/2/yscale),
			color=ursina.color.black66,
			position=(0,0.5-minute_adjust),
			scale=(c.aspect_ratio/2,yscale),
			origin=(0,0.5),
			add_to_scene_entities=False,
			eternal=True,
		)
		self.message_box = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.3, aspect = c.aspect_ratio/2.1/(yscale/message_box_scale)),
			color=ursina.color.white33,
			position=(0,0.5+1.6*minute_adjust-yscale),
			scale=(c.aspect_ratio/2-0.1*yscale,yscale/message_box_scale),
			origin=(0,0),
			add_to_scene_entities=False,
			eternal=True,
		)
		self.message_box.z -=0.1
		self.message_ticker = ursina.Text(
			text=self.displayed_message,
			origin=(0,0),
			position=self.message_box.position,
			scale = 0.65,
			size=0.025,
			add_to_scene_entities=False,
			eternal=True,
		)

		self.bottom_menu_box = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.1, aspect = c.aspect_ratio/2/(yscale)),
			color=ursina.color.black66,
			position=(0,-0.5+minute_adjust),
			scale=(c.aspect_ratio/2,yscale),
			origin=(0,-0.5),
			add_to_scene_entities=False,
			eternal=True,
		)
		self.bottom_menu_box.z+=1
		self.item_box = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.1, aspect=ursina.camera.aspect_ratio/2/(yscale)*0.35),
			position = (-0.5*ursina.camera.aspect_ratio/2,self.bottom_menu_box.y),
			color= ursina.color.black50,
			scale=(ursina.camera.aspect_ratio/2*0.35,self.yscale),
			origin=(-0.5,-0.5),
			add_to_scene_entities=False,
			eternal=True,
		)

		recipe_card_width = c.aspect_ratio/2/3
		recipe_card_height = 0.5-1.75*minute_adjust
		self.recipe_card = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.03, aspect = recipe_card_width/recipe_card_height),
			color=ursina.color.black66,
			position=(-(c.aspect_ratio*(1-minute_adjust))/2,0.5-minute_adjust),
			scale=(recipe_card_width,recipe_card_height),
			origin=(-0.5,0.5),
			add_to_scene_entities=False,
			eternal=True,
		)
		self.recipe_card_label = ursina.Text(
			parent=ursina.camera.ui,
			text="Recipes",
			origin=(0,-0.5),
			position=self.recipe_card.position,
			scale=0.75,
			add_to_scene_entities=False,
			eternal=True,
		)
		self.recipe_card_label.x += recipe_card_width/2
		self.recipe_card_label.y -= 4*minute_adjust
		self.recipe_card_label.z -= 0.2
		self.recipe_divider = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.5, aspect=settings.ui_divider_width/settings.ui_divider_height),
			position = self.recipe_card_label.position,
			color= ursina.color.white66,
			scale=(settings.ui_divider_width,settings.ui_divider_height),
			origin=(0,-0.5),
			add_to_scene_entities=False,
			eternal=True,
		)
		self.recipe_divider.y -= 2*minute_adjust
		recipes = self.app.game.recipes
		recipes_keys = list(recipes.keys())
		for y in range(len(recipes_keys)):
			k = recipes_keys[y]
			recipe = recipes[k]
			recipe_keys = list(recipe.keys())
			recipe_image = ursina.Entity(
				model='quad',
				texture=f'assets/textures/{RECIPE_MAP_INT_TO_NAME[k]}_icon.png',
				parent=ursina.camera.ui,
				scale=0.06,
				color=ursina.color.white,
				position = self.recipe_card.position,
				z=self.recipe_card.z-1,
				add_to_scene_entities=False,
				eternal=True
				)
			recipe_image.x += 0.175 * recipe_card_width 
			recipe_image.y -= (y+0.5)/len(recipes_keys) * recipe_card_height * 0.8 + 0.25*((recipe_card_height)/len(recipes_keys)) + 0.075 * recipe_card_height
			for x in range(len(recipe_keys)):
				r = recipe_keys[x]
				r_image = ursina.Entity(
					model='quad',
					texture=f'assets/textures/{RESOURCE_MAP_INT_TO_NAME[r]}_icon.png',
					parent=ursina.camera.ui,
					scale=0.035,
					color=ursina.rgb(*settings.ui_recipe_text_color),
					position = self.recipe_card.position,
					z=self.recipe_card.z-1,
					add_to_scene_entities=False,
					eternal=True
				)
				r_image.x += (x+0.5)/len(recipe_keys) * recipe_card_width * 0.7 + 0.3 * recipe_card_width 
				r_image.y -= (y+0.5)/len(recipes_keys) * recipe_card_height * 0.8 + 0.1 * recipe_card_height
				r_x = ursina.Text(
					parent=ursina.camera.ui,
					text="x",
					origin=(0,0),
					position=r_image.position-ursina.Vec3(0,0.20*((recipe_card_height)/len(recipes_keys)),0.1),
					color=ursina.rgb(*settings.ui_recipe_text_color),
					scale = 0.75,
					rotation_z = 0,
					add_to_scene_entities=False,
					eternal=True,
				)
				r_v = ursina.Text(
					parent=ursina.camera.ui,
					text=str(recipe[r]),
					origin=(0,0),
					position=r_x.position-ursina.Vec3(0,0.20*((recipe_card_height)/len(recipes_keys)),0.1),
					color=ursina.rgb(*settings.ui_recipe_text_color),
					scale = 0.8,
					rotation_z = -7,
					add_to_scene_entities=False,
					eternal=True,
				)
				
		self.item_box.z = 1
		self.resource_values = {}
		for i in range(len(RESOURCES)):
			r = RESOURCES[i]
			# r_text = ursina.Text(
			# 	parent=ursina.camera.ui,
			# 	text=RESOURCE_MAP_INT_TO_NAME[r],
			# 	origin=(0,-0.5),
			# 	position=self.item_box.position,
			# 	color=ursina.rgb(*settings.ui_resource_color),
			# 	scale = 0.75,
			# 	rotation_z = -7,
			# 	z = -0.2,
			# 	add_to_scene_entities=False,
			# 	eternal=True,
			# )
			# r_text.x += (i+0.5)*(ursina.camera.aspect_ratio/2*0.35)/len(RESOURCES)
			# r_text.y += 1.0/ursina.camera.aspect_ratio/2*0.35

			r_image = ursina.Entity(
				model='quad',
				texture=f'assets/textures/{RESOURCE_MAP_INT_TO_NAME[r]}_icon.png',
				parent=ursina.camera.ui,
				scale=0.035,
				z = -0.2,
				color=ursina.rgb(*settings.ui_recipe_text_color),
				position = self.item_box.position-(0,0,0.5),
				add_to_scene_entities=False,
				eternal=True,
			)
			r_image.x += (i+0.5)*(ursina.camera.aspect_ratio/2*0.35)/len(RESOURCES)
			r_image.y += 1.0/ursina.camera.aspect_ratio/2*0.375
			



			r_x = ursina.Text(
				parent=ursina.camera.ui,
				text="x",
				origin=(0,-0.5),
				position=r_image.position-(0,0.4/ursina.camera.aspect_ratio/2*0.35,0.5),
				color=ursina.rgb(*settings.ui_resource_color),
				scale = 0.75,
				add_to_scene_entities=False,
				eternal=True,
			)
			r_v = ursina.Text(
				parent=ursina.camera.ui,
				text="0",
				origin=(0,-0.5),
				position=r_x.position-(0,0.4/ursina.camera.aspect_ratio/2*0.35,0.5),
				color=ursina.rgb(*settings.ui_resource_color),
				scale = 1,
				rotation_z = -7,
				add_to_scene_entities=False,
				eternal=True,
			)
			self.resource_values[r]=r_v
		self.player_name = ursina.Text(
			parent=ursina.camera.ui,
			text="#PLAYER_NAME",
			origin=(0,1),
			position=self.bottom_menu_box.position+(0,yscale,-0.2),
			scale=0.75,
			add_to_scene_entities=False,
			eternal=True,
		)
		self.divider = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.5, aspect=settings.ui_divider_width/settings.ui_divider_height),
			position = self.bottom_menu_box.position+(0,self.yscale - 3.75 * self.minute_adjust,-0.2),
			color= ursina.color.white66,
			scale=(settings.ui_divider_width,settings.ui_divider_height),
			origin=(0,0),
			add_to_scene_entities=False,
			eternal=True,
		)
		self.action_box = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.1, aspect=ursina.camera.aspect_ratio/2/(yscale)*0.35),
			position = (0.5*ursina.camera.aspect_ratio/2,self.bottom_menu_box.y,1),
			color= ursina.color.black50,
			scale=(ursina.camera.aspect_ratio/2*0.35,self.yscale),
			origin=(0.5,-0.5),
			add_to_scene_entities=False,
			eternal=True,
		)
		self.action_box.disable()
		self.button_actions = {
			settings.exchange_resources_string: self.show_exchange_source_menu_for_current_player,
			settings.build_road_string : self.set_build_road_flag,
			settings.build_town_string :self.set_build_town_flag,
			settings.build_capitol_string : self.set_build_capitol_flag,
			settings.build_dev_card_string: self.set_build_achievement_flag,
			settings.request_trade_string: self.set_build_trade_requested_flag,
		}
		self.button_check_functions = {	
			settings.build_road_string : self.app.game.check_current_player_option_availability_road,
			settings.build_town_string :self.app.game.check_current_player_option_availability_town,
			settings.build_capitol_string : self.app.game.check_current_player_option_availability_capitol,
			settings.build_dev_card_string: self.app.game.check_current_player_option_availability_achievement,
			settings.request_trade_string: self.app.game.check_current_player_option_availability_trade,
			settings.exchange_resources_string: self.check_current_player_option_availability_exchange,
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
				eternal=True,
			)
			b.y += (i+0.5)/(len(buttonkeys))*self.yscale
			b.x -= (ursina.camera.aspect_ratio/2*0.35)/2
			b.z -= 0.2
			db = ursina.Button(
				parent=ursina.camera.ui,
				position = b.position,
				origin=(0,0),
				scale=b.scale,
				radius=0.5,
				enabled=False,
				color=ursina.color.black66,
				highlight_color=ursina.color.black66,
				eternal=True,
			)
			t = ursina.Text(
				parent=ursina.camera.ui,
				position=b.position-(0,0,0.1),
				scale =0.5,
				size=0.020,
				color=ursina.rgb(*settings.ui_inactive_color),
				text=k,
				origin=(0,0),
				eternal=True,
			)
			self.action_buttons[k],self.dummy_buttons[k],self.button_texts[k]=b,db,t
		self.cancel_button = ursina.Button(
				parent=ursina.camera.ui,
				text="CANCEL",
				position = self.action_box.position,
				on_click = self.set_cancel_selection_flag,
				origin=(0.5,-0.5),
				scale = self.action_box.scale,
				radius=0.1,
				color=ursina.color.black66,
				enabled=False,
				eternal=True,
			)
		self.end_turn_button = ursina.Button(
				parent=ursina.camera.ui,
				text=settings.end_turn_string,
				position = self.bottom_menu_box.position,
				on_click = self.set_build_end_turn_flag,
				origin=(0,-0.5),
				scale = (settings.ui_divider_width,2*self.yscale/(len(buttonkeys)+1)+self.minute_adjust),
				radius=0.2,
				color=ursina.color.black66,
				enabled=False,
				eternal=True,
			)


		self.exchange_source_menu = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.1, aspect = 2),
			color=ursina.color.black90,
			position=(0,0),
			scale=(1/2,1/4),
			origin=(0,0),
			add_to_scene_entities=False,
			eternal=True,
		)
		self.exchange_source_menu_texts = {}
		self.exchange_source_menu_values = {}
		self.exchange_source_menu_buttons = {}
		self.exchange_source_menu_dummy_buttons = {}
		self.exchange_source_menu_entities = [self.exchange_source_menu]
		for i in range(len(RESOURCES)):
			r = RESOURCES[i]
			r_text = ursina.Text(
				parent=ursina.camera.ui,
				text=RESOURCE_MAP_INT_TO_NAME[r],
				origin=(0,-0.5),
				position=self.exchange_source_menu.position-(1/4,6/64,0),
				color=ursina.rgb(*settings.ui_resource_color),
				scale = 0.75,
				rotation_z = -7,
				z = -0.2,
				add_to_scene_entities=False,
				eternal=True,
			)
			r_text.x += (i+0.5)*(1/2)/len(RESOURCES)
			r_text.y += 1/8
			r_x = ursina.Text(
				parent=ursina.camera.ui,
				text="X",
				origin=(0,-0.5),
				position=r_text.position-(0,0.4/1/8,0),
				color=ursina.rgb(*settings.ui_resource_color),
				scale = 0.75,
				add_to_scene_entities=False,
				eternal=True,
			)
			r_v = ursina.Text(
				parent=ursina.camera.ui,
				text="0",
				origin=(0,-0.5),
				position=r_x.position-(0,0.4/1/8,0),
				color=ursina.rgb(*settings.ui_resource_color),
				scale = 1,
				rotation_z = -7,
				add_to_scene_entities=False,
				eternal=True,
			)
			r_b = ursina.Button(
				parent=ursina.camera.ui,
				position = r_v.position-(0,0.2/1/8,0),
				model=ursina.Quad(radius=0.3, aspect = 0.05/0.035),
				origin=(0,0),
				scale=(0.05, 0.035),
				text="*",
				text_color=settings.ui_active_color,
				color=ursina.color.white33,
				highlight_color=ursina.color.white66,
				add_to_scene_entities=False,
				eternal=True,
			)
			r_db = ursina.Button(
				parent=ursina.camera.ui,
				position = r_b.position,
				model=ursina.Quad(radius=0.3, aspect = 0.05/0.035),
				origin=(0,0),
				scale=(0.05, 0.035),
				text="*",
				enabled=False,
				color=ursina.color.white10,
				highlight_color=ursina.color.white10,
				add_to_scene_entities=False,
				eternal=True,
			)
			r_db.text_color=settings.ui_inactive_color

			self.exchange_source_menu_texts[r], self.exchange_source_menu_values[r], self.exchange_source_menu_buttons[r], self.exchange_source_menu_dummy_buttons[r] =r_text, r_v, r_b, r_db
			self.exchange_source_menu_entities.extend([r_text, r_v, r_x, r_db, r_b])

		exchange_source_label = ursina.Text(
			parent=ursina.camera.ui,
			text="Select exchange material source",
			origin=(0,1),
			position=self.exchange_source_menu.position+(0,1/8,0),
			scale=0.75,
			z = -0.2,
			add_to_scene_entities=False,
			eternal=True,
		)
		exchange_source_divider = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.5, aspect=settings.ui_divider_width/settings.ui_divider_height),
			position = self.exchange_source_menu.position+(0,5/64,0),
			color= ursina.color.white66,
			scale=(settings.ui_divider_width,settings.ui_divider_height),
			origin=(0,0),
			z = -0.2,
			add_to_scene_entities=False,
			eternal=True,
		)
		self.exchange_source_menu_entities.extend([exchange_source_label, exchange_source_divider])

		for e in self.exchange_source_menu_entities: e.enabled = False

		self.exchange_dest_menu = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.1, aspect = 4),
			color=ursina.color.black90,
			position=(0,0),
			scale=(1/2,1/8),
			origin=(0,0),
			add_to_scene_entities=False,
			eternal=True,
		)
		self.exchange_dest_menu_buttons = []
		self.exchange_dest_menu_entities = [self.exchange_dest_menu]
		for i in range(len(RESOURCES)-1):
			b = ursina.Button(
				parent=ursina.camera.ui,
				position = self.exchange_dest_menu.position-(1/4,3/128,0.4),
				model=ursina.Quad(radius=0.3, aspect = 1/2/len(RESOURCES)/0.035),
				origin=(0,0),
				scale=(1/2/len(RESOURCES), 0.035),
				text="*",
				text_color=settings.ui_active_color,
				color=ursina.color.white33,
				highlight_color=ursina.color.white66,
				eternal=True,
			)
			b.x += (i+0.5)*(1/2)/(len(RESOURCES)-1)
			self.exchange_dest_menu_entities.extend([b])
			self.exchange_dest_menu_buttons.append(b)

		exchange_dest_label = ursina.Text(
			parent=ursina.camera.ui,
			text="Select resource to receive",
			origin=(0,1),
			position=self.exchange_dest_menu.position+(0,1/16,0),
			scale=0.75,
			z = -0.2,
			add_to_scene_entities=False,
			eternal=True,
		)
		exchange_dest_divider = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.5, aspect=settings.ui_divider_width/settings.ui_divider_height),
			position = self.exchange_dest_menu.position+(0,1/64,0),
			color= ursina.color.white66,
			scale=(settings.ui_divider_width,settings.ui_divider_height),
			origin=(0,0),
			z = -0.2,
			add_to_scene_entities=False,
			eternal=True,
		)
		self.exchange_dest_menu_entities.extend([exchange_dest_label, exchange_dest_divider])
		for e in self.exchange_dest_menu_entities: e.enabled = False



		self.select_resource_menu = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.1, aspect = 4),
			color=ursina.color.black90,
			position=(0,0),
			scale=(1/2,1/8),
			origin=(0,0),
			add_to_scene_entities=False,
			eternal=True,
		)
		self.select_resource_menu_buttons = []
		self.select_resource_menu_entities = [self.select_resource_menu]
		for i in range(len(RESOURCES)):
			b = ursina.Button(
				parent=ursina.camera.ui,
				position = self.select_resource_menu.position-(1/4,3/128,0.4),
				model=ursina.Quad(radius=0.3, aspect = 1/2/(len(RESOURCES)+1)/0.035),
				origin=(0,0),
				scale=(1/2/(len(RESOURCES)+1), 0.035),
				text=RESOURCE_MAP_INT_TO_NAME[RESOURCES[i]],
				text_color=settings.ui_active_color,
				color=ursina.color.white33,
				highlight_color=ursina.color.white66,
				on_click=lambda i=i: self.make_resource_selection(RESOURCES[i]),
				eternal=True,
			)
			b.x += (i+0.5)*(1/2)/(len(RESOURCES))
			self.select_resource_menu_entities.extend([b])
			self.select_resource_menu_buttons.append(b)

		select_resource_label = ursina.Text(
			parent=ursina.camera.ui,
			text="Select resource to take / receive",
			origin=(0,1),
			position=self.select_resource_menu.position+(0,1/16,0),
			scale=0.75,
			z = -0.2,
			eternal=True
		)
		select_resource_divider = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.5, aspect=settings.ui_divider_width/settings.ui_divider_height),
			position = self.select_resource_menu.position+(0,1/64,0),
			color= ursina.color.white66,
			scale=(settings.ui_divider_width,settings.ui_divider_height),
			origin=(0,0),
			z = -0.2,
			eternal=True
		)
		self.select_resource_menu_entities.extend([select_resource_label, select_resource_divider])
		for e in self.select_resource_menu_entities: e.enabled = False

		self.legend_card = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.deepcopy(self.recipe_card.model),
			color=ursina.color.black66,
			position=(-(ursina.camera.aspect_ratio*(1-minute_adjust))/2,-0.5*minute_adjust),
			scale=(recipe_card_width,recipe_card_height),
			origin=(-0.5,0.5),
			add_to_scene_entities=False,
			eternal=True,
		)
		self.legend_card_label = ursina.Text(
			parent=ursina.camera.ui,
			text="Legend",
			origin=(0,-0.5),
			position=self.legend_card.position,
			scale=0.75,
			add_to_scene_entities=False,
			eternal=True,
		)
		self.legend_card_label.x += recipe_card_width/2
		self.legend_card_label.y -= 4*minute_adjust
		self.legend_card_label.z -= 0.2
		self.legend_divider = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.5, aspect=settings.ui_divider_width/settings.ui_divider_height),
			position = self.legend_card_label.position,
			color= ursina.color.white66,
			scale=(settings.ui_divider_width,settings.ui_divider_height),
			origin=(0,-0.5),
			add_to_scene_entities=False,
			eternal=True,
		)
		self.legend_divider.y -= 2*minute_adjust
		num_types = len(ALL_TILE_TYPES)
		second_row = int(num_types/2)
		first_row = num_types - second_row
		x = ursina.camera.aspect_ratio*minute_adjust
		width = settings.ui_divider_width
		offset = 0.5 * (recipe_card_width - width)
		if first_row == second_row:
			hexagon_scale = width/(first_row)/2
		else:
			hexagon_scale = width/(first_row-0.5)/2
		for i in range(first_row): 
			t = ursina.Entity(
				parent=ursina.camera.ui,
				model="hexagon_flat",
				position = (-(ursina.camera.aspect_ratio*(1-minute_adjust))/2+sqrt3*((i+0.5)*hexagon_scale)+offset, self.legend_divider.position.y-(sqrt3/2+0.5)*hexagon_scale, self.legend_card.z+0.1),
				# position = self.recipe_divider.position + (sqrt3*(i*hexagon_scale)-ursina.camera.aspect_ratio*(0.25-minute_adjust), 0, 0),
				color=ursina.rgb(*RESOURCE_MAP_INT_TO_COLOR[ALL_TILE_TYPES[i]]),
				scale=hexagon_scale*0.95,
				origin=(0,0),
				rotation_x=(-90),
				add_to_scene_entities=False,
				eternal=True
			)
			f = ursina.Entity(
				parent=ursina.camera.ui,
				model="hexagon_frame",
				position = t.position - (0,0,0.2),
				color=ursina.color.white66,
				scale=hexagon_scale,
				origin=(0,0),
				rotation_x=(-90),
				add_to_scene_entities=False,
				eternal=True
			)
			
			if os.path.isfile(f'assets/textures/{RESOURCE_MAP_INT_TO_NAME[ALL_TILE_TYPES[i]]}_icon.png'):
				r_image = ursina.Entity(
					model='quad',
					texture=f'assets/textures/{RESOURCE_MAP_INT_TO_NAME[ALL_TILE_TYPES[i]]}_icon.png',
					parent=ursina.camera.ui,
					scale=0.035,
					color=ursina.rgb(*settings.ui_recipe_text_color),
					position = f.position - (0,0,0.1),
					add_to_scene_entities=False,
					eternal=True
				)
			else:
				txt = ursina.Text(
					parent=ursina.camera.ui,
					text=RESOURCE_MAP_INT_TO_NAME[ALL_TILE_TYPES[i]],
					origin=(0,0),
					position=f.position - (0,0,0.1),
					color=ursina.color.white,
					scale = 0.5,
					rotation_z = -7,
					add_to_scene_entities=False,
					eternal=True
				)
		for i in range(second_row): 
			t = ursina.Entity(
				parent=ursina.camera.ui,
				model="hexagon_flat",
				position = (-(ursina.camera.aspect_ratio*(1-minute_adjust))/2+sqrt3*((i+1)*hexagon_scale)+offset, self.legend_divider.position.y-(sqrt3/2+2)*hexagon_scale, self.legend_card.z+0.1),
				color=ursina.rgb(*RESOURCE_MAP_INT_TO_COLOR[ALL_TILE_TYPES[i+first_row]]),
				scale=hexagon_scale*0.95,
				origin=(0,0),
				rotation_x=(-90),
				add_to_scene_entities=False,
				eternal=True
			)
			f = ursina.Entity(
				parent=ursina.camera.ui,
				model="hexagon_frame",
				position = t.position - (0,0,0.2),
				color=ursina.color.white66,
				scale=hexagon_scale,
				origin=(0,0),
				rotation_x=(-90),
				add_to_scene_entities=False,
				eternal=True
			)
			if os.path.isfile(f'assets/textures/{RESOURCE_MAP_INT_TO_NAME[ALL_TILE_TYPES[i+first_row]]}_icon.png'):
				r_image = ursina.Entity(
					model='quad',
					texture=f'assets/textures/{RESOURCE_MAP_INT_TO_NAME[ALL_TILE_TYPES[i+first_row]]}_icon.png',
					parent=ursina.camera.ui,
					scale=0.035,
					color=ursina.rgb(*settings.ui_recipe_text_color),
					position = f.position - (0,0,0.1),
					add_to_scene_entities=False,
					eternal=True
				)
			else:
				txt = ursina.Text(
					parent=ursina.camera.ui,
					text=RESOURCE_MAP_INT_TO_NAME[ALL_TILE_TYPES[i+first_row]],
					origin=(0,0),
					position=f.position - (0,0,0.1),
					color=ursina.color.white,
					scale = 0.5,
					rotation_z = -7,
					add_to_scene_entities=False,
					eternal=True
				)

		gamerules = {
			"Bandit Enabled" : str(self.app.game.bandit_enabled),
			"Desert Enabled" : str(self.app.game.desert_enabled),
			"Desert In Center" : str(self.app.game.desert_enabled),
			"Limited Tile Pool" : str(self.app.game.limited_tile_pool),
			"Limited Achievement Cards" : str(not self.app.game.unlimited_achievement_cards),
			"Discard on 7 roll" : str(self.app.game.discard_on_7),
			"Roads for Via Domini" : str(self.app.game.min_roads_for_via_domini),
			"Ports for Portum Domini" : str(self.app.game.min_ports_for_portum_domini),
			"Patrols for Militum Dominus" : str(self.app.game.min_patrols_for_militum_dominus),
		}

		keys = list(gamerules.keys())
		y = self.legend_divider.position.y-(4*sqrt3+1)*hexagon_scale
		text = ""
		for g in range(len(keys)):
			text+=f"{keys[g]} : {gamerules[keys[g]].upper()}\n"
		txt = ursina.Text(
			parent=ursina.camera.ui,
			text=text,
			origin=(-0.5,0.5),
			position=(-(ursina.camera.aspect_ratio*(1-minute_adjust))/2+offset,y+(recipe_card_height+y),self.legend_card.z-0.1),
			color=ursina.color.white,
			scale = 0.6,
			ignore = True,
			eternal=True,
		)
		# for g in range(len(keys)):
		# 	txt = ursina.Text(
		# 		parent=ursina.camera.ui,
		# 		text=f"{keys[g]} : {gamerules[keys[g]].upper()}",
		# 		origin=(-0.5,0),
		# 		position=(-(ursina.camera.aspect_ratio*(1-minute_adjust))/2+offset,y+(g/len(keys))*(recipe_card_height+y),self.legend_card.z-0.1),
		# 		color=ursina.color.white,
		# 		scale = 0.55,
		# 		ignore = True,
		# 	)

		self.scoreboard_card = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.deepcopy(self.recipe_card.model),
			color=ursina.color.black66,
			position=((c.aspect_ratio*(1-minute_adjust))/2-self.recipe_card.scale.x,0.5-minute_adjust,-1),
			scale=self.recipe_card.scale,
			origin=(-0.5,0.5),
			ignore = True,
			eternal=True,
		)
		self.scoreboard_card_label = ursina.Text(
			parent=ursina.camera.ui,
			text="Scoreboard",
			origin=(0,-0.5),
			position=self.scoreboard_card.position,
			scale=0.75,
			ignore = True,
			eternal=True,
		)
		self.scoreboard_card_label.x += recipe_card_width/2
		self.scoreboard_card_label.y -= 4*minute_adjust
		self.scoreboard_card_label.z -= 0.4
		self.scoreboard_divider = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.5, aspect=settings.ui_divider_width/settings.ui_divider_height),
			position = self.scoreboard_card_label.position - (0,2*minute_adjust,0),
			color= ursina.color.white66,
			scale=(settings.ui_divider_width,settings.ui_divider_height),
			origin=(0,-0.5),
			add_to_scene_entities=False,
			eternal=True,
		)

		self.scoreboard_lowerdivider = None #Built in update scoreboard
		self.scoreboard_leader_text = None #Built in update scoreboard
		self.scoreboard_entities = []
		self.update_scoreboard()

		self.actioncard_card = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.deepcopy(self.recipe_card.model),
			color=ursina.color.black66,
			position=((c.aspect_ratio*(1-minute_adjust))/2-self.recipe_card.scale.x,-0.5*minute_adjust,self.scoreboard_divider.z+10),
			scale=self.recipe_card.scale,
			origin=(-0.5,0.5),
			add_to_scene_entities=False,
			eternal=True,
		)
		self.actioncard_card_label = ursina.Text(
			parent=ursina.camera.ui,
			text="Action Cards",
			origin=(0,-0.5),
			position=self.actioncard_card.position,
			scale=0.75,
			add_to_scene_entities=False,
			eternal=True,
		)
		self.actioncard_card_label.x += recipe_card_width/2
		self.actioncard_card_label.y -= 4*minute_adjust
		self.actioncard_card_label.z -= 0.2
		self.actioncard_divider = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.5, aspect=settings.ui_divider_width/settings.ui_divider_height),
			position = self.actioncard_card_label.position,
			color= ursina.color.white66,
			scale=(settings.ui_divider_width,settings.ui_divider_height),
			origin=(0,-0.5),
			add_to_scene_entities=False,
			eternal=True,
		)
		self.actioncard_divider.y -= 2*minute_adjust
		self.actioncard_menu = None #Gets generated each redraw

		self.actioncard_card_achievement_label = ursina.Text(
			parent=ursina.camera.ui,
			text="Achievement Cards",
			origin=(0,-0.5),
			position=self.actioncard_card.position-(0,0.5*self.actioncard_card.scale.y,0),
			scale=0.75,
			add_to_scene_entities=False,
			eternal=True,
		)
		self.actioncard_card_achievement_label.x += recipe_card_width/2
		self.actioncard_card_achievement_label.y -= 3*minute_adjust
		self.actioncard_card_achievement_label.z -= 0.2
		self.actioncard_achievement_divider = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.5, aspect=settings.ui_divider_width/settings.ui_divider_height),
			position = self.actioncard_card_achievement_label.position,
			color= ursina.color.white66,
			scale=(settings.ui_divider_width,settings.ui_divider_height),
			origin=(0,-0.5),
			add_to_scene_entities=False,
			eternal=True,
		)
		self.actioncard_achievement_divider.y -= 2*minute_adjust
		self.actioncard_achievement_menu = None #Gets generated each redraw


		self.acknowledgement_menu = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.1, aspect = 2),
			color=ursina.color.black90,
			position=(0,0),
			scale=(1/2,1/4),
			origin=(0,0),
			add_to_scene_entities=False,
			eternal=True,
			enabled=False
		)
		self.acknowledgement_text = ursina.Text(
			parent=ursina.camera.ui,
			text="Game Completed",
			origin=(0,1),
			position=self.acknowledgement_menu.position+(0,0.33*self.acknowledgement_menu.scale.y,0),
			scale=2,
			z = -0.2,
			add_to_scene_entities=False,
			eternal=True,
			enabled=False
		)
		self.acknowledgement_button = ursina.Button(
			parent=ursina.camera.ui,
			position = self.acknowledgement_menu.position-(0,0.33*self.acknowledgement_menu.scale.y,0),
			model=ursina.Quad(radius=0.3, aspect = 0.75*self.acknowledgement_menu.scale.x/0.035),
			origin=(0,0),
			scale=(0.75*self.acknowledgement_menu.scale.x, 0.035),
			text="Continue.",
			color=ursina.color.white10,
			highlight_color=ursina.color.white10,
			add_to_scene_entities=False,
			eternal=True,
			on_click= self.app.exit,
			enabled=False
		)
		self.acknowledgement_menu_entities = [self.acknowledgement_menu, self.acknowledgement_text, self.acknowledgement_button]


		exchange_source_label = ursina.Text(
			parent=ursina.camera.ui,
			text="Select exchange material source",
			origin=(0,1),
			position=self.exchange_source_menu.position+(0,1/8,0),
			scale=0.75,
			z = -0.2,
			add_to_scene_entities=False,
			eternal=True,
		)
		exchange_source_divider = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.5, aspect=settings.ui_divider_width/settings.ui_divider_height),
			position = self.exchange_source_menu.position+(0,5/64,0),
			color= ursina.color.white66,
			scale=(settings.ui_divider_width,settings.ui_divider_height),
			origin=(0,0),
			z = -0.2,
			add_to_scene_entities=False,
			eternal=True,
		)
		self.exchange_source_menu_entities.extend([exchange_source_label, exchange_source_divider])

		for e in self.exchange_source_menu_entities: e.enabled = False

	def set_displayed_message(self, message):
		self.displayed_message = message
		self.message_ticker.text=message

	def set_current_player(self, player):
		self.current_player = player
		self.player_name.text=PLAYER_FRIENDLY_NAMES[type(player)]

	def player_use_action_card(self, player, action_card):
		if type(action_card) in [BountifulHarvest, ClaimedProduct]: self.show_select_resource_menu()
		return self.app.game.player_use_action_card(player, action_card)

	def current_player_use_action_card(self, action_card):
		return self.player_use_action_card(self.current_player, action_card)

	def update_player_display(self):
		players = self.app.game.players
		for i in range(len(players)):
			if players[i] is self.current_player:
				color = ursina.color.white33
			else:
				color = ursina.color.black50
			player_box = ursina.Entity(
				parent=self.top_menu_box,
				model=ursina.Quad(radius=0.1, aspect=ursina.camera.aspect_ratio/2/self.yscale/len(players)/0.60),
				color=color,
				position=((i+0.5)/len(players)-0.5,-0.05,self.top_menu_box.z-0.3),
				scale=(1/len(players)-0.1*self.yscale,.60),
				origin=(0,0.5),
			)
			inner_box = ursina.Entity(
				parent=self.top_menu_box,
				model='quad',
				texture='assets/textures/town_icon.png',
				color=ursina.rgb(*players[i].color),
				position=player_box.position-(0,0,0.1),
				scale=(0.5/(ursina.camera.aspect_ratio/2/self.yscale),0.5),
				origin=(0,0.5),
				# rotation=(2,2,2),
			)
			# inner_box = ursina.Entity(
			# 	parent=self.top_menu_box,
			# 	texture='assets/textures/town_icon.png',
			# 	color=ursina.rgb(*players[i].color),
			# 	position=player_box.position-(0,0.5,0.3),
			# 	scale=(1,1),
			# 	origin=(0,0),
			# 	# rotation=(2,2,2),
			# )
			self.player_menu_entities.append(player_box)
			# self.player_menu_entities.append(inner_box)

	def set_build_end_turn_flag(self):	 self.app.game.set_build_end_turn_flag()
	def set_build_road_flag(self):		 self.app.game.set_build_road_flag()
	def set_build_town_flag(self): self.app.game.set_build_town_flag()
	def set_build_capitol_flag(self):		 self.app.game.set_build_capitol_flag()
	def set_build_achievement_flag(self):self.app.game.set_build_achievement_flag()
	def set_build_trade_requested_flag(self):self.app.game.set_build_trade_requested_flag()
	def update_achievement_card_menu(self):
		act = True
		if not self.app.game.phase in [PHASE_BUILD_AND_TRADE]: act = False
		if self.app.game.build_flag in [OPTION_NATURAL_PAVIMENTUM, OPTION_BOUNTIFUL_HARVEST, OPTION_CLAIMED_PRODUCT, OPTION_USE_PATROL]: act = False

		if self.current_player.action_cards and act:
			scale = self.actioncard_card.scale.y/2 - (self.actioncard_divider.y-self.actioncard_card.y)
			playable = self.app.game.check_current_player_option_availability_use_action_card()
			self.actioncard_menu = ScrolledMenu(
				[(a.name, lambda a=a:self.current_player_use_action_card(a), a.playable and playable) for a in self.current_player.action_cards],
				position=(self.actioncard_card.position.x,self.actioncard_divider.y),
				scale=(self.actioncard_card.scale.x,scale,self.actioncard_card.scale.z),
			)
		else:
			text = ursina.Text(
				parent=ursina.camera.ui,
				text="No action cards.",
				origin=(0,0.5),
				position=self.actioncard_divider.position - (0,self.minute_adjust,0),
				scale=0.75,
				add_to_scene_entities=False,
				color=ursina.rgb(*settings.ui_inactive_color)
			)

		if self.current_player.achievement_cards and act:
			scale = self.actioncard_card.scale.y/2 - (self.actioncard_divider.y-self.actioncard_card.y)
			self.actioncard_achievement_menu = ScrolledMenu(
				[(a.name, lambda a=a:print(a.name), False) for a in self.current_player.achievement_cards],
				position=(self.actioncard_card.position.x,self.actioncard_achievement_divider.y),
				scale=(self.actioncard_card.scale.x,scale,self.actioncard_card.scale.z),
			)
		else:
			text = ursina.Text(
				parent=ursina.camera.ui,
				text="No achievement cards.",
				origin=(0,0.5),
				position=self.actioncard_achievement_divider.position - (0,self.minute_adjust,0),
				scale=0.75,
				add_to_scene_entities=False,
				color=ursina.rgb(*settings.ui_inactive_color)
			)

	def update_scoreboard(self):
		via = PLAYER_FRIENDLY_NAMES[type(self.app.game.via_domini)] if self.app.game.via_domini else "Unclaimed"
		portum = PLAYER_FRIENDLY_NAMES[type(self.app.game.portum_domini)] if self.app.game.portum_domini else "Unclaimed"
		mili = PLAYER_FRIENDLY_NAMES[type(self.app.game.militum_dominus)] if self.app.game.militum_dominus else "Unclaimed"

		if self.app.game.via_domini:
			via_header = len(self.app.game.via_domini.owned_edges)+1
		else:
			via_header = self.app.game.min_roads_for_via_domini
		if self.app.game.portum_domini:
			portum_header = self.app.game.get_player_port_count(self.app.game.portum_domini) + 1
		else:
			portum_header = self.app.game.min_ports_for_portum_domini
		if self.app.game.militum_dominus:
			mil_header = self.app.game.militum_dominus.patrol_count + 1
		else:
			mil_header = self.app.game.min_patrols_for_militum_dominus
			

		scores = {
			f"Via Domini ({via_header})" : via,
			f"Portum Domini ({portum_header})" : portum,
			f"Militum Dominus ({self.app.game.min_patrols_for_militum_dominus})" : mili,
		}

		keys = list(scores.keys())
		text = ""
		for k in range(len(keys)):
			text+=f"{keys[k]} : {scores[keys[k]]}\n"
		txt = ursina.Text(
			parent=ursina.camera.ui,
			text=text,
			origin=(-0.5,0.5),
			position=self.scoreboard_divider.position-(0.5*self.scoreboard_divider.scale.x,self.minute_adjust,0),
			scale = 0.6,
			ignore = True,
		)
		self.scoreboard_entities.append(txt)
		if not self.scoreboard_lowerdivider:
			self.scoreboard_lowerdivider = ursina.Entity(
				parent=ursina.camera.ui,
				model=ursina.Quad(radius=0.5, aspect=settings.ui_divider_width/settings.ui_divider_height),
				position = (self.scoreboard_divider.position.x,txt.position.y-txt.height-self.minute_adjust,self.scoreboard_divider.position.z),
				color= ursina.color.white66,
				scale=(settings.ui_divider_width,settings.ui_divider_height),
				origin=(0,-0.5),
				add_to_scene_entities=False,
				eternal=True,
			)
		if not self.app.game.players: return
		height = (self.scoreboard_card.scale.y-(self.scoreboard_card.y-self.scoreboard_lowerdivider.y)-2*self.minute_adjust)/8

		players = sorted(self.app.game.players, key=lambda p: self.app.game.get_player_visible_victory_point_count(p) if not p is self.app.game.current_player else self.app.game.get_player_visible_victory_point_count(p), reverse=True)
		i = 0
		for p in players:
			if not i == 0:
				div = ursina.Entity(
					parent=ursina.camera.ui,
					model=ursina.Quad(radius=0.5, aspect=settings.ui_divider_width/settings.ui_divider_height),
					position=self.scoreboard_lowerdivider.position-(0,height*i,0.1),
					color= ursina.color.white66,
					scale=(settings.ui_divider_width*0.75,settings.ui_divider_height),
					origin=(0,-0.5),
				)
			r_image = ursina.Entity(
				model='quad',
				texture=f'assets/textures/Town_icon.png',
				parent=ursina.camera.ui,
				scale=0.035,
				color=ursina.rgb(*p.color),
				position = self.scoreboard_lowerdivider.position-(0.5*settings.ui_divider_width,height*i,0.1),
				origin=(-0.5,0.5)
			)
			v = self.app.game.get_player_visible_victory_point_count(p) if not p is self.current_player else self.app.game.get_player_victory_point_count(p)
			txt = ursina.Text(
				parent=ursina.camera.ui,
				text=f"GP : {str(v)} / {self.app.game.goal_points_to_win}" ,
				origin=(-0.5,0.5),
				position=self.scoreboard_lowerdivider.position-(0.5*settings.ui_divider_width - r_image.scale.x,height*i+0.5*r_image.scale.y,0.1),
				scale = 0.6,
				ignore = True,
			)
			i += 1

	def update_ui(self):
		if self.app.game.get_current_player_victory_point_count() > self.app.game.goal_points_to_win:
			self.show_acknowledgement_menu()
		self.update_inventory_display()
		self.update_achievement_card_menu()
		self.update_scoreboard()
		self.update_player_display()

	def update_inventory_display(self): #Update inventory counts
		for r in RESOURCES: self.resource_values[r].text = str(self.current_player.inventory[r])
		text_colors = [settings.ui_inactive_color, settings.ui_active_color]
		cancel_active = self.app.game.check_current_player_option_availability_cancel()
		cancel_active = cancel_active or self.exchange_dest_menu.enabled or self.exchange_source_menu.enabled
		self.cancel_button.enabled = cancel_active
		for k in self.action_buttons.keys(): #update action buttons
			button_active = not self.app.game.build_flag and self.button_check_functions[k]()
			self.action_buttons[k].enabled = button_active and not cancel_active
			self.dummy_buttons[k].enabled = not button_active and not cancel_active	
			self.button_texts[k].color = ursina.rgb(*text_colors[button_active])
			self.button_texts[k].enabled = not cancel_active
		self.end_turn_button.enabled=self.app.game.check_current_player_option_availability_end_turn()

		player = self.current_player
		via = len(self.current_player.owned_edges)
		portum = self.app.game.get_player_port_count(self.current_player)
		mil = self.current_player.patrol_count

		text = ""

		if self.current_player is self.app.game.via_domini:
			text += f"Via Domini: Held\n"
		else:
			if self.app.game.via_domini:
				text += f"Via Domini: {len(self.current_player.owned_edges)}/{len(self.app.game.via_domini.owned_edges)+1}\n"
			else:
				text += f"Via Domini: {len(self.current_player.owned_edges)}/{self.app.game.min_roads_for_via_domini}\n"

		if self.current_player is self.app.game.portum_domini:
			text += f"Portum Domini: Held\n"
		else:
			if self.app.game.portum_domini:
				goal_ports = self.app.game.get_player_port_count(self.app.game.portum_domini)
				player_ports = self.app.game.get_player_port_count(self.app.game.current_player)
				text += f"Portum Domini: {player_ports}/{goal_ports+1}\n"
			else:
				text += f"Portum Domini: {self.app.game.get_player_port_count(self.app.game.current_player)}/{self.app.game.min_ports_for_portum_domini}\n"

		if self.current_player is self.app.game.militum_dominus:
			text += f"Militum Dominus: Held"
		else:
			if self.app.game.militum_dominus:
				text += f"Militum Dominus: {self.current_player.patrol_count}/{self.app.game.militum_dominus.patrol_count + 1}\n"
			else:
				text += f"Militum Dominus: {self.current_player.patrol_count}/{self.app.game.min_patrols_for_militum_dominus}\n"
		
		txt = ursina.Text(
			parent=ursina.camera.ui,
			text=text,
			origin=(-0.5,0.5),
			position=self.divider.position-(0.5*self.divider.scale.x,self.minute_adjust,0),
			scale = 0.6,
			ignore = True,
		)

	def show_exchange_source_menu_for_current_player(self):
		return self.show_exchange_source_menu_for_player(self.current_player)
	def show_exchange_source_menu_for_player(self, player):
		rates = self.app.game.get_player_exchange_rates(player)
		for e in self.exchange_source_menu_entities: e.enabled = True
		for r in RESOURCES:
			rate = rates[r]
			count = player.inventory[r]
			ratestr = f"{rate}:1"
			self.exchange_source_menu_buttons[r].text = ratestr
			self.exchange_source_menu_buttons[r].on_click = lambda i=r: self.show_exchange_dest_menu_for_current_player(int(i))
			self.exchange_source_menu_dummy_buttons[r].text = ratestr
			status = rate <= count
			self.exchange_source_menu_values[r].text = str(count)
			self.exchange_source_menu_dummy_buttons[r].enabled = not status
			self.exchange_source_menu_buttons[r].enabled = status
		self.app.game.ui_needs_update = True
	def hide_exchange_source_menu(self):
		for e in self.exchange_source_menu_entities: e.enabled = False
	def show_exchange_dest_menu_for_current_player(self, resource):
		return self.show_exchange_dest_menu_for_player(self.current_player, resource)
	def show_exchange_dest_menu_for_player(self, player, resource):
		self.hide_exchange_source_menu()
		rate = self.app.game.get_player_exchange_rates(player)[resource]
		for e in self.exchange_dest_menu_entities: e.enabled = True

		target_resources = []
		for r in RESOURCES:
			if not r is resource:target_resources.append(r)
		for r, b in zip(target_resources, self.exchange_dest_menu_buttons):
			b.text = RESOURCE_MAP_INT_TO_NAME[r]
			b.on_click = lambda i=resource,j=r: self.make_player_exchange(player, i, j)
			b.player = player
		self.app.game.ui_needs_update = True
	def hide_exchange_dest_menu(self):
		for e in self.exchange_dest_menu_entities: e.enabled = False

	def check_current_player_option_availability_exchange(self):
		return self.app.game.phase == PHASE_BUILD_AND_TRADE

	def make_player_exchange(self,player,source_resource,target_resource):
		self.hide_exchange_dest_menu()
		return self.app.game.make_player_exchange(player,source_resource,target_resource)
	def make_resource_selection(self, resource):
		self.app.game.selection = resource
		self.hide_select_resource_menu()
	def show_select_resource_menu(self):
		for e in self.select_resource_menu_entities: e.enabled = True
	def hide_select_resource_menu(self):
		for e in self.select_resource_menu_entities: e.enabled = False
	def set_cancel_selection_flag(self):
		self.hide_exchange_dest_menu()
		self.hide_exchange_source_menu()
		self.app.game.set_cancel_selection_flag()

	def show_acknowledgement_menu(self):
		for e in self.acknowledgement_menu_entities: e.enabled = True
	def hide_acknowledgement_menu(self):
		for e in self.acknowledgement_menu_entities: e.enabled = False
	

if __name__=="__main__":
	app = App()
	def update(*args,**kwargs): app.update(*args,**kwargs)
	app.run()
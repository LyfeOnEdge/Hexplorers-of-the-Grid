import os, math, json, random
import ursina
from collections import deque

from modules.map_gen import MapMaker
from modules.settings import settings
from modules.entities import Node, Tile, WaterTile, Edge, Divider
from modules.UrsinaLighting import LitObject
from HexplorationEngine import Game, bluePlayer, greenPlayer, yellowPlayer,\
	purplePlayer, pinkPlayer, brownPlayer, redPlayer, grayPlayer, RESOURCES,\
	RESOURCE_MAP_INT_TO_NAME, PLAYER_FRIENDLY_NAMES, RECIPE_MAP_INT_TO_NAME,\
	PHASE_BUILD_AND_TRADE, RESOURCE_WASTELAND

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

		self.toggle_water_button = ursina.Button(parent=ursina.camera.ui,position = (-0.85,-.2),on_click = self.map.toggle_water,scale=0.035)
		self.toggle_grid_button = ursina.Button(parent=ursina.camera.ui, position = (-0.85,-0.3),on_click = self.map.toggle_grid,scale=0.035)
		self.toggle_skybox_button = ursina.Button(parent=ursina.camera.ui,position = (-0.85,-0.4),on_click = self.map.toggle_skybox,scale=0.035)
		# players = [bluePlayer(), greenPlayer(), redPlayer(), yellowPlayer(), purplePlayer(), pinkPlayer(), brownPlayer(), grayPlayer()]
		players = [bluePlayer(), greenPlayer()]
		self.game.start(players)

		self.robber = LitObject(
			position=(0,-9999,0),
			model='robber',
			color=ursina.rgb(50,50,50),
			scale=settings.board_scale,
			ambientStrength=1,
			smoothness = 2,
			cubemapIntensity=0.15,
			)

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
					model = "capital" if o.upgraded else "town"
					self.scene_entities.append(LitObject(
						position=o.position-(0,0.01,0),
						model=model,
						color=ursina.rgb(*o.owner.color),
						scale = settings.board_model_scale,
						ambientStrength=0.05,
						smoothness = 2,
						cubemapIntensity=0.15,
						))
				elif type(o) is Edge:
					x_0, _, z_0 = o.node_a.position
					x_1, _, z_1 = o.node_b.position
					self.scene_entities.append(LitObject(
						position=o.position-(0,0.01,0),
						model='road',
						color=ursina.rgb(*o.owner.color),
						scale = settings.board_model_scale,
						ambientStrength=0.05,
						smoothness = 2,
						rotation_y = math.degrees(math.atan2(x_0-x_1,z_0-z_1))+90,
						cubemapIntensity=0.15,
						))
				elif type(o) is Tile:
					if not o.resource_type is RESOURCE_WASTELAND:
						self.scene_entities.append(LitObject(
							position=o.position-(0,0.01,0),
							model='chip_beveled',
							color=ursina.rgb(200,200,200),
							scale = settings.board_model_scale*8,
							ambientStrength=0.05,
							smoothness = 2,
							cubemapIntensity=0.15,
							))
						self.scene_entities.append(ursina.Text(
							parent=ursina.scene,
							text=str(o.value),
							scale=22,
							size=40,
							position = o.position+(0,0.01+0.01*settings.board_scale,0),
							color=ursina.rgb(0,0,0),
							rotation_x = 90,
							origin=(0,0),
							cubemapIntensity=0.15,
							))	

					if o.has_robber:
						self.robber.position = o.position-(0,0.1,0)
			if type(o) is WaterTile:
				for e in o.neighbor_edges:
					if e.port:
						x_0, _, z_0 = o.position
						x_1, _, z_1 = e.position
						pos = ursina.Vec3(e.position[0],0.75*settings.board_scale*settings.island_height_above_water,e.position[2])-(0,0.01,0)
						angle = math.degrees(math.atan2(x_0-x_1,z_0-z_1))
						self.scene_entities.append(LitObject(
							position=pos,
							model='port_chip',
							# color=ursina.rgb(*settings.port_color),
							texture="textures/sand.png",
							scale = settings.board_scale,
							ambientStrength=0.05,
							smoothness = 2,
							rotation_y = angle,
							cubemapIntensity=0.15,
							))
						self.scene_entities.append(ursina.Text(
							parent=ursina.scene,
							text=str(RESOURCE_MAP_INT_TO_NAME[e.port]),
							scale=13,
							size=40,
							position = ((x_0+x_1+x_1)/3,pos[1]+0.01+0.01*settings.board_scale,(z_0+z_1+z_1)/3), #Place text shifted towards land
							color=ursina.rgb(0,0,0),
							rotation_x = 90,
							origin=(0,0),
							rotation_y = angle,
						))
						self.scene_entities.append(ursina.Text(
							parent=ursina.scene,
							text=f"{self.game.port_exchange_rates[e.port]}:1",
							scale=14,
							size=40,
							position = ((x_0+x_0+x_1)/3,pos[1]+0.01+0.01*settings.board_scale,(z_0+z_0+z_1)/3), #Place text shifted towards tile
							color=ursina.rgb(0,0,0),
							rotation_x = 90,
							origin=(0,0),
							rotation_y = angle,
						))



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
		self.recipe_divider = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.5, aspect=settings.ui_divider_width/settings.ui_divider_height),
			position = self.recipe_card_label.position,
			color= ursina.color.white66,
			scale=(settings.ui_divider_width,settings.ui_divider_height),
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
		self.resource_values = {}
		for i in range(len(RESOURCES)):
			r = RESOURCES[i]
			r_text = ursina.Text(
				parent=ursina.camera.ui,
				text=RESOURCE_MAP_INT_TO_NAME[r],
				origin=(0,-0.5),
				position=self.item_box.position,
				color=ursina.rgb(*settings.ui_resource_color),
				scale = 0.75,
				rotation_z = -7,
				z = -0.2	
			)
			r_text.x += (i+0.5)*(ursina.camera.aspect_ratio/2*0.35)/len(RESOURCES)
			r_text.y += 1.0/ursina.camera.aspect_ratio/2*0.35
			r_x = ursina.Text(
				parent=ursina.camera.ui,
				text="X",
				origin=(0,-0.5),
				position=r_text.position-(0,0.4/ursina.camera.aspect_ratio/2*0.35,0),
				color=ursina.rgb(*settings.ui_resource_color),
				scale = 0.75,
			)
			r_v = ursina.Text(
				parent=ursina.camera.ui,
				text="0",
				origin=(0,-0.5),
				position=r_x.position-(0,0.4/ursina.camera.aspect_ratio/2*0.35,0),
				color=ursina.rgb(*settings.ui_resource_color),
				scale = 1,
				rotation_z = -7,
			)
			self.resource_texts[r], self.resource_values[r]=r_text, r_v

		self.message_ticker = ursina.Text(
			parent=self.message_box,
			text=self.displayed_message,
			origin=(0,0),
			position=(0,-0.5, -0.1),
			scale_y=c.aspect_ratio/3/(yscale/message_box_scale),
			size=0.025,			
		)
		self.player_name = ursina.Text(
			parent=ursina.camera.ui,
			text="#PLAYER_NAME",
			origin=(0,1),
			position=self.bottom_menu_box.position+(0,yscale,-0.2),
			scale=0.75,
		)
		self.divider = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.5, aspect=settings.ui_divider_width/settings.ui_divider_height),
			position = self.bottom_menu_box.position+(0,9*self.yscale/13,-0.2),
			color= ursina.color.white66,
			scale=(settings.ui_divider_width,settings.ui_divider_height),
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
			settings.exchange_resources_string: self.show_exchange_source_menu_for_current_player,
			settings.build_road_string : self.set_build_road_flag,
			settings.build_town_string :self.set_build_town_flag,
			settings.build_capital_string : self.set_build_capital_flag,
			settings.build_dev_card_string: self.set_build_achievement_flag,
			settings.request_trade_string: self.set_build_trade_requested_flag,
		}
		self.button_check_functions = {	
			settings.build_road_string : self.app.game.check_current_player_option_availability_road,
			settings.build_town_string :self.app.game.check_current_player_option_availability_town,
			settings.build_capital_string : self.app.game.check_current_player_option_availability_capital,
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
			)
			t = ursina.Text(
				parent=ursina.camera.ui,
				position=b.position-(0,0,0.1),
				scale =0.5,
				size=0.020,
				color=ursina.rgb(*settings.ui_inactive_color),
				text=k,
				origin=(0,0),
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
				enabled=False
			)
		self.end_turn_button = ursina.Button(
				parent=ursina.camera.ui,
				text=settings.end_turn_string,
				position = self.bottom_menu_box.position,
				on_click = self.set_build_end_turn_flag,
				origin=(0,-0.5),
				scale = (ursina.camera.aspect_ratio/2*0.25,2*self.yscale/(len(buttonkeys)+1)),
				radius=0.2,
				color=ursina.color.black66,
				enabled=False
			)


		self.exchange_source_menu = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.1, aspect = 2),
			color=ursina.color.black90,
			position=(0,0),
			scale=(1/2,1/4),
			origin=(0,0)
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
				z = -0.2	
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
			)
			r_v = ursina.Text(
				parent=ursina.camera.ui,
				text="0",
				origin=(0,-0.5),
				position=r_x.position-(0,0.4/1/8,0),
				color=ursina.rgb(*settings.ui_resource_color),
				scale = 1,
				rotation_z = -7,
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
			)
			r_db.text_color=settings.ui_inactive_color

			self.exchange_source_menu_texts[r], self.exchange_source_menu_values[r], self.exchange_source_menu_buttons[r], self.exchange_source_menu_dummy_buttons[r] =r_text, r_v, r_b, r_db
			self.exchange_source_menu_entities.extend([r_text, r_v, r_x, r_db, r_b])

		exchange_source_label = ursina.Text(
			parent=ursina.camera.ui,
			text="Select Exchange Source",
			origin=(0,1),
			position=self.exchange_source_menu.position+(0,1/8,0),
			scale=0.75,
			z = -0.2
		)
		exchange_source_divider = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.5, aspect=settings.ui_divider_width/settings.ui_divider_height),
			position = self.exchange_source_menu.position+(0,5/64,0),
			color= ursina.color.white66,
			scale=(settings.ui_divider_width,settings.ui_divider_height),
			origin=(0,0),
			z = -0.2
		)
		self.exchange_source_menu_entities.extend([exchange_source_label, exchange_source_divider])

		for e in self.exchange_source_menu_entities: e.enabled = False

		self.exchange_dest_menu = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.1, aspect = 4),
			color=ursina.color.black90,
			position=(0,0),
			scale=(1/2,1/8),
			origin=(0,0)
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
			)
			b.x += (i+0.5)*(1/2)/(len(RESOURCES)-1)
			self.exchange_dest_menu_entities.extend([b])
			self.exchange_dest_menu_buttons.append(b)

		exchange_dest_label = ursina.Text(
			parent=ursina.camera.ui,
			text="Select Resource to receive",
			origin=(0,1),
			position=self.exchange_dest_menu.position+(0,1/16,0),
			scale=0.75,
			z = -0.2
		)
		exchange_dest_divider = ursina.Entity(
			parent=ursina.camera.ui,
			model=ursina.Quad(radius=0.5, aspect=settings.ui_divider_width/settings.ui_divider_height),
			position = self.exchange_dest_menu.position+(0,1/64,0),
			color= ursina.color.white66,
			scale=(settings.ui_divider_width,settings.ui_divider_height),
			origin=(0,0),
			z = -0.2
		)
		self.exchange_dest_menu_entities.extend([exchange_dest_label, exchange_dest_divider])
		for e in self.exchange_dest_menu_entities: e.enabled = False

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
				model='town',
				color=ursina.rgb(*players[i].color),
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
	def set_build_town_flag(self): self.app.game.set_build_town_flag()
	def set_build_capital_flag(self):		 self.app.game.set_build_capital_flag()
	def set_build_achievement_flag(self):self.app.game.set_build_achievement_flag()
	def set_build_trade_requested_flag(self):self.app.game.set_build_trade_requested_flag()
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

	def set_cancel_selection_flag(self):
		self.hide_exchange_dest_menu()
		self.hide_exchange_source_menu()
		self.app.game.set_cancel_selection_flag()
		

if __name__=="__main__":
	app = App()
	update = app.update #Set this so app.update gets called every loop, usually you would define a function
	app.run()
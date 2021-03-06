import os, sys, json
from types import SimpleNamespace

def remake_settings():
	setting_dict = {
		"devMode" : True,
		"keep_topmost" : False,
		"borderless" : False,
		"fullscreen" : False,
		"heightmap_noise_dampening":1,
		"water_scale":6,
		"water_subdivisions_per_axis_radius":3,

		"island_subdivisions_per_axis_radius":3,

		"shore_drop":0.2,
		"shore_spread":-0.5,
		"default_radius":3,
		"default_terrain_amp":1,
		"island_height_above_water":0.05,

		"island_skirt_color":(200,200,160),
		"snow_color": (190,190,195),
		"grass_color": (0,160,30),
		"rock_color": (120,120,120),
		"dirt_color": (130,130,50),
		"mud_color": (100,100,50),
		"sand_color": (200,200,160),
		"grass_cutoff": (0.45),
		"dirt_cutoff": (0.3),
		"mud_cutoff": (0.15),
		"water_color":(0,0,180),

		"port_color": (90,90,20),
		
		"board_snow_color": (245,245,245),
		"board_rock_color": (200,200,200),
		"board_grass_color": (150,160,150),
		"board_dirt_color": (170,170,170),
		"board_sand_color": (145,145,140),
		"board_water_color": (130,130,130),
		"board_snow_cutoff": 0.80,
		"board_rock_cutoff": 0.65,
		"board_grass_cutoff": 0.425,
		"board_dirt_cutoff": 0.175,
		"board_sand_cutoff": 0.1,
		"board_texture_scale":40,
		"board_texture_resolution":5,

		"tile_grid_thickness":5,

		"island_resolution":100, #Number of verts per axis in island mesh
		"island_scale":7, #Bigger means more, smaller islands
		"activated_color":(255,165,0),
		"board_scale":2,

		"player_color_red": (200,0,0),
		"player_color_blue": (0,0,200),
		"player_color_green": (0,150,30),
		"player_color_yellow": (200,203,8),
		"player_color_purple": (80,30,120),
		"player_color_pink": (255,90,220),
		"player_color_brown": (107, 67, 33),
		"player_color_gray": (127,127,127),
		"board_model_scale":0.25,
		"board_selector_scale":0.5,

		"ui_active_color":(255,255,255),
		"ui_inactive_color":(100,100,100),
		"ui_recipe_text_color":(255,255,255),
		"ui_resource_color":(255,255,255),
		"ui_divider_width" : 0.25,
		"ui_divider_height" : 0.0035,
		"ui_menu_y_scale" : 0.15,

		"end_turn_string" : "End Turn",
		"build_road_string" : "Build Road",
		"build_town_string" : "Build Town",
		"build_capitol_string" : "Build Capital",
		"build_dev_card_string" : "Build Achievement/Action Card",
		"request_trade_string" : "Request Trade",
		"exchange_resources_string" : "Exchange Resources"

	}
	with open("settings.json", "w+") as s:
		json.dump(setting_dict, s, indent=4)

def load_settings():
	with open("settings.json") as data:
		return json.load(data, object_hook=lambda d: SimpleNamespace(**d))

if not os.path.isfile("settings.json"):remake_settings()
settings=load_settings()
if settings.devMode:remake_settings()
settings=load_settings()
import os, sys, json
from types import SimpleNamespace

def remake_settings():
	setting_dict = {
		"devMode" : True,
		"appName" : "Plan-O-Grab",
		"keep_topmost" : False,
		"borderless" : False,
		"fullscreen" : False,
		"heightmap_noise_dampening":1,
		"water_scale":8,
		"island_height_multiplier":1,
		"shore_drop":1,
		"default_radius":15,
		"default_scale":1,
		"default_terrain_amp":1,
		"default_terrain_scale":1,
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
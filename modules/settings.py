import os, sys, json
from types import SimpleNamespace
from PIL import Image, ImageTk

BACKGROUND_COLOR = "#232a2f"
BUTTON_COLOR = "#363941"
DESKTOP = "desktop"
MOBILE = "mobile"
DEFAULT_FONT_COLOR = "white"


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
	}

	with open("settings.json", "w+") as s:
		json.dump(setting_dict, s, indent=4)

if not os.path.isfile("settings.json"):
	remake_settings()

def load_settings():
	with open("settings.json") as data:
		return json.load(data, object_hook=lambda d: SimpleNamespace(**d))

settings = load_settings()

if settings.devMode:
	remake_settings()
	settings = load_settings()
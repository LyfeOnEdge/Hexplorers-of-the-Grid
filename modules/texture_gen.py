import random
from opensimplex import OpenSimplex
import numpy as np
from PIL import Image, ImageOps
from .settings import settings
import math

random.seed(random.random())

uid=0
def get_uid():
	global uid
	uid+=1
	return uid-1

class BoardTexturer:
	def __init__(self, width, height, seed=0, num_generators=2):
		self.seed = seed
		self.width, self.height = width, height
		self.position = 0,0,0
		self.generators = [OpenSimplex(seed=seed+i**i).noise2 for i in range(num_generators)]
		self.image = None

	def generate_board(self):
		x,y,z=self.position
		arr = np.full([settings.board_texture_resolution*self.width, settings.board_texture_resolution*self.height, 3], settings.board_water_color, dtype=np.uint8)
		print(f"Board Image Size - {settings.board_texture_resolution*self.width} x {settings.board_texture_resolution*self.height}")
		for _x in range(len(arr)):
			rel_x = (x - _x/(settings.board_texture_resolution*self.width))
			for _z in range(len(arr[_x])):
				rel_z = (z - _z/(settings.board_texture_resolution*self.height))
				vals = [g((rel_x)*settings.board_texture_scale, (rel_z)*settings.board_texture_scale) for g in self.generators]
				avg = math.sin(abs(sum(vals)/len(vals))*1.5)
				if avg > settings.board_snow_cutoff: arr[_x][_z] = settings.board_snow_color
				elif avg > settings.board_rock_cutoff: arr[_x][_z] = settings.board_rock_color
				elif avg > settings.board_grass_cutoff: arr[_x][_z] = settings.board_grass_color
				elif avg > settings.board_dirt_cutoff: arr[_x][_z] = settings.board_dirt_color
				elif avg > settings.board_sand_cutoff: arr[_x][_z] = settings.board_sand_color
		self.image = ImageOps.mirror(Image.fromarray(np.swapaxes(np.uint8(arr),0,1)).convert('RGB')).rotate(270)
		self.image_name = f"textures/temp/board{self.seed}.png"
		self.image.save(self.image_name)
		return self.image

	def get_image_piece(self,x,z):
		x,z = 0.25*x+0.5*self.width, 0.25*z+0.5*self.height
		left = max(settings.board_texture_resolution*x,0)
		right = min(settings.board_texture_resolution*(x+1),self.image.size[0]-1)
		upper = min(settings.board_texture_resolution*z, self.image.size[1]-1)
		lower = max(settings.board_texture_resolution*(z+1), 0)
		texname = f"textures/temp/board_piece{get_uid()}.png"
		with open(texname, "wb+") as f: ImageOps.mirror(self.image.crop((left,upper,right,lower))).save(f)
		return texname


#Leopard print
# vals = [g((rel_x)*settings.board_texture_scale, (rel_z)*settings.board_texture_scale) for g in self.generators]
# avg = math.cos(abs(sum(vals)/len(vals))*2)

#Deep Valley
#avg = math.cos(abs(sum(vals)/len(vals))*5)

#Patches
#avg = math.cos(sum(vals)/len(vals))

#Carbon Fiber
#avg = (math.cos(sum(vals)/len(vals))+math.sin(_x+_z))/2

#Torn
#avg = (math.cos(sum(vals)/len(vals))+math.sin(_x/10+_z/10))/2
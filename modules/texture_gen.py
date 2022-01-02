import random
from opensimplex import OpenSimplex
import numpy as np
from PIL import Image

random.seed(random.random())

def generate_lin_noise(width, height,scale=20, seed=0, color_depth=3, num_generators=1, cutoff=0.5, default_color=(30,160,30), color=(100,100,50)):
	generators = [OpenSimplex(seed=seed+i**i).noise2 for i in range(num_generators)]
	r,g,b = default_color
	arr = np.full([width, height, color_depth], (r,g,b), dtype=np.uint8)
	for x in range(len(arr)):
		for z in range(len(arr[x])):
			vals = [g(x/scale,z/scale) for g in generators]
			if sum(vals) / len(vals) > cutoff:
				arr[x][z] = color
	return arr

class TextureMaker:
	def __init__(self, seed = None):
		self.texturecache = {}

	def get_random_seed(self):
		return random.randint(0,100)

	def get_texture(self, tid):
		return self.texturecache.get(tid)

	def make_rock_texture(self,width,height):
		seed = self.get_random_seed()
		texture = generate_lin_noise(width,height,scale=2, seed=seed, color_depth=3, num_generators=1, cutoff=0, default_color=(200,200,160), color=(180,180,110))
		self.texturecache["rock"] = Image.fromarray(np.uint8(texture)).convert('RGB')
		return self.texturecache["rock"]

	def make_sand_texture(self,width,height):
		seed = self.get_random_seed()
		texture = generate_lin_noise(width,height,scale=2, seed=seed, color_depth=3, num_generators=1, cutoff=0.65, default_color=(140,140,30), color=(100,100,50))
		self.texturecache["sand"] = Image.fromarray(np.uint8(texture)).convert('RGB')
		return self.texturecache["sand"]

	def make_grass_texture(self,width,height):
		seed = self.get_random_seed()
		texture = generate_lin_noise(width,height,scale=10, seed=seed, color_depth=3, num_generators=1, cutoff=0.5, default_color=(30,160,30), color=(100,100,50))
		self.texturecache["grass"] = Image.fromarray(np.uint8(texture)).convert('RGB')
		return self.texturecache["grass"]

	def make_dirt_texture(self,width,height):
		seed = self.get_random_seed()
		texture = generate_lin_noise(width,height,scale=30, seed=seed, color_depth=3, num_generators=1, cutoff=0, default_color=(80,40,12), color=(60,30,5))
		self.texturecache["rock"] = Image.fromarray(np.uint8(texture)).convert('RGB')
		return self.texturecache["rock"]



# tm = TextureMaker()
# tm.make_sand_texture(150,150).show()
# tm.make_grass_texture(150,150).show()
# tm.make_rock_texture(150,150).show()
# tm.make_dirt_texture(150,150).show()
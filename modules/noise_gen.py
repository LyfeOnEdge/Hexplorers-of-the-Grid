from opensimplex import OpenSimplex
import random

from .settings import settings

class generator_object:
	def __init__(self, seed = None):
		self.regen(seed)
	def regen(self, seed): #Randomizes the generator seeds again
		self.seed = seed or random.uniform(0,1)
		random.seed(random.random())
		self.generator = OpenSimplex(seed=3*int(random.uniform(0,50))).noise2
		self.generator_2 = OpenSimplex(seed=17*int(random.uniform(0,50))).noise2
		self.generator_3 = OpenSimplex(seed=27*int(random.uniform(0,50))).noise2
	def get_heightmap(self,x,z):
		return abs((self.generator(x/5, z/5) + self.generator_2(x/9, z/9))/(2*settings.heightmap_noise_dampening))
	def get_scaled_heightmap(self,x,z,scale):
		return abs((self.generator(x/scale, z/scale) + self.generator_2(x/scale, z/scale))/2)
noiseGenerator = generator_object(seed = 3)
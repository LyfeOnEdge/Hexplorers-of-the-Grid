import ursina
from .settings import settings

class ScrollingButtonMenu():
	def __init__(self, **kwargs):
		super().__init__()
		self.max = ursina.inf
		self.min = 0
		self.scroll_speed = .01
		self.axis = 'y'
		self.target_value = None

		for key, value in kwargs.items():
			setattr(self, key, value)

	def input(self, key):
		if not ursina.mouse.hovered_entity:
			return

		if not self.target_value:
			self.target_value = getattr(self.entity, self.axis)

		if self.entity.hovered or ursina.mouse.hovered_entity.has_ancestor(self.entity):
			if key =='scroll up': v=-self.scroll_speed
			elif key =='scroll down': v=self.scroll_speed
			else: return
			self.entity.y += v
			if hasattr(self.entity, 'scissor_view'):
				if self.entity.y < self.entity.start_y:
					self.entity.y = self.entity.start_y
					a,b=self.entity.scissor_view
					a.y = 0
					b.y = -self.entity.scissor_height
					self.entity.scissor_view = (a,b)
					self.entity.set_scissor(*self.entity.scissor_view)
				elif self.entity.y > self.entity.end_y:
					self.entity.y -= v #Undo change and don't do anything else
					return
				else:
					a,b=self.entity.scissor_view
					a.y -= 2*v/self.entity.scissor_height
					b.y = a.y - self.entity.scissor_height
					self.entity.scissor_view = (a,b)
					self.entity.set_scissor(*self.entity.scissor_view)
			self.entity.update_buttons_shown()

class _menuButtonInnerView(ursina.Entity):
	def __init__(self, *args, **kwargs):
		super().__init__(self, *args, **kwargs)
		self.scissor_view = None
		self.scissor_height = None
		self.start_y = self.position.y
		self.top_y = self.position.y + self.scale.y
		self.bottom_y =self.position.y
		self.buttons = []
		self.end_y = None
	def update_buttons_shown(self):
		top = self.position.y + self.scale.y
		bottom = self.position.y
		for b in self.buttons:
			b_pos = b.position.y*self.scale.y+top
			b.enabled = b_pos <= self.top_y+0.05 and b_pos > self.bottom_y+0.05

class ScrolledMenu(ursina.Entity):
	def __init__(self, options, *args, **kwargs):
		super().__init__(args, **kwargs)
		self.inner_frame = _menuButtonInnerView(
			parent=ursina.camera.ui,
			model='quad',
			color=ursina.color.clear,
			position=self.position,
			scale=self.scale,
			origin=self.origin
		)
		self.inner_frame.scissor_height = 2*self.inner_frame.scale.y
		self.inner_frame.scissor_view = ursina.Vec3(-1,0,0), ursina.Vec3(1,-self.inner_frame.scissor_height,0)
		self.inner_frame.set_scissor(*self.inner_frame.scissor_view)
		if options:
			self.update_options(options)
			self.inner_frame.update_buttons_shown()

	def update_options(self, options):
		if self.inner_frame.buttons:
			[ursina.destroy(b) for b in self.inner_frame.buttons]
			for b in self.inner_frame.buttons: del b
			self.inner_frame.buttons=[]
		self.options = list(options)
		for i in range(len(self.options)):
			b = ursina.Button(
				parent=self.inner_frame,
				text=str(self.options[i][0]),
				position=(0.5,-i*0.1-0.01),
				color=ursina.color.black66 ,
				on_click=self.options[i][1] if self.options[i][2] else None,
				highlight_color= ursina.color.white33 if self.options[i][2] else ursina.color.black66,
				scale = (0.9,0.1005),
				z = -0.2,
				origin = (0,0.5),
				radius=0.5,
				size=0.2,
			)
			b.text_entity.scale*=0.75
			b.text_entity.color= ursina.color.white if self.options[i][2] else ursina.rgb(*settings.ui_inactive_color)
			self.inner_frame.buttons.append(b)
		if i*0.1 > self.inner_frame.scale.y:
			self.inner_frame.add_script(ScrollingButtonMenu())
		self.inner_frame.end_y = self.inner_frame.bottom_y + i*0.1*self.scale.y-0.01

	# def destroy(self):
	# 	[ursina.destroy(b) for b in self.inner_frame.buttons]
	# 	for b in self.inner_frame.buttons: del b
	# 	ursina.destroy(self.inner_frame)
	# 	del self.inner_frame
	# 	ursina.destroy(self)
	# 	del self
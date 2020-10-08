class Method:

	def __init__(self, meth, name):
		self.meth = meth
		self.name = name

	def __eq__(self, other):
		return self.name == other.name

	def execute(self):
		self.meth()


class Timer:
	methods = []

	def push(self, meth):
		methods.append(math)

	def polling(self):
		for i in range(len(self.methods)):
			methods[i].execute()

	def remove(method_name):
		for method in self.methods:
			if method.name == method_name:
				self.methods.remove(method)
				return
		raise IndexError("No method in list")

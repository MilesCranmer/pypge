from __future__ import print_function
from __future__ import division

import sympy
sympy.init_printing(use_unicode=True)

from itertools import combinations, combinations_with_replacement as combos

from pypge import filters
from pypge import model

BASIC_BASE = [sympy.exp, sympy.cos, sympy.sin]
BASIC_MISC = [sympy.Abs, sympy.sqrt, sympy.log, sympy.exp]
BASIC_TRIG = [sympy.cos, sympy.sin, sympy.tan]
HYPER_TRIG = [sympy.cosh, sympy.sinh, sympy.tanh]

C = sympy.symbols('C')

def map_names_to_funcs(names):
	funcs = []
	for name in names:

		if name == "sqrt":
			func.append(sympy.sqrt)
		elif name == "abs":
			funcs.append(sympy.Abs)
		elif name == "sin":
			funcs.append(sympy.sin)
		elif name == "cos":
			funcs.append(sympy.cos)
		elif name == "tan":
			funcs.append(sympy.tan)
		elif name == "exp":
			funcs.append(sympy.exp)
		elif name == "log":
			funcs.append(sympy.log)
		elif name == "sinh":
			funcs.append(sympy.sinh)
		elif name == "cosh":
			funcs.append(sympy.cosh)
		elif name == "tanh":
			funcs.append(sympy.tanh)

		else:
			raise Exception("Unknown function name: " + name)

	return funcs


class Grower:

	def __init__(self,xs, funcs, **kwargs):
	
		# if only one variable, turn into list
		if type(xs) is sympy.Symbol:
			xs = [xs]
	
		self.xs = xs
		self.funcs = funcs

		# policy configs
		self.func_level = "linear"     # [linear,nonlin]
		self.init_level = "low"     # [low,med,high]
		self.subs_level = "low"     # [low,med,high]

		# do grow_level this way so we can override the individual ones if we want
		self.grow_level = kwargs.get("grow_level", "low")   # [low,med,high]
		self.add_extend_level = self.grow_level               # [low,med,high]
		self.mul_extend_level = self.grow_level               # [low,med,high]

				# override with kwargs
		# --------------------
		for key, value in kwargs.items():
			# print (key, value)
			setattr(self, key, value)
		# --------------------

		print("xs: ", self.xs)
		print("funcs: ", self.funcs)
		print("f_lvl:", self.func_level)
		print("i_lvl:", self.init_level)
		print("g_lvl:", self.grow_level)

		self.xs_pow1 = [x**(n*(p+1)) for p in range(1) for n in [-1,1] for x in xs]
		self.xs_pow2 = [x**(n*(p+1)) for p in range(2) for n in [-1,1] for x in xs]
		self.xs_pow3 = [x**(n*(p+1)) for p in range(3) for n in [-1,1] for x in xs]
		self.xs_pow4 = [x**(n*(p+1)) for p in range(4) for n in [-1,1] for x in xs]

		# print("xs_pow1:", self.xs_pow1)
		# print("xs_pow2:", self.xs_pow2)
		# print("xs_pow3:", self.xs_pow3)
		# print("xs_pow4:", self.xs_pow4)


		self.wout_c_xs1_muls = [ x for x in self.xs_pow1 ]
		self.wout_c_xs2_muls = [ tpl[0] * tpl[1] for tpl in combos(self.xs_pow1, 2)] + self.wout_c_xs1_muls
		self.wout_c_xs3_muls = [ tpl[0] * tpl[1] * tpl[2] for tpl in combos(self.xs_pow1, 3)]
		self.wout_c_xs4_muls = [ tpl[0] * tpl[1] * tpl[2] * tpl[3] for tpl in combos(self.xs_pow1, 4)] + self.wout_c_xs3_muls
		self.with_c_xs1_muls = [ C * m for m in self.wout_c_xs1_muls ]
		self.with_c_xs2_muls = [ C * m for m in self.wout_c_xs2_muls ]
		self.with_c_xs3_muls = [ C * m for m in self.wout_c_xs3_muls ]
		self.with_c_xs4_muls = [ C * m for m in self.wout_c_xs4_muls ]

		# print("wout_c_xs1_muls", self.wout_c_xs1_muls)
		# print("wout_c_xs2_muls", self.wout_c_xs2_muls)
		# print("wout_c_xs3_muls", self.wout_c_xs3_muls)
		# print("wout_c_xs4_muls", self.wout_c_xs4_muls)
		# print("with_c_xs1_muls", self.with_c_xs1_muls)
		# print("with_c_xs2_muls", self.with_c_xs2_muls)
		# print("with_c_xs3_muls", self.with_c_xs3_muls)
		# print("with_c_xs4_muls", self.with_c_xs4_muls)
		
		self.wout_c_linear_funcs = []
		self.wout_c_nonlin_funcs = []
		self.with_c_linear_funcs = []
		self.with_c_nonlin_funcs = []
		if funcs is not None:
			self.wout_c_linear_funcs = [ f(x) for f in funcs for x in self.xs_pow1]
			self.wout_c_nonlin_funcs = [ f(C*x+C) for f in funcs for x in self.xs_pow1]
			self.with_c_linear_funcs = [ C*f(x) for f in funcs for x in self.xs_pow1]
			self.with_c_nonlin_funcs = [ C*f(C*x+C) for f in funcs for x in self.xs_pow1]

		# print("wout_c_linear_funcs", self.wout_c_linear_funcs)
		# print("wout_c_nonlin_funcs", self.wout_c_nonlin_funcs)
		# print("with_c_linear_funcs", self.with_c_linear_funcs)
		# print("with_c_nonlin_funcs", self.with_c_nonlin_funcs)

		self.with_c_func_exprs = []
		self.wout_c_func_exprs = []
		if self.func_level == "linear":
			self.with_c_func_exprs = self.with_c_linear_funcs + [ f**(-1) for f in self.with_c_linear_funcs ]
			self.wout_c_func_exprs = self.wout_c_linear_funcs + [ f**(-1) for f in self.wout_c_linear_funcs ]
		elif self.func_level in ["nonlin", "nonlinear"]:
			self.with_c_func_exprs = self.with_c_nonlin_funcs + [ f**(-1) for f in self.with_c_nonlin_funcs ]
			self.wout_c_func_exprs = self.wout_c_nonlin_funcs + [ f**(-1) for f in self.wout_c_nonlin_funcs ]
		else:
			print("UNKNOWN FUNC_LEVEL!!")
			return

		self.init_var_subs()
		self.init_add_extends()
		self.init_mul_extends()

	def first_exprs(self):
		
		mul_exprs = []
		if self.init_level == "low":
			if len(self.xs) > 3:
				mul_exprs = self.with_c_xs1_muls
			else:
				mul_exprs = self.with_c_xs2_muls
		elif self.init_level == "med":
			if len(self.xs) > 3:
				mul_exprs = self.with_c_xs1_muls
			elif len(self.xs) > 1:
				mul_exprs = self.with_c_xs2_muls
			else:
				mul_exprs = self.with_c_xs3_muls
		elif self.init_level == "high":
			if len(self.xs) > 3:
				mul_exprs = self.with_c_xs2_muls
			elif len(self.xs) > 1:
				mul_exprs = self.with_c_xs3_muls
			else:
				mul_exprs = self.with_c_xs4_muls
		else:
			print("UNKNOWN INIT_LEVEL!!")
			return

		# print("mul_exprs: ", mul_exprs)

		mid_exprs = mul_exprs + self.with_c_func_exprs
		# print("mid_exprs: ", mid_exprs)
		add_exprs = [ tpl[0] + tpl[1] for tpl in combinations(mid_exprs, 2)]
		if self.init_level == "high":
			add_exprs += [ tpl[0] + tpl[1] + tpl[2] for tpl in combinations(mid_exprs, 3)]

		# print("add_exprs: ", mid_exprs)
		exprs_set = mid_exprs + add_exprs

		# always add the plus C
		plus_C_exprs = [ sympy.Add( expr, C ) for expr in exprs_set]
		ret_exprs = exprs_set + plus_C_exprs

		## UNIQUIFY THE RESULTS
		pass_set = set()
		for p in ret_exprs:
			s = p.evalf()
			pass_set.add(s)
		ret_exprs = list(pass_set)

		models = [model.Model(e, xs=self.xs) for e in ret_exprs]
		for m in models:
			m.gen_relation = "first_gen"
			m.parent_id = -1

		return models




	def init_var_subs(self):

		add_terms = [ C*x+C for x in self.xs ]

		if self.subs_level == "low":
			self.var_sub_lim_terms = self.wout_c_xs2_muls
			self.var_sub_terms = self.var_sub_lim_terms + self.wout_c_func_exprs

		elif self.subs_level == "med":
			self.var_sub_lim_terms = self.wout_c_xs2_muls
			self.var_sub_terms = self.var_sub_lim_terms + self.wout_c_func_exprs + add_terms

		elif self.subs_level == "high":
			self.var_sub_lim_terms = self.wout_c_xs3_muls + add_terms
			self.var_sub_terms = self.var_sub_lim_terms + self.wout_c_func_exprs + add_terms

		else:
			print("UNKNOWN SUBS_LEVEL!!")

		## UNIQUIFY THE RESULTS
		pass_set = set()
		for p in self.var_sub_terms:
			pass_set.add(p)
		self.var_sub_terms = list(pass_set)


	def init_add_extends(self):

		if self.add_extend_level == "low":
			self.add_extend_terms = self.with_c_xs1_muls + self.with_c_func_exprs
		elif self.add_extend_level == "med":
			self.add_extend_terms = self.with_c_xs2_muls + self.with_c_func_exprs
		elif self.add_extend_level == "high":
			cross = [x*f for f in self.with_c_func_exprs for x in self.with_c_xs1_muls]
			self.add_extend_terms = self.with_c_xs2_muls + self.with_c_func_exprs + cross
		else:
			print("UNKNOWN EXTEND_LEVEL!!")

		## UNIQUIFY THE RESULTS
		pass_set = set()
		for p in self.add_extend_terms:
			pass_set.add(p)
		self.add_extend_terms = list(pass_set)

	def init_mul_extends(self):

		if self.mul_extend_level == "low":
			self.mul_extend_terms = self.wout_c_xs1_muls + self.wout_c_func_exprs
		elif self.mul_extend_level == "med":
			self.mul_extend_terms = self.wout_c_xs2_muls + self.wout_c_func_exprs
		elif self.mul_extend_level == "high":
			cross = [x*f for f in self.wout_c_func_exprs for x in self.wout_c_xs1_muls]
			self.mul_extend_terms = self.wout_c_xs2_muls + self.wout_c_func_exprs + cross
		else:
			print("UNKNOWN EXTEND_LEVEL!!")

		## UNIQUIFY THE RESULTS
		pass_set = set()
		for p in self.mul_extend_terms:
			pass_set.add(p)
		self.mul_extend_terms = list(pass_set)




	def grow(self, M):

		var_expands = self._var_sub(M.orig)
		add_expands = self._add_extend(M.orig)
		mul_expands = self._mul_extend(M.orig)

		var_models = [model.Model(e, p_id=M.id, reln="var_xpnd") for e in var_expands if e != C]
		add_models = [model.Model(e, p_id=M.id, reln="add_xpnd") for e in add_expands if e != C]
		mul_models = [model.Model(e, p_id=M.id, reln="mul_xpnd") for e in mul_expands if e != C]

		models = var_models + add_models + mul_models
		return models


	def _var_sub(self, expr, limit_sub=False):
		new_exprs = []
		# only worry about non-atoms, cause we have to replace args
		if not expr.is_Atom:
			# make a list of args to this non-atom
			# each member of the list is the original expr's args with one substitution made
			args_sets = []
			for i,e in enumerate(expr.args):
				# if the current arg is also a non-atom, recurse
				if not e.is_Atom:
					## check to see if we are in some function besides ADD or MUL
					## if so, limit what we substitute
					lim_sub = limit_sub or not (e.is_Add or e.is_Mul)
					# for each expr returned, we need to clone the current args
					# and make the substitution, sorta like flattening?
					ee = self._var_sub(e, lim_sub)
					if len(ee) > 0:
						# We made a substitution(s) on a variable down this branch!!
						for vs in ee:
							# clone current args
							cloned_args = list(expr.args)
							# replace this term in each
							cloned_args[i] = vs
							# append to the args_sets
							args_sets.append(cloned_args)

				elif e in self.xs:
					## Lets make a variable substitution !!
					# loop over self.var_sub_terms
					sub_terms = self.var_sub_terms
					if limit_sub:
						sub_terms = self.var_sub_lim_terms
					for vs in sub_terms:
						# clone current args
						cloned_args = list(expr.args)
						# replace this term in each
						cloned_args[i] = vs
						# append to the args_sets
						args_sets.append(cloned_args)
				else:
					# we don't have to do anything, probably?
					pass

			# finally, create all of the clones at the current level of recursion
			for args in args_sets:
				args = tuple(args)
				tmp = expr.func(*args)
				new_exprs.append(tmp)

		## UNIQUIFY THE RESULTS
		pass_set = set()
		for p in new_exprs:
			s = p.evalf()
			pass_set.add(s)
		new_exprs = list(pass_set)

		return new_exprs

		# if e.is_Symbol and e in self.xs:
		

	def _add_extend(self, expr):
		new_exprs = []
		# only worry about non-atoms, cause we extend args
		if not expr.is_Atom:
			args_sets = []
			# however we have 2 cases here (as opposed to _var_sub)
			# 1. extend this expression if it's an Add
			if expr.is_Add:
				for term in self.add_extend_terms:
					# has_match skips extending an add with a term that is already present 
					has_match = False
					for e in expr.args:
						if e == term:
							has_match = True
							break
					if has_match:
						continue
					
					cloned_args = list(expr.args)
					cloned_args.append(term)
					args_sets.append(cloned_args)

			# 2. do the recursion
			for i,e in enumerate(expr.args):
				if not e.is_Atom:
					ee = self._add_extend(e)
					if len(ee) > 0:
						# We made a substitution(s) on a variable down this branch!!
						for vs in ee:
							# clone current args
							cloned_args = list(expr.args)
							# replace this term in each
							cloned_args[i] = vs
							# append to the args_sets
							args_sets.append(cloned_args)


			# finally, create all of the clones at the current level of recursion
			for args in args_sets:
				args = tuple(args)
				tmp = expr.func(*args)
				new_exprs.append(tmp)

		## UNIQUIFY THE RESULTS
		pass_set = set()
		for p in new_exprs:
			s = p.evalf()
			pass_set.add(s)
		new_exprs = list(pass_set)

		return new_exprs

	def _mul_extend(self, expr):
		new_exprs = []
		# only worry about non-atoms, cause we extend args
		if not expr.is_Atom:
			args_sets = []
			# however we have 2 cases here (as opposed to _var_sub)
			# 1. extend this expression if it's an Add
			if expr.is_Mul:
				for term in self.mul_extend_terms:
					cloned_args = list(expr.args)
					cloned_args.append(term)
					args_sets.append(cloned_args)

			# 2. do the recursion
			for i,e in enumerate(expr.args):
				if not e.is_Atom:
					ee = self._mul_extend(e)
					if len(ee) > 0:
						# We made a substitution(s) on a variable down this branch!!
						for vs in ee:
							# clone current args
							cloned_args = list(expr.args)
							# replace this term in each
							cloned_args[i] = vs
							# append to the args_sets
							args_sets.append(cloned_args)


			# finally, create all of the clones at the current level of recursion
			for args in args_sets:
				args = tuple(args)
				tmp = expr.func(*args)
				new_exprs.append(tmp)

		## UNIQUIFY THE RESULTS
		pass_set = set()
		for p in new_exprs:
			s = p.evalf()
			pass_set.add(s)
		new_exprs = list(pass_set)

		return new_exprs






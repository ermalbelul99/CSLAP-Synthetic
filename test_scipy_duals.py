import numpy as np
from scipy.optimize import linprog

# min -x1 - x2
# s.t. x1 + x2 <= 1 => dual is y1 >= 0
# x1, x2 >= 0
# Obj should be -1. Active constraint x1+x2<=1 has dual 1 or -1?
res = linprog([-1, -1], A_ub=[[1, 1]], b_ub=[1], bounds=(0, None))
print("Obj:", res.fun)
print("Ineq marginals:", res.ineqlin.marginals)

# Equality
# min x1
# s.t. x1 + x2 == 1
# x1, x2 >= 0
res2 = linprog([1, 0], A_eq=[[1, 1]], b_eq=[1], bounds=(0, None))
print("Eq marginals:", res2.eqlin.marginals)

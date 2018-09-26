import json

with open('shortest_paths_loop_ex_rank') as f:
	a = json.load(f)

k = 0
for x in a:
	if x[3] is None:
		k+= 1
		continue
	print '%d %d %d %d %d' % (len(x[0]), len(x[1]), len(x[2]), len(x[3]), len(x[4]))
print k

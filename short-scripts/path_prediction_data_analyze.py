import json

with open('path_prediction_loop_ex') as f:
	a = json.load(f)

for x in a:
	print '%d %d %d %d' % (x[0], x[1], x[2], x[3])

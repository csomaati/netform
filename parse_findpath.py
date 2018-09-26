import json
import glob
import numpy as np
import sys


name_pattern = sys.argv[1]
vf_route_list_fname = sys.argv[2]

with open(vf_route_list_fname) as f:
    vf_route_list = json.load(f)

pattern = '%s*' % (name_pattern,)
print pattern
fnames = glob.glob(pattern)
print len(fnames)
stretch_failed = 0
vf_failed = 0
lp_failed = 0

only_vf_failed = 0

trace_count = 0
vf_compressions = []

vf_predictions = []
str_predictions = []

for fname in fnames:
    # print fname
    with open(fname, 'r') as f:
        results = json.load(f)
    str_tmp = 0
    vf_tmp = 0
    lp_tmp = 0
    for res in results:
        possible_routes = res[0]
        vf_routes = res[1]
        lp_routes = res[2]
        lp_all_routes = res[3]
        id_s = res[4]
        id_t = res[5]
        max_len = res[6]
        sh_len = res[7]
        trace = res[8]
        str_pred_failed = res[9]
        vf_pred_failed = res[10]
        lp_pred_failed = res[11]

        stretch_prediction_failed = str_pred_failed > str_tmp
        vf_prediction_failed = vf_pred_failed > vf_tmp
        lp_prediction_failed = lp_pred_failed > lp_tmp

        str_tmp = str_pred_failed
        vf_tmp = vf_pred_failed
        lp_tmp = lp_pred_failed

        if stretch_prediction_failed: stretch_failed += 1
        if vf_prediction_failed: vf_failed += 1
        if lp_prediction_failed: lp_failed += 1

        if not stretch_prediction_failed and vf_prediction_failed:
            only_vf_failed += 1

        trace_count += 1

        if not vf_prediction_failed:
            vf_compression = float(vf_routes) / float(possible_routes)
            vf_compressions.append(vf_compression)
            vf_predictions.append(vf_routes)
            str_predictions.append(possible_routes)


print 'Trace count: %d' % trace_count
print 'STRETCH failed: %d' % stretch_failed
good_stretch = trace_count - stretch_failed
print 'Remained trace: %d' % good_stretch
# print 'VF failed: %d' % vf_failed
print 'Only VF failed: %d (%f%%)' % (only_vf_failed, (only_vf_failed / float(good_stretch)))

print 'VF OK: %d' % len(vf_compressions)
print 'mean of #VF/#POSSIBLE_ROTUES: %f' % np.mean(vf_compressions)
print 'mean vf trace number: %f' % np.mean(vf_predictions)
print 'mean stretch trace number: %f' % np.mean(str_predictions)

import numpy as np
import matplotlib.pyplot as plt
import pypet

# folder_path = '../output/pypet/'
folder_path = '/Users/raphaelholca/Mountpoint/hebbianRL/output/dopa_L1_run3/'

traj_name = 'dMid'
traj = pypet.load_trajectory(traj_name, filename=folder_path + 'perf.hdf5', force=True)
traj.v_auto_load = True

p_W_act = []
skipped_count = 0
ok_runs = []
for run in traj.f_iter_runs():
	try:
		# p_W_act.append(traj.results[run].perc_W_act)
		p_W_act.append(traj.results[run].perf)
		ok_runs.append(int(run[4:]))
	except pypet.pypetexceptions.DataNotInStorageError:
		skipped_count+=1
print str(skipped_count) + ' runs skipped'

param_traj = traj.f_get_explored_parameters()
param = {}
for k in param_traj:
	if k[11:] != 'runName':
		param[k[11:]] = np.array(param_traj[k].f_get_range())[ok_runs]

arg_best = np.argmax(p_W_act)


best_param = {}

print 'best parameters:'
print '================'
for k in param.keys():
	best_param[k] = param[k][arg_best]
	print k + ' : ' + str(param[k][arg_best]) + '\t\t' + str(np.round(np.unique(param[k]),2))

keys = param.keys()
for ik in range(len(keys)):
	for k in keys[ik+1:]:
		others = keys[:]
		others.remove(keys[ik])
		others.remove(k)
		
		mask = np.ones_like(param[k], dtype=bool)
		if len(param)>2:
			for o in others:
				mask = np.logical_and(mask, param[o]==best_param[o])
		pX = param[keys[ik]][mask]
		pY = param[k][mask]
		rC = np.array(p_W_act)[mask]

		fig = plt.figure()
		fig.patch.set_facecolor('white')
		plt.scatter(pX, pY, c=rC, cmap='CMRmap', vmin=0.0, vmax=1.0, s=5000, marker='s')
		# plt.scatter(param[keys[ik]][arg_best], param[k][arg_best], c='r', s=50, marker='x')
		for i in range(len(pX)):
			plt.text(pX[i], pY[i], str(np.round(rC[i]*100,1)), horizontalalignment='center', verticalalignment='center')
		plt.xticks(pX)
		plt.yticks(pY)
		plt.xlabel(keys[ik], fontsize=25)
		plt.ylabel(k, fontsize=25)
		plt.tick_params(axis='both', which='major', labelsize=18)
		plt.tight_layout()
		plt.savefig(folder_path + keys[ik] + '_' + k)

plt.show()
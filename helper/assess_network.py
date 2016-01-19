""" Support functions to assess network; functions to plot receptive fields, histogram of the distribution of the classes of the weights (RFs) of the representation, etc.  """

import numpy as np
import external as ex
import grating as gr 
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.cm as cm
import pickle

ex = reload(ex)
gr = reload(gr)


def hist(name, W, classes, images, labels, n_bins=10, save_data=True, verbose=True):
	"""
	computes the class of the weight (RF) of each neuron. Can be used to compute the selectivity index of a neuron. Selectivity is measured as # of preferred stimulus example that activate the neuron / # all stimulus example that activate the neuron

	Args:
		name (str): name of the network, used to save to file
		W (numpy array): weight matrix from input to hidden layer; shape = (input x hidden)
		classes (numpy array): all classes of the MNIST dataset used in the current run
		images (numpy array): images of the MNIST dataset used for training
		labels (numpy array): labels corresponding to the images of the MNIST dataset
		n_bins (int, optional): number of bins in the histogram
		save_data (bool, optional): whether save data
		verbose (bool, optional): whether to display text ouput

	return:
		RFproba (numpy array): probability that a each RF belongs to a certain class. The probability is computed as the # of stimuli from a digit class that activate the neuron / total # of stimuli that activate the neuron (shape= n_runs x n_hid_neurons x 10). This can be used to compute the selectivity index of a neuron by taking np.max(RFproba,2)
		RFclass (numpy array): count of neurons responsive of each digit class (shape= n_runs x 10)
		RFselec (numpy array): mean selectivity index for all RFs of a digit class. Computed as the mean of RFproba for each class
	"""

	if verbose: print "computing RF classes..."
	n_runs = np.size(W,0)
	n_neurons = np.size(W,2)

	RFproba = np.zeros((n_runs,n_neurons,n_bins))
	RFclass = np.zeros((n_runs,n_bins))
	RFselec = np.zeros((n_runs,n_bins))
	for r in range(n_runs):
		if verbose: print 'run: ' + str(r+1)
		mostActiv = np.argmax(ex.propagate_layerwise(images, W[r]),1)
		for n in range(n_neurons):
			RFproba[int(r),n,:] = np.histogram(labels[mostActiv==n], bins=n_bins, range=(-0.5,9.5))[0]
			RFproba[int(r),n,:]/= np.sum(RFproba[int(r),n,:])+1e-20 #+1e-20 to avoid divide zero error
		RFclass[r,:], _ = np.histogram(np.argmax(RFproba[r],1), bins=n_bins, range=(-0.5,9.5))
		for c in range(n_bins):
			RFselec[r,c] = np.mean(np.max(RFproba[r],1)[np.argmax(RFproba[r],1)==c])

	RFclass_mean = np.mean(RFclass, 0)
	RFclass_ste = np.std(RFclass, 0)/np.sqrt(np.size(RFclass,0))


	if save_data:
		bin_names = classes
		fig = plot_hist(RFclass_mean[classes], bin_names, h_err=RFclass_ste[classes])
		plt.savefig('./output/'+name+'/' +name+ '_RFhist.pdf')
		plt.close(fig)

	RF_info = {'RFproba':RFproba, 'RFclass_all':RFclass, 'RFclass_mean':RFclass_mean, 'RFclass_ste':RFclass_ste, 'RFselec':RFselec}

	return RFproba, RF_info

def hist_gabor(n_bins, name, hid_W_runs, t, target_ori, save_data, verbose):
	""" Computes the distribution of orientation preference of neurons in the network. """
	
	curves = gr.tuning_curves(hid_W_runs, t, target_ori, name, method='no_softmax', plot=True)
	pref_ori = gr.preferred_orientations(hid_W_runs, t, target_ori, name)
	slopes = gr.slopes(hid_W_runs, curves, pref_ori, t, target_ori, name)
	
	RFproba = np.zeros((np.size(hid_W_runs,0), np.size(hid_W_runs,2), 2), dtype=int)
	
	n_runs = np.size(pref_ori,0)
	for r in range(n_runs):
		RFproba[r,:,:][pref_ori[r,:]<=target_ori] = [1,0]
		RFproba[r,:,:][pref_ori[r,:]>target_ori] = [0,1]

	h_all = np.zeros((n_runs, n_bins))
	for r in range(n_runs):
		h_all[r, :] = np.histogram(pref_ori[r,:], n_bins, range=(0.,180.))[0]
	h_mean = np.mean(h_all,0)
	h_ste = np.std(h_all,0)/np.sqrt(n_runs)

	if save_data:
		bin_size = 180./n_bins
		bin_names = np.zeros(n_bins, dtype='|S3')
		for i in range(n_bins):
			bin_names[i] = str(int(bin_size*i + bin_size/2.))

		fig = plot_hist(h_mean, bin_names, h_err=h_ste)
		plt.savefig('./output/'+name+'/' +name+ '_RFhist.pdf')
		plt.close(fig)
	
	RF_info = {'RFproba':RFproba, 'curves':curves, 'pref_ori':pref_ori, 'slopes':slopes}
	
	return RFproba, RF_info

def selectivity(W, RFproba, images, labels, classes):
	"""
	computes the selectivity of a neuron, using the already computed RFproba. This RFproba must have been computed using hist()

	Args:
		W (numpy array) : weights from input to hidden neurons
		RFproba (numpy array) : 
	"""
	acti = ex.propagate_layerwise(images, W, SM=False)
	n_neurons = np.size(acti,1)
	n_classes = len(classes)
	best_neuron = np.argmax(acti, 1)
	RFclass = np.argmax(RFproba,1)
	select_neuron = np.zeros(n_neurons)
	select_class = np.zeros(n_classes)
	for n in range(n_neurons):
		all_acti, _ = np.histogram(labels[best_neuron==n], bins=10, range=(0,9))
		select_neuron[n] = float(all_acti[RFclass[n]])/np.sum(all_acti)
	for i, c in enumerate(classes):
		select_class[i] = np.mean(select_neuron[RFclass==c])

	return select_class, select_neuron

""" initialize color maps """
n_colors = 9
my_blues = [plt.get_cmap('YlGnBu')(1.*i/n_colors) for i in range(n_colors)]
my_reds = [plt.get_cmap('YlOrRd')(1.*i/n_colors) for i in range(n_colors)]
cm_pastel = [plt.get_cmap('Paired')(1.*i/n_colors) for i in range(n_colors)]

def print_save_CM(perf_dict, name, classes, verbose, save_data):
	""" print and save performance measures """

	CM_avg = perf_dict['CM_avg']
	perf_all = perf_dict['perf_all']
	perf_avg = perf_dict['perf_avg']
	perf_ste = perf_dict['perf_ste']

	if verbose or save_data:
		perf_print = ''
		perf_print += '\naverage confusion matrix:' + '\n'
		c_str = ''
		for c in classes: c_str += str(c).rjust(6)
		perf_print += c_str + '\n'
		perf_print += '-'*(len(c_str)+3) + '\n'
		perf_print += str(np.round(CM_avg,2)) + '\n'
		perf_print += '\naverage correct classification:' + '\n'
		perf_print += str(np.round(100*perf_avg,2)) + ' +/- ' + str(np.round(100*perf_ste,2)) + ' %' + '\n'
		if len(perf_all)>1:
			perf_print += '\nof which best performance is:' + '\n'
			perf_print += str(np.round(100*(np.max(perf_all)),2)) + '%' + ' (run ' + str(np.argmax(perf_all)) + ')' + '\n'
			perf_print += 'and worse performance is:' + '\n'
			perf_print += str(np.round(100*(np.min(perf_all)),2)) + '%' + ' (run ' + str(np.argmin(perf_all)) + ')' + '\n'

		print perf_print

	if save_data:
		perf_file = open('./output/' + name + '/' +name+ '_perf.txt', 'w')
		perf_file.write(perf_print)
		perf_file.close()

		fig = plot_CM(CM_avg, classes)
		plt.savefig('./output/' + name + '/' +name+ '_avgCM.pdf')
		plt.close(fig)


def plot_all_RF(name, W, RFproba, target=None, W_act=None, sort=None, not_same=None, verbose=True):
	""" Plot the RFs of neurons """
	if verbose: print "\nploting RFs..."

	if sort=='tSNE':
		if np.mod(np.sqrt(np.size(W['000'],1)),1)!=0:
			print '!! number of neurons not square; using class sorting for display !!'
			sort='class'

	n_runs = np.size(W,0)
	for r in range(n_runs):
		W_sort = np.copy(W[r])
		if verbose: print 'run: ' + str(r+1)
		if sort=='class': #sort weights according to their class
			RFclass = np.argmax(RFproba[r],1)
			sort_idx = np.array([x for (y,x) in sorted(zip(RFclass, np.arange(len(RFclass))), key=lambda pair: pair[0])])
			W_sort = W[r][:,sort_idx] 
			RFproba[r] = np.array([x for (y,x) in sorted(zip(RFclass, RFproba[r]), key=lambda pair: pair[0])])
		elif sort=='tSNE':
			W_sort = tSNE_sort(W_sort)
		target_pass=None
		if target:
			T_idx = np.argwhere(np.argmax(RFproba[r],1)==target[r])
			target_pass = np.zeros((np.size(W_sort,0),1,1))
			target_pass[T_idx,:,:]=1.0
		W_act_pass=None
		if W_act is not None:
			W_act_pass = W_act[r]
		if not_same:
			notsame_pass = not_same[r]
		else: 
			notsame_pass = np.array([])

		fig = plot_single_RF(W_sort, target=target_pass, W_act=W_act_pass, not_same=notsame_pass)
		plt.savefig('output/' + name + '/RFs/' + name+ '_' + str(r).zfill(3)+'.png')
		plt.close(fig)

def clockwise(r):
	return list(r[0]) + clockwise(list(reversed(zip(*r[1:])))) if r else []

def tSNE_sort(W):
	"""
	sorts weight using t-Distributed Stochastic Neighbor Embedding (t-SNE)

	Args:
		W (numpy array) : weights from input to hidden neurons

	returns:
		(numpy array) : sorted weights
	"""
	import tsne
	import numpy.ma as ma

	Y = tsne.tsne(W.T, 2 , 50).T
	side = int(np.sqrt(np.size(W,1)))
	n_hid_neurons = np.size(W,1)

	n0_min, n1_min = np.min(Y,1)
	n0_max, n1_max = np.max(Y,1)
	n0_grid = np.hstack(np.linspace(n0_min, n0_max, side)[:,np.newaxis]*np.ones((side,side)))
	n1_grid = np.hstack(np.linspace(n1_max, n1_min, side)[np.newaxis,:]*np.ones((side,side)))

	sorted_idx = np.zeros(n_hid_neurons, dtype=int)
	mask = np.zeros(n_hid_neurons, dtype=bool)

	iterate_clockwise = map(int, clockwise(list(np.reshape(np.linspace(0,n_hid_neurons-1,n_hid_neurons),(side,side)))))

	for i in iterate_clockwise:
		c_point = np.array([n0_grid[i], n1_grid[i]])[:,np.newaxis]
		dist = ma.array(np.sum((Y-c_point)**2,0), mask=mask)
		min_idx = np.argmin(dist)
		sorted_idx[i] = min_idx
		mask[min_idx] = True

	return W[:,sorted_idx]

def plot_single_RF(W, target=None, W_act=None, cmap='Greys', not_same=np.array([])):
	""" plots of the weights, with superimposed colouring for target digit and out layer weights """
	
	#plot parameters
	n_hid_neurons = np.size(W,1)
	v = int(np.sqrt(n_hid_neurons))
	h = int(np.ceil(float(n_hid_neurons)/v))
	Wmin = np.min(W)
	Wmax = np.max(W)

	#create a transparent colormap
	cmap_trans = plt.get_cmap('binary') 
	cmap_trans._init()
	alphas = np.linspace(0., 1., cmap_trans.N+3)
	cmap_trans._lut[:,-1] = alphas

	im_size = int(np.sqrt(np.size(W,0)))

	#plot figure
	fig, ax = plt.subplots(figsize=(h,v))
	for i in range(np.size(W,1)):
		plt.subplot(v,h,i+1)
		if type(target)!=type(None) and target[i]!=0:
			plt.imshow(target[i], cmap=cmap, vmin=0., vmax=3, extent=(0,im_size,0,im_size))
		plt.imshow(np.reshape(W[:,i], (im_size,im_size)), interpolation='nearest', cmap=cmap_trans, extent=(0,im_size,0,im_size), vmin=Wmin)
		if type(W_act)!=type(None):
			if i in not_same:
				plt.imshow([[0]], cmap='RdYlBu', vmin=0., vmax=3, extent=(im_size,im_size+2,0,im_size))
			plt.imshow(W_act[i,:][:,np.newaxis], interpolation='nearest', cmap='binary', extent=(im_size,im_size+2,0,im_size))
			plt.imshow([[0.]], interpolation='nearest', cmap='binary', alpha=0, extent=(0,im_size+2,0,im_size))
		plt.xticks([])
		plt.yticks([])

	#plot parameters
	fig.patch.set_facecolor('white')
	plt.subplots_adjust(left=0., right=1., bottom=0., top=1., wspace=0., hspace=0.)

	return fig

def plot_CM(confusMatrix, classes):
	""" plots the confusion matrix, with color on the diagonal, and with the alphas indicating the magnitude of the error """

	#create a transparent colormap
	n_classes = len(classes)
	cmap_trans = mpl.colors.LinearSegmentedColormap.from_list('my_cmap',['white','white'],256) 
	cmap_trans._init()
	alphas = np.linspace(1.0, 0, cmap_trans.N+3)
	cmap_trans._lut[:,-1] = alphas

	#creates the background color matrix
	colorMatrix = np.ones_like(confusMatrix)
	np.fill_diagonal(colorMatrix, -1.0)

	#plot the matrix and number values
	sH = 1.0+0.5*n_classes
	sV = 0.9+0.5*n_classes
	fig, ax = plt.subplots(figsize=(sH,sV))
	ax.imshow(colorMatrix, interpolation='nearest', cmap='RdYlGn_r', vmin=-1.2, vmax=1.2)
	ax.imshow(confusMatrix, interpolation='nearest', cmap=cmap_trans, vmin=-0.0, vmax=1)
	for i in range(n_classes):
		for j in range(n_classes):
			perc = int(np.round(confusMatrix[i,j],2)*100)
			ax.annotate(perc, xy=(0, 0),  xycoords='data', xytext=(j, i), textcoords='data', size=15, ha='center', va='center')

	#plot parameters
	fig.patch.set_facecolor('white')
	ax.spines['right'].set_visible(False)
	ax.spines['left'].set_visible(False)
	ax.spines['bottom'].set_visible(False)
	ax.spines['top'].set_visible(False)
	ax.set_xticks(np.arange(n_classes))
	ax.set_yticks(np.arange(n_classes))
	ax.set_xticklabels(classes, fontsize=18)
	ax.set_yticklabels(classes, fontsize=18)
	ax.xaxis.set_ticks_position('none')
	ax.yaxis.set_ticks_position('none')
	ax.set_xlabel('prediction', fontsize=17)
	ax.set_ylabel('label', fontsize=18)
	plt.tight_layout()
	# fig.subplots_adjust(top=0, bottom=0, right=1, left=0)

	return fig

def plot_hist(h, bins, h_err=None):
	""" plots the histogram of receptive field class distribution """

	fig, ax = plt.subplots(figsize=(1+0.5*len(h),3))
	Xs = np.arange(len(h))
	y_max = np.ceil(np.sum(h))
	ax.bar(Xs, h, yerr=h_err, color=my_blues[6], ecolor=my_blues[7])

	fig.patch.set_facecolor('white')
	ax.spines['right'].set_visible(False)
	ax.spines['top'].set_visible(False)
	ax.set_xticks(Xs+0.5)
	ax.set_xticklabels(bins)
	s = np.where(y_max>4, 2,1)
	ax.set_yticks(np.arange(y_max+1, step=s))
	ax.tick_params(axis='both', which='major', direction='out', labelsize=17)
	ax.xaxis.set_ticks_position('bottom')
	ax.yaxis.set_ticks_position('left')
	ax.set_xlabel('class', fontsize=18)
	ax.set_ylabel('neuron count', fontsize=18)
	plt.tight_layout()

	return fig

def plot_perf_progress(name, perf_train, perf_test, dopa_start, epi_start=0):
	"""
	plots the progression of the error rate over training episodes

	Args:
		name (str): name of the network, used for saving purposes
		perf_train (numpy array): training performance at each episode of each run
		perf_test (numpy array): testing performance at each episode of each run
		epi_start (int, optional): episode at which to start the plot (used epi_start=n_epi_crit to plot only after statistical pre-training). Default: 0 
	"""

	fig, ax = plt.subplots()
	plt.gca().set_color_cycle(cm.Paired(i) for i in np.linspace(0,0.9,10))

	n_runs = np.size(perf_train, 0)
	for r in range(n_runs):
		if epi_start <= dopa_start:
			plt.axvline(x=dopa_start, ymin=0, ymax=100, lw=2.5, ls='--', c='k', alpha=0.25)
		X = np.arange( len(perf_train[r, epi_start:]) )+1
		ax.plot(X, perf_train[r, epi_start:]*100, lw=3, ls='-')
		if perf_test is not None:
			ax.plot(X, perf_test[r, epi_start:]*100, lw=3, ls=':')

	fig.patch.set_facecolor('white')
	ax.spines['right'].set_visible(False)
	ax.spines['top'].set_visible(False)
	ax.tick_params(axis='both', which='major', direction='out', labelsize=17)
	ax.set_xticks(np.arange(1, len(perf_train[0,epi_start:])+1))
	ax.xaxis.set_ticks_position('bottom')
	ax.yaxis.set_ticks_position('left')
	ax.set_xlabel('training episodes', fontsize=18)
	ax.set_ylabel('% correct', fontsize=18)
	plt.tight_layout()

	plt.savefig('output/' + name + '/' + name+ '_progress.pdf')
	plt.close(fig)	















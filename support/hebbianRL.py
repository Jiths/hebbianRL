""" 
This function trains a hebbian neural network to learn a representation from the MNIST dataset. It makes use of a reward/relevance signal that increases the learning rate when the network makes a correct state-action pair selection.

Output is saved under RL/data/[runName]
"""

# from progressbar import ProgressBar
import numpy as np
import matplotlib.pyplot as pyplot
import support.external as ex
import support.plots as pl
import support.classifier as cl
import support.assessRF as rf
import support.svmutils as su
import support.grating as gr
import sys

ex = reload(ex)
pl = reload(pl)
cl = reload(cl)
rf = reload(rf)
su = reload(su)
gr = reload(gr)


def RLnetwork(	images, labels, orientations, 
				images_test, labels_test, orientations_test, 
				images_task, labels_task, orientations_task, 
				kwargs,	classes, rActions, nRun, nEpiCrit, nEpiDopa, t_hid, t_act, A, runName, dataset, nHidNeurons, lr, aHigh, aPairing, dHigh, dMid, dNeut, dLow, nBatch, protocol, target_ori, excentricity, noise_crit, noise_train, noise_test, im_size, classifier, pypet_xplr, SVM, bestAction, createOutput, showPlots, show_W_act, sort, target, seed):

	""" variable initialization """
	if createOutput: runName = ex.checkdir(runName, OW_bool=True) #create saving directory
	else: print " !!! ----- not saving data ----- !!! "
	W_in_save = {}
	W_act_save = {}
	nClasses = len(classes)
	_, idx = np.unique(rActions, return_index=True)
	lActions = rActions[np.sort(idx)]
	nEpiTot = nEpiCrit + nEpiDopa
	nImages = np.size(images,0)
	nInpNeurons = np.size(images,1)
	nActNeurons = nClasses
	# ach_bal = 0.25 ##optimize


	""" training of the network """
	print '\ntraining network...'
	for r in range(nRun):
		np.random.seed(seed+r)
		print '\nrun: ' + str(r+1)

		#randommly assigns a class with ACh release (used to run multiple runs of ACh)
		# if True: target, rActions, rActions, lActions = ex.rand_ACh(nClasses) ##

		#initialize network variables
		ach = np.zeros(nBatch)
		dopa = np.zeros(nBatch)
		W_in = np.random.random_sample(size=(nInpNeurons, nHidNeurons)) + 1.0
		W_act = (np.random.random_sample(size=(nHidNeurons, nActNeurons))/1000+1.0)/nHidNeurons
		W_in_init = np.copy(W_in)
		W_act_init = np.copy(W_act)
		perf_track = np.zeros((nActNeurons, 2))

		choice_count = np.zeros((nClasses, nClasses))
		dopa_save = []

		# pbar_epi = ProgressBar()
		# for e in pbar_epi(range(nEpiTot)):
		for e in range(nEpiTot):
			#shuffle input
			rndImages, rndLabels = ex.shuffle([images, labels])

			if e==nEpiCrit: print '--end crit--'
			###
			# if e==5:
			# 	RFproba, _, _ = rf.hist(runName, {'000':W_in}, classes, nInpNeurons, images, labels, SVM=SVM, proba=False, output=False, show=False)
			# 	W_act = reorder(W_in, W_act, RFproba, classes, rActions)

			#train network with mini-batches
			for b in range(int(nImages/nBatch)):
				
				#select batch training images (may leave a few training examples out (< nBatch))
				if protocol=='digit' or (protocol=='gabor' and e < nEpiCrit): 
					bImages = rndImages[b*nBatch:(b+1)*nBatch,:]
					bLabels = rndLabels[b*nBatch:(b+1)*nBatch]
				elif protocol=='gabor' and e >= nEpiCrit:
					bImages = images_task[b*nBatch:(b+1)*nBatch,:]
					bLabels = labels_task[b*nBatch:(b+1)*nBatch]

				#initialize batch variables
				ach = np.ones(nBatch)
				dopa = np.ones(nBatch)
				dW_in = 0.
				dW_act = 0.
				disinhib_Hid = np.ones(nBatch)##np.zeros(nBatch)
				disinhib_Act = np.zeros(nBatch)
				
				#compute activation of hidden and classification neurons
				bHidNeurons = ex.propL1(bImages, W_in, SM=False)
				bActNeurons = ex.propL1(ex.softmax(bHidNeurons, t=t_hid), W_act, SM=False)

				#predicted best action
				bPredictActions = rActions[np.argmax(bActNeurons,1)]

				#add noise to activation of hidden neurons and compute lateral inhibition
				if not bestAction and (e >= nEpiCrit):
					bHidNeurons += np.random.uniform(0, 50, np.shape(bHidNeurons)) ##param explore, optimize
					bHidNeurons = ex.softmax(bHidNeurons, t=t_hid)
					bActNeurons = ex.propL1(bHidNeurons, W_act, SM=False)
				else:
					bHidNeurons = ex.softmax(bHidNeurons, t=t_hid)
				
				#adds noise in W_act neurons
				if e < nEpiCrit:
					bActNeurons += np.random.uniform(0, 10, np.shape(bActNeurons)) ##param explore, optimize
				bActNeurons = ex.softmax(bActNeurons, t=t_act)
					
				#take action - either deterministically (predicted best) or stochastically (additive noise)			
				bActions = rActions[np.argmax(bActNeurons,1)]	
				bActions_idx = ex.val2idx(bActions, lActions)

				#compute reward and ach signal
				bReward = ex.compute_reward(ex.label2idx(classes, bLabels), np.argmax(bActNeurons,1))
				# pred_bLabels_idx = ex.val2idx(bPredictActions, lActions) ##same as bActions_idx for bestAction = True ??
				# ach, ach_labels = ex.compute_ach(perf_track, pred_bLabels_idx, aHigh=aHigh, rActions=None, aPairing=1.0) # make rActions=None or aPairing=1.0 to remove pairing

				#compute dopa signal and disinhibition based on training period
				if e < nEpiCrit:
					""" critical period """
					dopa = ex.compute_dopa(bPredictActions, bActions, bReward, dHigh=0.0, dMid=0.75, dNeut=0.0, dLow=-0.5) #original param give close to optimal results
					# dopa = ex.compute_dopa(bPredictActions, bActions, bReward, dHigh=dHigh, dMid=dMid, dNeut=dNeut, dLow=dLow)
					# dopa = ex.compute_dopa(bPredictActions, bActions, bReward, dHigh=0.0, dMid=0.2, dNeut=-0.3, dLow=-0.5)

					disinhib_Hid = ach
					disinhib_Act = dopa

				elif e >= nEpiCrit: 
					""" Dopa - perceptual learning """
					dopa = ex.compute_dopa(bPredictActions, bActions, bReward, dHigh=dHigh, dMid=dMid, dNeut=dNeut, dLow=dLow)

					disinhib_Hid = ach*dopa
					# disinhib_Act = ex.compute_dopa(bPredictActions, bActions, bReward, dHigh=0.0, dMid=0.75, dNeut=0.0, dLow=-0.5) #continuous learning in L2
					disinhib_Act = np.zeros(nBatch) #no learning in L2 during perc_dopa.
					
				#compute weight updates
				dW_in 	= ex.learningStep(bImages, 		bHidNeurons, W_in, 		lr=lr, disinhib=disinhib_Hid)
				dW_act 	= ex.learningStep(bHidNeurons, 	bActNeurons, W_act, 	lr=lr*1e-4, disinhib=disinhib_Act)
				dopa_save = np.append(dopa_save, dopa)

				#update weights
				W_in += dW_in
				W_act += dW_act
				# if (W_act>1.5).any(): import pdb; pdb.set_trace()

				W_in = np.clip(W_in, 1e-10, np.inf)
				W_act = np.clip(W_act, 1e-10, np.inf)

				# if np.isnan(W_in).any(): import pdb; pdb.set_trace()

			#to check Wact assignment after each episode:
			if protocol=='digit':
				RFproba, _, _ = rf.hist(runName, {'000':W_in}, classes, images, labels, protocol, SVM=SVM, output=False, show=False)
			elif protocol=='gabor':
				pref_ori = gr.preferred_orientations({'000':W_in}, params=kwargs)
				RFproba = np.zeros((1, nHidNeurons, nClasses), dtype=int)
				RFproba[0,:,:][pref_ori['000']<=target_ori] = [1,0]
				RFproba[0,:,:][pref_ori['000']>target_ori] = [0,1]
			correct_W_act = 0.	
			same = ex.labels2actionVal(np.argmax(RFproba[0],1), classes, rActions) == rActions[np.argmax(W_act,1)]
			correct_W_act += np.sum(same)
			correct_W_act/=len(RFproba)
			if e==nEpiCrit: print '----------end crit-----------'
			print 'correct action weights: ' + str(int(correct_W_act)) + '/' + str(int(nHidNeurons))


		#save weights
		W_in_save[str(r).zfill(3)] = np.copy(W_in)
		W_act_save[str(r).zfill(3)] = np.copy(W_act)

	""" compute network statistics and performance """

	if protocol=='digit':
		#compute histogram of RF classes
		RFproba, RFclass, _ = rf.hist(runName, W_in_save, classes, images, labels, protocol, SVM=SVM, output=createOutput, show=showPlots, lr_ratio=1.0, rel_classes=classes[rActions!='0'])

	elif protocol=='gabor':
		#compute histogram of RF classes
		n_bins = 10
		bin_size = 180./n_bins
		orientations_bin = np.zeros(len(orientations), dtype=int)
		for i in range(n_bins): 
			mask_bin = np.logical_and(orientations >= i*bin_size, orientations < (i+1)*bin_size)
			orientations_bin[mask_bin] = i

		# RFproba, RFclass, _ = rf.hist(runName, W_in_save, classes, images, labels, protocol, n_bins=10, SVM=SVM, output=False, show=False)
		pref_ori = gr.preferred_orientations(W_in_save, params=kwargs)
		RFproba = np.zeros((nRun, nHidNeurons, nClasses), dtype=int)
		for r in pref_ori.keys():
			RFproba[int(r),:,:][pref_ori[r]<=target_ori] = [1,0]
			RFproba[int(r),:,:][pref_ori[r]>target_ori] = [0,1]
		_, _, _ = rf.hist(runName, W_in_save, range(n_bins), images, orientations_bin, protocol, n_bins=n_bins, SVM=SVM, output=createOutput, show=showPlots)

	#compute correct weight assignment in the action layer
	correct_W_act = 0.
	notsame = {}
	for k in W_act_save.keys():
		same = ex.labels2actionVal(np.argmax(RFproba[int(k)],1), classes, rActions) == rActions[np.argmax(W_act_save[k],1)]
		notsame[k] = np.argwhere(~same)
		correct_W_act += np.sum(same)
	correct_W_act/=len(RFproba)

	# plot the weights
	if createOutput:
		if show_W_act: W_act_pass=W_act_save
		else: W_act_pass=None
		if protocol=='digit':
			rf.plot(runName, W_in_save, RFproba, target=target, W_act=W_act_pass, sort=sort, notsame=notsame)
		elif protocol=='gabor':
			rf.plot(runName, W_in_save, RFproba, W_act=W_act_pass, notsame=notsame)

	#assess classification performance with neural classifier or SVM 
	if classifier=='actionNeurons':	allCMs, allPerf = cl.actionNeurons(runName, W_in_save, W_act_save, classes, rActions, nHidNeurons, nInpNeurons, A, images_test, labels_test, output=createOutput, show=showPlots)
	if classifier=='SVM': 			allCMs, allPerf = cl.SVM(runName, W_in_save, images, labels, classes, nInpNeurons, A, dataset, output=createOutput, show=showPlots)
	if classifier=='neuronClass':	allCMs, allPerf = cl.neuronClass(runName, W_in_save, classes, RFproba, nInpNeurons, A, images_test, labels_test, output=createOutput, show=showPlots)

	print 'correct action weight assignment:\n' + str(correct_W_act) + ' out of ' + str(nHidNeurons)

	#save data
	if createOutput:
		ex.save_data(W_in_save, W_act_save, kwargs)

	print '\nrun: '+runName + '\n'

	# import pdb; pdb.set_trace()

	return allCMs, allPerf, correct_W_act/nHidNeurons, W_in, W_act, RFproba





	



















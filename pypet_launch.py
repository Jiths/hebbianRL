"""
Author: Raphael Holca-Lamarre
Date: 23/10/2014

This code uses PyPet to explore the parameters of the hebbian neural network object.


"""

import os
import matplotlib
if 'mnt' in os.getcwd(): matplotlib.use('Agg') #to avoid sending plots to screen when working on the servers
import numpy as np
import datetime
import time
import pypet
import helper.external as ex
import helper.pypet_helper as pp
np.random.seed(0)

ex = reload(ex)
pp = reload(pp)

""" static parameters """
parameter_dict = {	'dHigh' 			: 4.0,
					'dMid' 				: 0.01,
					'dNeut' 			: -0.25,
					'dLow' 				: -1.0,
					'd_noLabel'			: 0.0,
					'dopa_func' 		: 'discrete', #'exponential', #'discrete', 'linear' 'linear_discrete'
					'dopa_out_same'		: True,
					'train_out_dopa'	: False,
					'dHigh_out'			: 2.0,#0.5,#
					'dMid_out'			: 0.0,#0.1,#
					'dNeut_out'			: -0.0,#-0.1,#
					'dLow_out'			: -2.0,#-0.5,#
					'ach_1' 			: 16.0,
					'ach_2' 			: 9.0,
					'ach_3' 			: 0.0,
					'ach_4' 			: 0.0,
					'ach_func' 			: 'sigmoidal', #'linear', 'exponential', 'polynomial', 'sigmoidal', 'handmade', 'preset'
					'ach_avg' 			: 20,
					'ach_stim' 			: False,
					'ach_uncertainty' 	: True,
					'ach_BvSB' 			: False,
					'ach_approx_class' 	: False,
					'protocol'			: 'digit',#'gabor',#'digit',#'toy_data'
					'name' 				: 'pypet_DA_greedy_cross_val',
					'dopa_release' 		: True, 
					'ach_release'		: False, 
					'n_runs' 			: 5,
					'n_epi_crit'		: 0,	
					'n_epi_fine' 		: 0,
					'n_epi_perc'		: 40,
					'n_epi_post' 		: 0,				
					't_hid'				: 1.0,
					't_out'				: 0.1,
					'A' 				: 1.0e3,
					'lr_hid'			: 5e-3, #5e-4, #5e-3, ##<---------
					'lr_out'			: 5e-7,
					'batch_size' 		: 50,
					'block_feedback'	: False,
					'shuffle_datasets'	: False,
					'cross_validate'	: True,
					'n_hid_neurons'		: 49, #15,#49, ##<-----------
					'weight_init' 		: 'input',
					'init_file'			: 'digit_pretrain_cross_val',
					'lim_weights'		: True,
					'log_weights' 		: 'log',
					'epsilon_xplr'		: 1.0,
					'noise_xplr_hid'	: 0.3,
					'noise_xplr_out'	: 2e4,
					'exploration'		: False,
					'compare_output' 	: True,
					'noise_activ'		: 0.0,
					'pdf_method' 		: 'fit',
					'classifier'		: 'neural_prob',
					'RF_classifier' 	: 'data',
					'test_each_epi'		: False,
					'early_stop'		: False,
					'verbose'			: False,
					'save_light' 		: True,
					'seed' 				: 973#np.random.randint(1000)
					}

""" explored parameters """
explore_dict = {	
					# 'dHigh'			: [+0.00, +4.00, +8.00, +12.0],
					# 'dMid'			: [-0.01, +0.00, +0.01, +0.10],
					# 'dNeut'			: [-0.00, -0.10, -0.25, -0.75],
					# 'dLow'			: [-1.00, -2.00, -3.00, -4.00]

					'dMid'			: [0.0, 0.1, 0.2, 0.5, 1.0],
					'dLow'			: [-0.0, -1.0, -2.0, -3.0, -4.0]

					# 'ach_1'			: [5.0, 10.0, 15.0, 20.0, 25.0],
					# 'ach_2'		 	: [0.5, 1.0, 2.0, 5.0, 10.0],

					# 'd_noLabel'		: [-0.1, -0.01, 0.0, +0.01, +0.1, +0.5, +1.0]
				}

""" load and pre-process images """
images_dict, labels_dict, ori_dict, images_params = ex.load_images(	protocol 		= parameter_dict['protocol'],
																	A 				= parameter_dict['A'],
																	verbose 		= parameter_dict['verbose'],
																	digit_params 	= {	'dataset_train'		: 'train',
																						# 'classes' 			: np.array([ 1, 4, 9 ], dtype=int),
																						# 'classes' 			: np.array([ 0, 1, 3, 5, 8 ], dtype=int),
																						'classes' 			: np.array([ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 ], dtype=int),
																						'dataset_path' 		: '/Users/raphaelholca/Documents/data-sets/MNIST',
																						'even_dataset'		: False,
																						'class_reduce'		: False, ##<-- False
																						'labels_subs'		: 1
																						},
																	gabor_params 	= {	'n_train' 			: 10000,
																						'n_test' 			: 10000,
																						'renew_trainset'	: False,
																						'target_ori' 		: 165.,
																						'excentricity' 		: 90.,#3.0,
																						'noise_pixel'		: 0.0,
																						'rnd_phase' 		: False,
																						'rnd_freq' 			: False,
																						'im_size'			: 50#28
																						},
																	toy_data_params	= {	'dimension' 		: '2D', #'2D' #'3D'
																						'n_points'			: 2000,
																						'separability' 		: '1D', #'1D'#'2D'#'non_linear'
																						'data_distrib' 		: 'uniform' #'uniform' #'normal' #'bimodal'
																						}
																	)

""" create directory to save data """
parameter_dict['pypet_name'] = parameter_dict['name']
save_path = os.path.join('output', parameter_dict['name'])
pp.check_dir(save_path, overwrite=False)
print_dict = parameter_dict.copy()
print_dict.update(explore_dict)
print_dict.update({'images_params':images_params})

""" create pypet environment """
env = pypet.Environment(trajectory 		= 'explore_perf',
						log_stdout		= False,
						add_time 		= False,
						multiproc 		= True,
						ncores 			= 16,
						filename		=  os.path.join(save_path, 'explore_perf.hdf5'))


traj = env.v_trajectory
pp.add_parameters(traj, parameter_dict)

explore_dict = pypet.cartesian_product(explore_dict, tuple(explore_dict.keys())) #if not all entry of dict need be explored through cartesian product replace tuple(.) only with relevant dict keys in tuple

explore_dict['name'] = pp.set_run_names(explore_dict, parameter_dict['name'])
traj.f_explore(explore_dict)

""" launch simulation with pypet for parameter exploration """
tic = time.time()
env.f_run(pp.launch_exploration, images_dict, labels_dict, images_params, save_path)
toc = time.time()

""" save parameters to file """
save_file = os.path.join(save_path, parameter_dict['name'] + '_params.txt')
ex.print_params(print_dict, save_file, runtime=toc-tic)

""" plot results """
name_best = pp.plot_results(folder_path=save_path)
pp.launch_assess(save_path, parameter_dict['name']+name_best, images_dict['train'], labels_dict['train'], curve_method='with_noise', slope_binned=False)
if 'dHigh' in explore_dict.keys() and 'dMid' in explore_dict.keys() and 'dNeut' in explore_dict.keys() and 'dLow' in explore_dict.keys():
	pp.faceting(save_path)

print '\nrun name:\t' + parameter_dict['name']
print 'start time:\t' + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(tic))
print 'end time:\t' + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(toc))
print 'train time:\t' + str(datetime.timedelta(seconds=toc-tic))








































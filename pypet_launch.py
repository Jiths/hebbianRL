"""
Author: Raphael Holca-Lamarre
Date: 23/10/2014

This code uses PyPet to explore the parameters of the hebbian neural network object.
"""

import os
import matplotlib
if 'mnt' in os.getcwd(): matplotlib.use('Agg') #to avoid sending plots to screen when working on the servers
import numpy as np
import time
import pypet
import helper.external as ex
import helper.pypet_helper as pp
np.random.seed(0)

ex = reload(ex)
pp = reload(pp)

""" static parameters """
parameter_dict = {	'dHigh' 			: 0.0,
					'dMid' 				: 0.0,
					'dNeut' 			: 0.0,
					'dLow' 				: 0.0,
					'dopa_out_same'		: True,
					'train_out_dopa'	: False,
					'dHigh_out'			: 6.0,#0.0
					'dMid_out'			: 0.01,#0.2
					'dNeut_out'			: -0.01,#-0.3
					'dLow_out'			: -2.0,#-0.5
					'protocol'			: 'digit',#'gabor',#
					'name' 				: 'pypet_digit_t_1-0_fine_classLayer',
					'n_runs' 			: 1,#50,#
					'n_epi_crit'		: 20,	
					'n_epi_fine' 		: 30,			
					'n_epi_dopa'		: 0,
					'n_epi_post' 		: 0,				
					't'					: 1.0,#0.1,#
					'A' 				: 1.2,
					'lr_hid'			: 5e-3,
					'lr_out'			: 5e-7,
					'batch_size' 		: 50,
					'block_feedback'	: False,
					'n_hid_neurons'		: 49,#16,#
					'init_file'			: '',
					'lim_weights'		: False,
					'epsilon_xplr' 		: 1.0,
					'noise_xplr_hid'	: 0.2,
					'noise_xplr_out'	: 2e4,
					'exploration'		: True,
					'noise_activ'		: 0.0,
					'pdf_method' 		: 'fit',
					'classifier'		: 'neural',
					'test_each_epi'		: True,
					'early_stop'		: False,
					'verbose'			: False,
					'seed' 				: 978 #np.random.randint(1000)
					}

""" explored parameters """
explore_dict = {	'dHigh'			: [+0.000, +0.100, +0.500, +2.000],
					'dNeut'			: [-0.500, -0.100, -0.010, -0.000], 
					
					'dMid'			: [+0.000, +0.010, +0.100, +0.500],
					'dLow'			: [-2.000, -0.500, -0.100, -0.000]
				}

""" load and pre-process images """
images_dict, labels_dict, ori_dict, images_params = ex.load_images(	protocol 		= parameter_dict['protocol'],
																	A 				= parameter_dict['A'],
																	verbose 		= parameter_dict['verbose'],
																	digit_params 	= {	'dataset_train'		: 'train',
																						# 'classes' 			: np.array([ 4, 7, 9 ], dtype=int),
																						'classes' 			: np.array([ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 ], dtype=int),
																						'dataset_path' 		: '/Users/raphaelholca/Documents/data-sets/MNIST',
																						'shuffle'			: False
																						},
																	gabor_params 	= {	'n_train' 			: 10000,
																						'n_test' 			: 10000,
																						'renew_trainset'	: True,
																						'target_ori' 		: 165.,
																						'excentricity' 		: 90.,#3.0,
																						'noise'				: 0.0,
																						'im_size'			: 50#28
																						}
																	)

""" create directory to save data """
save_path = os.path.join('output', parameter_dict['name'])
pp.check_dir(save_path, overwrite=False)
print_dict = parameter_dict.copy()
print_dict.update(explore_dict)
print_dict.update({'images_params':images_params})
save_file = os.path.join(save_path, parameter_dict['name'] + '_params.txt')
ex.print_params(print_dict, save_file)

""" create pypet environment """
env = pypet.Environment(trajectory 		= 'explore_perf',
						log_stdout		= False,
						add_time 		= False,
						multiproc 		= True,
						ncores 			= 10,
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

print "\n\nplotting results"
name_best = pp.plot_results(folder_path=save_path)
pp.launch_assess(save_path, parameter_dict['name']+name_best, images_dict['train'], labels_dict['train'], curve_method='with_noise', slope_binned=False)
pp.faceting(save_path)

print '\nrun name:\t' + parameter_dict['name']
print 'start time:\t' + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(tic))
print 'end time:\t' + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(toc))
print 'train time:\t' + time.strftime("%H:%M:%S", time.gmtime(toc-tic))








































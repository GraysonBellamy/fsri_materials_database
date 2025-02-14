# Cone calorimeter data processing script
#   by: ULRI's Fire Safety Research Institute
#   Questions? Submit them here: https://github.com/ulfsri/fsri_materials_database/issues

# ***************************** Usage Notes *************************** #
# - Script outputs as a function of heat flux                           #
#   -  PDF Graphs dir: /03_Charts/{Material}/Cone                       #
#      Graphs: Extinction_Coefficient, Heat Release Rate Per Unit Area, #
#      Mass Loss Rate, Specific Extinction Area, Smoke Production Rate  #
#                                                                       #
#      CSV Tables dir: /01_Data/{Material}/Cone                         #
#      Tables: Cone Notes, Analysis Data                                #
# ********************************************************************* #

# --------------- #
# Import Packages #
# --------------- #
import os
import glob
import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
import git

# Define variables #
data_dir = '../01_Data/'
save_dir = '../03_Charts/'

hf_list_default = ['25', '50', '75']
quant_list = ['HRRPUA', 'MLR', 'SPR', 'Extinction Coefficient'] #'EHC','SEA'

y_max_dict = {'HRRPUA':500, 'MLR':1, 'SPR':5, 'Extinction Coefficient':2} #'EHC':50,'SEA':1000,
y_inc_dict = {'HRRPUA':100, 'MLR':0.2, 'SPR':1, 'Extinction Coefficient':0.5} #'EHC':10,'SEA':200

label_size = 20
tick_size = 18
line_width = 2
legend_font = 10
fig_width = 10
fig_height = 6

### Fuel Properties ###
e = 13100 # [kJ/kg O2] del_hc/r_0
laser_wl = 632.8/10e9 # m
smoke_density = 1100 # kg/m3
c = 7 # average coefficient of smoke extinction
avg_ext_coeff = 8700 # m2/kg  from Mullholland

def apply_savgol_filter(raw_data):

	# raw_data.drop('Baseline', axis = 'index', inplace = True)
	raw_data = raw_data.dropna()
	converted_data = savgol_filter(raw_data,31,3)
	filtered_data = pd.Series(converted_data, index=raw_data.index.values)
	return(filtered_data.iloc[0:])

def create_1plot_fig():
	# Define figure for the plot
	fig, ax1 = plt.subplots(figsize=(fig_width, fig_height))
	#plt.subplots_adjust(left=0.08, bottom=0.3, right=0.92, top=0.95)

	# Reset values for x & y limits
	x_min, x_max, y_min, y_max = 0, 0, 0, 0

	return(fig, ax1, x_min, x_max, y_min, y_max)

def plot_data(df, rep):

	rep_dict = {'R1': 'k', 'R2': 'b', 'R3': 'r', 'R4': 'g', 'R5': 'm', 'R6': 'c'}

	ax1.plot(df.index, df.iloc[:,0], color=rep_dict[rep], ls='-', marker=None, label = rep)

	y_max = max(df.iloc[:,0])
	y_min = min(df.iloc[:,0])

	x_max = max(df.index)
	x_min = min(df.index)

	return(y_min, y_max, x_min, x_max)

def air_density(temperature):
	# returns density in kg/m3 given a temperature in C
	rho = 1.2883 - 4.327e-3*temperature + 8.78e-6*temperature**2
	return rho

def format_and_save_plot(xlims, ylims, inc, quantity, file_loc):

	label_dict = {'HRRPUA': 'HRRPUA (kW/m$^2$)', 'MLR': 'Mass Loss Rate (g/s)', 'EHC':'Effective Heat of Combustion (MJ/kg)' , 'SPR': 'Smoke Production Rate (1/s)', 'Extinction Coefficient': 'Extinction Coefficient (1/m)'}

	# Set tick parameters
	ax1.tick_params(labelsize=tick_size, length=8, width=0.75, direction = 'inout')

	# Scale axes limits & labels
	ax1.set_ylim(bottom=ylims[0], top=ylims[1])
	ax1.set_xlim(left=xlims[0], right=xlims[1])
	ax1.set_xlabel('Time (s)', fontsize=label_size)

	y_range_array = np.arange(ylims[0], ylims[1] + inc, inc)
	ax1.set_ylabel(label_dict[quantity], fontsize=label_size)

	yticks_list = list(y_range_array)

	x_range_array = np.arange(xlims[0], xlims[1] + 120, 120)
	xticks_list = list(x_range_array)

	if quantity == 'HRRPUA':
		ax1.autoscale(enable = True, axis = 'both')
	else:
		ax1.set_yticks(yticks_list)
		ax1.autoscale(enable = True, axis = 'x')

	ax1.tick_params(axis = 'x', labelrotation = 45)

	# ax2 = ax1.secondary_yaxis('right')
	ax2 = ax1.twinx()
	ax2.tick_params(axis='y', direction='in', length = 4)
	ax2.set_yticks(yticks_list)
	empty_labels = ['']*len(yticks_list)
	ax2.set_yticklabels(empty_labels)

	# ax3 = ax1.secondary_xaxis('top')
	ax3 = ax1.twiny()
	ax3.tick_params(axis='x', direction='in', length = 4)
	ax3.set_xticks(xticks_list)
	empty_labels = ['']*len(xticks_list)
	ax3.set_xticklabels(empty_labels)

	#Get github hash to display on graph
	repo = git.Repo(search_parent_directories=True)
	sha = repo.head.commit.hexsha
	short_sha = repo.git.rev_parse(sha, short=True)
	# short_sha = '*** need python git pkg ***'

	ax1.text(1, 1,'Repository Version: ' + short_sha,
		horizontalalignment='right',
		verticalalignment='bottom',
		transform = ax1.transAxes)

	# Add legend
	handles1, labels1 = ax1.get_legend_handles_labels()

	plt.legend(handles1, labels1, loc = 'upper center', bbox_to_anchor = (0.5, -0.27), fontsize=16,
				handlelength=2, frameon=True, framealpha=1.0, ncol=3)

	# Clean up whitespace padding
	fig.tight_layout()

	# Save plot to file
	plt.savefig(file_loc)
	plt.close()

for d in sorted((f for f in os.listdir(data_dir) if not f.startswith(".")), key=str.lower):
	df_dict = {}
	material = d
	output_df = pd.DataFrame()
	co_df = pd.DataFrame()
	soot_df = pd.DataFrame()
	notes_df = pd.DataFrame()
	if os.path.isdir(f'{data_dir}{d}/Cone/'):
		print(material + ' Cone')
		data_df = pd.DataFrame()
		reduced_df = pd.DataFrame()
		if os.path.isfile(f'{data_dir}{d}/Cone/hf_list.csv'):
			hf_list =  pd.read_csv(f'{data_dir}{d}/Cone/hf_list.csv') # for parsing hf outside of base set of ranges
		else:
			hf_list = hf_list_default
		for f in sorted(glob.iglob(f'{data_dir}{d}/Cone/*.csv')):
			if 'scan' in f.lower():
				label_list = f.split('.csv')[0].split('_')
				label = label_list[-3].split('Scan')[0] + '_' + label_list[-1]
				data_temp_df = pd.read_csv(f, header = 0, skiprows = [1, 2, 3, 4], index_col = 'Names')

				scalar_data_fid = f.replace('Scan','Scalar')
				scalar_data_series = pd.read_csv(scalar_data_fid, index_col = 0).squeeze()

				# Test Notes #
				try:
					pretest_notes = scalar_data_series.at['PRE TEST CMT']
				except:
					pretest_notes = ' '
				surf_area_mm2 = 10000
				dims = 'not specified'
				frame = False
				for notes in pretest_notes.split(';'):
					if 'Dimensions' in notes:
						dims = []
						for i in notes.split(' '):
							try:
								dims.append(float(i))
							except: continue
						surf_area_mm2 = dims[0] * dims[1]
					elif 'frame' in notes:
						frame = True
				if frame or '-Frame' in f:
						surf_area_mm2 = 8836

				surf_area_m2 = surf_area_mm2 / 1000000.0

				notes_df.at[label, 'Surface Area (mm^2)'] = surf_area_mm2
				notes_df.at[label, 'Pretest'] = pretest_notes
				try:
					notes_df.at[label, 'Posttest'] = scalar_data_series.at['POST TEST CMT']
				except:
					notes_df.at[label, 'Posttest'] = ' '


				c_factor = float(scalar_data_series.at['C FACTOR'])

				data_temp_df['O2 Meter'] = data_temp_df['O2 Meter']/100
				data_temp_df['CO2 Meter'] = data_temp_df['CO2 Meter']/100
				data_temp_df['CO Meter'] = data_temp_df['CO Meter']/100

				data_temp_df.loc[:,'EDF'] = ((data_temp_df.loc[:,'Exh Press']/(data_temp_df.loc[:,'Stack TC']+273.15)).apply(np.sqrt)).multiply(c_factor) # Exhaust Duct Flow (m_e_dot)
				data_temp_df.loc[:,'Volumetric Flow'] = data_temp_df.loc[:,'EDF']*air_density(data_temp_df.loc[:,'Smoke TC']) # Exhaust Duct Flow (m_e_dot)
				# O2_offset = 0.2095 - data_temp_df.at['Baseline', 'O2 Meter']
				# data_temp_df.loc[:,'ODF'] = (0.2095 - data_temp_df.loc[:,'O2 Meter'] + O2_offset) / (1.105 - (1.5*(data_temp_df.loc[:,'O2 Meter'] + O2_offset))) # Oxygen depletion factor with only O2
				data_temp_df.loc[:,'ODF'] = (data_temp_df.at['Baseline', 'O2 Meter'] - data_temp_df.loc[:,'O2 Meter']) / (1.105 - (1.5*(data_temp_df.loc[:,'O2 Meter']))) # Oxygen depletion factor with only O2
				data_temp_df.loc[:,'ODF_ext'] = (data_temp_df.at['Baseline', 'O2 Meter']*(1-data_temp_df.loc[:, 'CO2 Meter'] - data_temp_df.loc[:, 'CO Meter']) - data_temp_df.loc[:, 'O2 Meter']*(1-data_temp_df.at['Baseline', 'CO2 Meter']))/(data_temp_df.at['Baseline', 'O2 Meter']*(1-data_temp_df.loc[:, 'CO2 Meter']-data_temp_df.loc[:, 'CO Meter']-data_temp_df.loc[:, 'O2 Meter'])) # Oxygen Depletion Factor with O2, CO, and CO2
				data_temp_df.loc[:,'HRR'] = 1.10*(e)*data_temp_df.loc[:,'EDF']*data_temp_df.loc[:,'ODF']
				data_temp_df.loc[:,'HRR_ext'] = 1.10*(e)*data_temp_df.loc[:,'EDF']*data_temp_df.at['Baseline', 'O2 Meter']*((data_temp_df.loc[:,'ODF_ext']-0.172*(1-data_temp_df.loc[:,'ODF'])*(data_temp_df.loc[:, 'CO2 Meter']/data_temp_df.loc[:, 'O2 Meter']))/((1-data_temp_df.loc[:,'ODF'])+1.105*data_temp_df.loc[:,'ODF']))
				data_temp_df.loc[:,'HRRPUA'] = data_temp_df.loc[:,'HRR']/surf_area_m2
				data_temp_df['THR'] = 0.25*data_temp_df['HRRPUA'].cumsum()/1000
				data_temp_df['MLR_grad'] = -np.gradient(data_temp_df['Sample Mass'], 0.25)
				data_temp_df['MLR'] = apply_savgol_filter(data_temp_df['MLR_grad'])
				data_temp_df['MLR'][data_temp_df['MLR'] > 5] = 0

				data_temp_df['EHC'] = data_temp_df['HRR']/data_temp_df['MLR'] # kW/(g/s) -> MJ/kg
				data_temp_df['Extinction Coefficient'] = data_temp_df['Ext Coeff'] - data_temp_df.at['Baseline','Ext Coeff']
				data_temp_df['SPR'] = (data_temp_df.loc[:,'Extinction Coefficient'] * data_temp_df.loc[:,'Volumetric Flow'])/surf_area_m2
				data_temp_df['SPR'][data_temp_df['SPR'] < 0] = 0
				data_temp_df['SEA'] = (1000*data_temp_df.loc[:,'Volumetric Flow']*data_temp_df.loc[:,'Extinction Coefficient'])/data_temp_df['MLR']
				# data_temp_df['SEA'][np.isinf(data_temp_df['SEA'])] = np.nan

				df_dict[label] = data_temp_df[['Time', 'HRRPUA', 'MLR', 'EHC', 'SPR', 'SEA', 'Extinction Coefficient']].copy()
				df_dict[label].set_index(df_dict[label].loc[:,'Time'], inplace = True)
				df_dict[label] = df_dict[label][df_dict[label].index.notnull()]
				df_dict[label].drop('Time', axis = 1, inplace = True)
				end_time = float(scalar_data_series.at['END OF TEST TIME'])
				num_intervals = (max(df_dict[label].index)-end_time)/0.25
				drop_list = list(np.linspace(end_time, max(df_dict[label].index), int(num_intervals+1)))
				df_dict[label].drop(labels = drop_list, axis = 0, inplace = True)

				output_df.at['Time to Sustained Ignition (s)', label] = scalar_data_series.at['TIME TO IGN']
				output_df.at['Peak HRRPUA (kW/m2)', label] = float("{:.2f}".format(max(data_temp_df['HRRPUA'])))
				output_df.at['Time to Peak HRRPUA (s)', label] = data_temp_df.loc[data_temp_df['HRRPUA'].idxmax(), 'Time'] - float(scalar_data_series.at['TIME TO IGN'])
				ign_index = data_temp_df.index[data_temp_df['Time'] == float(scalar_data_series.at['TIME TO IGN'])][0]
				t60 = str(int(ign_index) + 240)
				t180 = str(int(ign_index) + 720)
				t300 = str(int(ign_index) + 1200)

				try: output_df.at['Average HRRPUA over 60 seconds (kW/m2)', label] = float("{:.2f}".format(np.mean(data_temp_df.loc[ign_index:t60,'HRRPUA'])))
				except: output_df.at['Average HRRPUA over 60 seconds (kW/m2)', label] = math.nan

				try: output_df.at['Average HRRPUA over 180 seconds (kW/m2)', label] = float("{:.2f}".format(np.mean(data_temp_df.loc[ign_index:t180,'HRRPUA'])))
				except: output_df.at['Average HRRPUA over 180 seconds (kW/m2)', label] = math.nan

				try: output_df.at['Average HRRPUA over 300 seconds (kW/m2)', label] = float("{:.2f}".format(np.mean(data_temp_df.loc[ign_index:t300,'HRRPUA'])))
				except: output_df.at['Average HRRPUA over 300 seconds (kW/m2)', label] = math.nan

				output_df.at['Total Heat Released (MJ/m2)', label] = float("{:.2f}".format(data_temp_df.at[scalar_data_series.at['END OF TEST SCAN'],'THR']))
				total_mass_lost = data_temp_df.at['1','Sample Mass'] - data_temp_df.at[scalar_data_series.at['END OF TEST SCAN'],'Sample Mass']
				holder_mass = data_temp_df.at['1','Sample Mass'] - float(scalar_data_series.at['SPECIMEN MASS'])
				output_df.at['Avg. Effective Heat of Combustion (MJ/kg)', label] = float("{:.2f}".format(((data_temp_df.at[scalar_data_series.at['END OF TEST SCAN'],'THR'])*surf_area_m2)/(total_mass_lost/1000)))
				output_df.at['Initial Mass (g)', label] = scalar_data_series.at['SPECIMEN MASS']
				output_df.at['Final Mass (g)', label] = float("{:.2f}".format(data_temp_df.at[scalar_data_series.at['END OF TEST SCAN'],'Sample Mass'] - holder_mass))
				output_df.at['Mass at Ignition (g)', label] = float("{:.2f}".format(data_temp_df.at[ign_index,'Sample Mass'] - holder_mass))

				t10 = data_temp_df['Sample Mass'].sub(data_temp_df.at['1','Sample Mass'] - 0.1*total_mass_lost).abs().idxmin()
				t90 = data_temp_df['Sample Mass'].sub(data_temp_df.at['1','Sample Mass'] - 0.9*total_mass_lost).abs().idxmin()

				output_df.at['Avg. Mass Loss Rate [10% to 90%] (g/m2s)', label] = float("{:.2f}".format(np.mean(data_temp_df.loc[t10:t90,'MLR']/surf_area_m2)))

		for n in quant_list:
			for m in hf_list:
				ylims = [0,0]
				xlims = [0,0]
				fig, ax1, x_min, x_max, y_min, y_max = create_1plot_fig()
				for key, value in df_dict.items():
					rep_str = key.split('_')[-1]
					if m in key:
						plot_df = df_dict[key].filter(regex = n)
						ymin, ymax, xmin, xmax = plot_data(plot_df, rep_str)

				y_min = max(ymin, y_min)
				x_min = max(xmin, x_min)
				y_max = max(ymax, y_max)
				x_max = max(xmax, x_max)

				inc = y_inc_dict[n]

				ylims[0] = y_min - abs(y_min * 0.1)
				ylims[1] = y_max * 1.1
				xlims[0] = x_min
				xlims[1] = x_max

				plot_dir = f'../03_Charts/{material}/Cone/'

				if not os.path.exists(plot_dir):
					os.makedirs(plot_dir)

				format_and_save_plot(xlims, ylims, inc, n, f'{plot_dir}{material}_Cone_{n}_{m}.pdf')

	else:
		continue

	output_df.sort_index(axis=1, inplace=True)
	output_df.to_csv(f'{data_dir}{material}/Cone/{material}_Cone_Analysis_Data.csv', float_format='%.2f')

	notes_df.sort_index(axis=0, inplace=True)
	notes_df.to_csv(f'{data_dir}{material}/Cone/{material}_Cone_Notes.csv', float_format='%.2f')

import os
import time
import pickle
import pandas as pd
import numpy as np
import subprocess
import multiprocessing as mp
import argparse
import pathlib
from tqdm import tqdm
import warnings
import xml.parsers.expat
import warnings
import random
from pm4py.objects.log.importer.xes import importer as xes_importer
import pm4py
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.importer import importer as pnml_importer
from pm4py.algo.simulation.playout.petri_net import algorithm as simulator
from pm4py.statistics.variants.log import get as variants_module
from pm4py.algo.evaluation.earth_mover_distance import algorithm as emd_evaluator
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.util import dataframe_utils

warnings.filterwarnings("ignore", category=UserWarning, module='pm4py.utils')
warnings.filterwarnings("ignore", category=UserWarning, module='pm4py.objects.stochastic_petri')
warnings.filterwarnings("ignore", category=UserWarning, module='pm4py.algo.simulation.montecarlo')

import warnings
import random
from pm4py.objects.log.importer.xes import importer as xes_importer


train_logfile =r'bubble_train.xes'
log = pm4py.read_xes(train_logfile)


log['case:concept:name'] = log['case:concept:name'].astype(str)
log['concept:name']      = log['concept:name'].astype(str)
# log['time:timestamp']    = pd.to_datetime(log['time:timestamp'], utc=True)
log['time:timestamp'] = pd.to_datetime(log['time:timestamp'], format="%Y-%m-%dT%H:%M:%S", utc=True)

test_logfile_path1 = r'selection_test.csv'
full_log1 =  pd.read_csv(test_logfile_path1)

# Directory path for the tracking DataFrame
tracking_df_directory = 'EMD-GROUP-SEL'

# Check if directory exists, and create it if it doesn't
if not os.path.exists(tracking_df_directory):
    os.makedirs(tracking_df_directory)

log = pm4py.convert_to_event_log(log)
language_model = variants_module.get_language(log)
# xes_exporter.apply(language_model, 'language_model_of_train.xes')
print('language of model is produced')
def perform_analysis(num_groups,language_model, test_log,seed=None):
    test_log = test_log.copy()

    test_log['case:concept:name'] = test_log['case:concept:name'].astype(str)
    test_log['concept:name']      = test_log['concept:name'].astype(str)
    # test_log['time:timestamp']    = pd.to_datetime(test_log['time:timestamp'], utc=True)
    #format="%Y-%m-%d %H:%M:%S"
    test_log['time:timestamp'] = pd.to_datetime(test_log['time:timestamp'], utc=True,format="ISO8601")

    # Get unique case IDs and divide them into num_groups
    case_ids = test_log['case:concept:name'].unique()
    # Shuffle case_ids with a seed
    if seed is not None:
        random.seed(seed)
        np.random.shuffle(case_ids)


    grouped_case_ids = np.array_split(case_ids, num_groups)

    emd_results = []

    for group_case_ids in grouped_case_ids:
        group_df = test_log[test_log['case:concept:name'].isin(group_case_ids)]

        if not group_df.empty:
            traditional_log = pm4py.convert_to_event_log(group_df)
            case_language = variants_module.get_language(traditional_log)
            emd_value = emd_evaluator.apply(language_model, case_language)
            emd_results.append(emd_value)

    # Convert the list of results to a DataFrame
    emd_df = pd.DataFrame({'EMD Value': emd_results})

    return emd_df



def main(language_model, full_log1, num_groups):
    emd_estimation_start_time_group = time.time()
    emd_df = perform_analysis(num_groups, language_model, full_log1)
    average_emd = emd_df['EMD Value'].mean()

    emd_estimation_time_group = time.time() - emd_estimation_start_time_group
    return emd_df,average_emd, emd_estimation_time_group

group_counts = [1, 2 ,10 ,50 ,200,500, 1000,2000,5000 ,10000]
seed = 117

tracking_df_group = pd.DataFrame(columns=['Num Groups', 'EMD Estimation Time', 'EMD CSV File'])
tracking_df_group = pd.DataFrame(columns=['Num Groups', 'Average EMD', 'EMD Estimation Time', 'EMD CSV File'])


for num_groups in group_counts:
    print(f'EMD analysis for num_groups= {num_groups} is started')

    emd_df,average_emd , emd_estimation_time_group= main(language_model, full_log1, num_groups)
    print('Emd evaluated')
    csv_file_path = f'{tracking_df_directory}/EMD_SOLO_nGroup{num_groups}.csv'
    emd_df.to_csv(csv_file_path, index=False)
    print(f'EMD results for num_groups= {num_groups} saved to {csv_file_path}')

    new_row = {
        'Num Groups': num_groups,
        'Average EMD': average_emd,
        'EMD Estimation Time': emd_estimation_time_group,
        'EMD CSV File': csv_file_path,
    }

    tracking_csv_file_path = os.path.join(tracking_df_directory, "EMD_SOLO_tracking_groups.csv")

    tracking_df_group = pd.concat([tracking_df_group, pd.DataFrame([new_row])], ignore_index=True)
    tracking_df_group.to_csv(tracking_csv_file_path, index=False)
    print(f'Tracking DataFrame updated for num_groups= {num_groups}')

    print("-------------------------------------------------------------------------------------------------")


print('Analysis finished')

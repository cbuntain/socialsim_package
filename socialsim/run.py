# External imports
import traceback 

import pandas as pd
import numpy  as np

from ast import literal_eval

# Internal imports
from .metrics import Metrics

from .measurements import SocialActivityMeasurements
from .measurements import InformationCascadeMeasurements
from .measurements import SocialStructureMeasurements
from .measurements import CrossPlatformMeasurements
from .measurements import MultiPlatformMeasurements
from .measurements import RecurrenceMeasurements
from .measurements import PersistentGroupsMeasurements

from .visualizations import charts
from .visualizations import transformer

from .visualizations.visualization_config import measurement_plot_params

from .load   import load_measurements
from .record import RecordKeeper
from .utils  import subset_for_test

class TaskRunner:
    def __init__(self, ground_truth, configuration, metadata=None, test=False, plot_dir="./plots"):
        """
        Description: Initializes the TaskRunner object. Stores the metadata and
            ground_truth objects and defines all measurements and metrics
            specified by the configuration dictionary.

        Inputs:
            :ground_truth: (pd.DataFrame)
            :metadata: (ss.MetaData)
            :configuration: (dict)
        Outputs:
            None
        """

        # Set object variables
        self.ground_truth  = ground_truth
        self.metadata      = metadata
        self.configuration = configuration
        self.test          = test
        self.plot_dir      = plot_dir

        if ground_truth is str:
            temp = load_measurements(ground_truth)
            self.ground_truth_results, self.ground_truth_logs = temp
        else:
            temp = run_measurements(ground_truth, configuration, metadata, 
                timing=False, verbose=True, save=False, save_directory='./', 
                save_format='json', test=test)
            
            self.ground_truth_results, self.ground_truth_logs = temp


    def __call__(self, dataset, timing=False, verbose=False, save=False,
        save_directory='./', save_format='json'):
        """
        Description: This function runs the measurements and metrics code at
            across all measurement types. It does not deal with multiple
            platforms.

        """
        configuration = self.configuration

        simulation_results, simulation_logs = run_measurements(dataset,
            configuration, self.metadata, timing, verbose, save, 
            save_directory, save_format, self.test)

        # Get the ground truth measurement results
        ground_truth_results = self.ground_truth_results
        ground_truth_logs    = self.ground_truth_logs

        # Run metrics to compare simulation and ground truth results
        metrics, metrics_logs = run_metrics(simulation_results, 
            ground_truth_results, configuration, verbose, self.plot_dir)

        # Log results at the task level
        results = {
            'simulation_results'   : simulation_results, 
            'ground_truth_results' : ground_truth_results,
            'metrics'              : metrics
        }

        logs    = {
            'simulation_logs'   : simulation_logs,
            'ground_truth_logs' : ground_truth_logs,
            'metrics_logs'      : metrics_logs
        }

        return results, logs

    def get_results(self):
        return self.ground_truth_results, self.ground_truth_logs


def run_measurements(dataset, configuration, metadata, timing, verbose, save,
    save_directory, save_format, test):
    """
    Description: Takes in a dataset and a configuration file and runs the
        specified measurements.

    Input:

    Output:
    """

    results = {}
    logs    = {}

    # Loop over platforms
    for platform in configuration.keys():
        platform_results = {}
        platform_logs    = {}

        dataset_subset = []
        try:
            if verbose:
                message = 'SOCIALSIM TASKRUNNER   | Subsetting '
                message = message + platform+' data... '
                print(message, end='', flush=True)

            if platform=='multi_platform':
                dataset_subset = dataset

            else:
                dataset_subset = dataset[dataset['platform']==platform]

            if test:
                dataset_subset = subset_for_test(dataset_subset)

            if verbose:
                print('Done.', flush=True)

        except Exception as error:
                measurement_logs    = {
                    'status': 'Failed to subset ' + platform, 
                    'error': error
                    }

                if verbose:
                    print('')
                    print('-'*80)
                    trace = traceback.format_exc()
                    print(trace)
                    print('-'*80)

        # Loop over measurement types
        for measurement_type in configuration[platform].keys():
            if measurement_type=='social_activity':
                Measurement = SocialActivityMeasurements
            elif measurement_type=='information_cascades':
                Measurement = InformationCascadeMeasurements
            elif measurement_type=='social_structure':
                Measurement = SocialStructureMeasurements
            elif measurement_type=='cross_platform':
                Measurement = CrossPlatformMeasurements
            elif measurement_type=='multi_platform':
                Measurement = MultiPlatformMeasurements
            elif measurement_type == 'recurrence':
                Measurement = RecurrenceMeasurements
            elif measurement_type == 'persistent_groups':
                Measurement = PersistentGroupsMeasurements

            # Get data and configuration subset
            configuration_subset = configuration[platform][measurement_type]

            try:
                # Instantiate measurement object
                if verbose:
                    message = 'SOCIALSIM TASKRUNNER   | Instantiating '
                    message = message+measurement_type+'... '
                    print(message, end='', flush=True)

                if platform=='multi_platform':
                    measurement = Measurement(dataset_subset,
                                              configuration_subset, metadata)
                else:
                    measurement = Measurement(dataset_subset,platform,
                                              configuration_subset, metadata)

                if verbose:
                    print('Done.')

                try:
                    kwargs = {'verbose':verbose, 'save':save,
                        'save_directory':save_directory, 
                        'save_format':save_format}

                    # Run the specified measurements
                    measurement_results, measurement_logs = measurement.run(**kwargs)

                except Exception as error:
                    measurement_logs    = {
                        'status': 'Measurements object failed to run.', 
                        'error': error
                        }
                    measurement_results = None

                    if verbose:
                        print('')
                        print('-'*80)
                        trace = traceback.format_exc()
                        print(trace)
                        print('-'*80)

            except Exception as error:
                measurement_logs    = {
                    'status': 'Failed to instantiate measurements object', 
                    'error': error
                    }
                measurement_results = None
                
                if verbose:
                    print('')
                    print('-'*80)
                    trace = traceback.format_exc()
                    print(trace)
                    print('-'*80)

            # Log the results at the measurement type level
            platform_results.update({measurement_type:measurement_results})
            platform_logs.update({measurement_type:measurement_logs})

        # Log the results at the platform level
        results.update({platform:platform_results})
        logs.update({platform:platform_logs})

    return results, logs


def run_metrics(simulation, ground_truth, configuration, verbose, plot_dir):
    """
    Description: Takes in simulation and ground truth measurement results and a
        configuration file and runs all the specified metrics on the
        measurements.

    Input:
        :simulation_results:
        :ground_truth_results:
        :configuration:

    Output:
        :results:
        :logs:
    """
    metrics_object = Metrics(simulation=simulation, ground_truth=ground_truth, configuration=configuration)

    results, logs = metrics_object.run(verbose=verbose, plot_dir=plot_dir)

    return results, logs


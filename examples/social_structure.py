import socialsim as ss

# Load the example dataset
dataset = 'data/test_dataset.txt'
dataset = ss.load_data(dataset)

# Subset the dataset to a particular platform 
dataset = dataset[dataset['platform']=='twitter']

# Load the configuration file
config = './data/cp1_configuration.json'
config = ss.load_config(config)

# Subset the configuration for the given task 
config = config['twitter']['social_structure']

# Define the measurement object
social_structure_measurements = ss.SocialStructureMeasurements(dataset, config, None, 'twitter', plot=True,
                                                               node='CVE-2017-0199')

# Run all measurements in the config file
results = social_structure_measurements.run(verbose=True)

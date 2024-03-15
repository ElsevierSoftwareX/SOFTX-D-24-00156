# Stop@

A framework for scalable and noise-resistant stop-move segmentation of large datasets of trajectories in outdoor and indoor spaces.


Stop@ or StopAt, targets the behavior analysis by providing a framework designed for extracting stop-move patterns from staptial trajectories, applicable across mobility data indoor or outdoor.
It is built around a stop detection method (SeqScan), it is responsible for segmenting a trajectories into segments of stop and move. 
Stop@ provides also a set of functionalities for pre-segmenation data analysis, and for analyzing the segmentation results as well.
Stop# includes the parallel processing of large datasets of trajectories.
All the functionalities can be run either using a single processor (single mode), or by parallelism using multiple proessors (bulk mode). 

## Installation

You need to download the project directory. 
Once you're in the project directory, you can start using the project's functionalities by calling the corresponding modules, as described in the exmaples below.

The project requires the python libraries: Pandas, json, multiprocessing, statistics, numpy, utm
You can install them using pip with the provided requirements.txt file.

`pip install -r requirements.txt`

## Code components
The code contains 4 main modules for the 4 main functionalities explained in the section below:  `main_runSeqScan.py`, `run_statistics.py`, `run_trajectory_plotter.py`, `run_statistics_on_stops.py`.
In addition, there is the `config.json`, the configuration file where you can change the default values for variables used in the code.
The `seqscan` directory contains classes and modules utilized by the SeqScan functionality (min_runSeqScan.py), while the `tools` directory consists of classes and modules utilized by the other functionalities.
In the `input` directory, we've made available data examples, the users can try to test the code and better understand the input structure requirements and expected results.
The `output` directory contains examples about the output of the functionalities of the examples shown below.

### config file
The file to configure the values of these variables:
- is_cartesian: true or false; true indicates that the expected spatial coordinates in input are planar, while false means that the coordintes in input are geographic.
- The CSV_COLUMNS variables denote the fields' names in the csv files used as input. This is important for a correct parsing and interpretations of the files.
- TIMESTAMP_FORMAT: define the timestamps format
- UNITS: determine the DISTANCE and TIME units, to be adopted for the values of the segmentation algorithm's parameters and other functionalities.
- OUTPUT_COLUMNS variables denote the fields' names in the output csv files.

### input directory

### output directory 

### Software usage

The software presents 4 functionalities:

1- SeqScan. `main_runSeqScan.py`: the main module that extracts the stops from the trajectories
In order to undersatnd the details of the algorithm and how it works, you may refer to [1]
Seqscan is a cluster-based segmentation technique, that extract stops as clusters that are temporally non-overlapping.
It requires three parameters: the spatial density related parameters (*epsilon* and *n*) and *delta* which denotes the minimum required presence within a cluster to qualify as a ”stop”.
The presence refers to the effective time the entity spends within the location of the stops, excluding the abscence periods called *excursions*.



##References

1- Maria Luisa Damiani, Fatima Hachem, Hamza Issa, Nathan Ranc, Paul Moorcroft, and Francesca Cagnacci. ’Cluster-based trajectory segmentation with local noise’.Data Min. Knowl. Discov. 32, no.4 (2018): 1017–1055

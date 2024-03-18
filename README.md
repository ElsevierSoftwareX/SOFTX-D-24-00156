# Stop@

A framework for scalable and noise-resistant stop-move segmentation of large datasets of trajectories in outdoor and indoor spaces.


Stop@, also known as StopAt, focuses on behavior analysis by offering a framework specifically designed to extract stop-move patterns from spatial trajectories.This framework addresses mobility data from both indoor and outdoor environments.
Built around a stop detection method (SeqScan), it efficiently segments trajectories into stop and move segments. 
Additionally, Stop@ provides a set of functionalities for pre-segmenation data analysis, and for analyzing the segmentation results.

Stop@ also implements parallel processing capabilities for handling large datasets of trajectories.
Users can execute all functionalities either in single processor mode or through parallelism using multiple processors (bulk mode). In single mode, the input must be a single file referring to one moving entity. Conversely, in bulk mode, the input can either be a single file containing data for multiple moving entities or a directory of individual files, each representing data for one entity.

## Installation

You need to download the project directory. 
Once you're in the project directory, you can begin utilizing the project's functionalities by calling the corresponding modules, as described in the examples below.

The project requires the python libraries: Pandas, json, multiprocessing, statistics, numpy, utm.
You can install them using pip with the provided _requirements.txt_ file.

`pip install -r requirements.txt`

## Code components
The code comprises 4 main modules, each corresponding to one of the four primary functionalities described below:  
- `main_runSeqScan.py`
- `run_statistics.py`
- `run_trajectory_plotter.py`
- `run_statistics_on_stops.py`
Additionally, there is a configuration file named _config.json_, where users can adjust default values for variables utilized within the code.
Within the project structure, you'll find the `_seqscan_` directory, containing classes and modules utilized by the SeqScan functionality (in min_runSeqScan.py). Similarly, the `_tools_` directory contains classes and modules utilized by other functionalities.
For user convenience and demonstration purposes, we've included a directory named `_input_`, which provides data examples. These examples can be utilized by users for testing the code and gaining a better understanding of the input structure requirements.
The `_output_` directory contains examples illustrating the output of all the functionalities when employing the input files, while using different scenarios in single/bulk modes (results of the examples provided below).

### config file
The configuration file allows users to adjust the values of the following variables:
- is_cartesian: _true_ or _false_; _true_ indicates that the expected spatial coordinates in input are planar, while _false_ means that the coordintes in input are geographic.
- The CSV_COLUMNS: denotes the field names in the CSV files used as input. This is crucial for accurate parsing and interpretation of the files.
- TIMESTAMP_FORMAT: defines the timestamps format
- UNITS: determines the TIME unit, to be adopted for the value of the segmentation algorithm's parameter (_delta_).
- OUTPUT_COLUMNS: denote the fields' names in the output csv files.

### input directory
The input directory contains mobility data that serves as examples for the functionalities.
The purpose is to have examples covering both planar and geographical coordinates (indoor and outdoor cases), and also to try different scenarios using single and bulk modes, i.e single file for a single moving entity, a single file containing multiple entities, and a directory of files each of which refers to one entity.

Here is the description for the datasets:

- geolife_example.csv: dataset for a __single__ person moving in the city of Beijing, China, in __outdoor__ settings.
  This dataset has been taken from the Microsoft geoLife website[2] (trajectory of user 005 on the day 24/10/2008 (20081024041230)).
  When working with this example, you need to modify the content of the config file accordingly (especially the *INPUT_COLUMNS*, and the *is_cartesian* has to be set to _false_)
  
- atc_7traj.csv: a single file representing dataset for __multiple__ persons (seven) moving in an __indoor__ place (ATC shopping center in Japan).This dataset sample has been taken from [4], and for more details about the data collection and characteristics, you can check [3].
In the config file, *is_cartesian* should be set to *true* and the *INPUT_COLUMNS* need to fit the fields' names of the file.
- atc_7traj: __directory__ containing 7 individual files, each representing the movement of a single person from the ATC dataset.
   
### output directory 
The output directory comprises files and directories that represent the results of functionalities executed based on the examples provided in what follows. 
For each functionality, outputs are provided for both single and bulk modes. In the case of bulk mode, outputs are included for scenarios where the input is either a single file containing data for multiple entities or a directory containing multiple individual files, each representing data for one entity.

### Software usage

The software presents 4 functionalities:
#### 1-SeqScan 
`main_runSeqScan.py`: the main module that extracts the stops from the trajectories
In order to undersatnd the details of the algorithm and how it works, you may refer to [1]
Seqscan is a cluster-based segmentation technique, that extract stops as clusters that are temporally non-overlapping.
It requires three parameters: the spatial density related parameters (*epsilon* and *n*) and *delta* which denotes the minimum required presence within a cluster to qualify as a "stop".
The presence refers to the effective time the entity spends within the location of the stops, excluding the abscence periods called *excursions*.

The output of this functionality consists of two components: point classification and symbolic trajectories. 
The point classification file maintains a structure similar to the input file, but  with four additional fields in order to classify each point into one of these cases: 
1- belonging to a stop
2- an excursion point
3- belonging to a "move" segment
4- a noise point   
The second file represents the symbolic trajectory, consisting of a sequence of the extracted stops. Each stop is represented by its ID, start and end time.

#### Single mode:
```python
  seqscan = mainRun()
  input_path_f = "./input/geolife_example.csv"
  output_path_f = "./output/seqscan_geolife_example.csv"
  output_path_f_symbolic = "./output/symbolic_seqscan_geolife_example.csv"
  # params: 8 m, 15 minutes, 30 points
  seqscan.run_ss_single_mode(8, 15, 30, input_path_f, output_path_f, output_path_f_symbolic)
   ``` 
#### bulk mode:
a) input is a single file of multiple entities:
With parallelism:
```python
  seqscan = mainRun()

  input_path_f = "./input/atc_7traj.csv"
  output_path_f = "./output/seqscan_atc_7traj.csv"
  #params: 1000 mm, 10 sec, 5 points
  seqscan.run_ss_multi_mode(1000, 10, 5, input_file=input_path_f, output_file=output_path_f, max_processors=3)
```
Without parallelism:
```python
  seqscan.run_ss_multi_mode(1000, 10, 5, input_file=input_path_f, output_file=output_path_f, max_processors=3)
```
 b) input is a folder of separate csv files:
 With parallelism:
 ```python
    input_path_folder = "./input/atc_7traj/"
    ##The output path is for a folder where the points classification files are going to be saved, and the folder of symbolic trajectories too
    output_path_folder = "./output/seqscan_output/"

    ## Run Seqscan, using bulk mode, with 10 processors in parallel
    seqscan.run_ss_multi_mode(1000, 10, 5,  # Seqscan parameters
                              input_folder=input_path_folder,
                              output_folder=output_path_folder,
                              max_processors=10)
   ```
Without parallelism:
```python
  seqscan.run_ss_multi_mode(1000, 10, 5,  # Seqscan parameters
                              input_folder=input_path_folder,
                              output_folder=output_path_folder
                              )
```
#### 2- Trajectory plotter
`run_trajectory_plotter.py`: 3D trajectory plotter for visualizing the movement in spatial-temporal dimension.
#### single mode
```python
   plotter = RunPlotter()
   # The input is a single file of 1 trajectory
   input_path_file = "./input/atc_7traj/10340900.csv"
   #The output is a single PNG of the trajectory
   output_path_file = "./output/plot_10340900.png"
    #Plot the trajectory
   plotter.plot_single_mode(input_path_file, output_path_file)
```
#### bulk mode:
a) input is a single file of multiple entities:
With parallelism
```python
   plotter = RunPlotter()
   # The input is a single file of many trajectories
   input_path_file = "./input/atc_7traj.csv"
   # The output is a folder of multiple PNGs
   output_folder = "./output/plots_folder/"
   plotter.plot_multi_mode(input_file=input_path_file, output_folder=output_folder,max_processors=3)
```
Without parallelism
```python
plotter.plot_multi_mode(input_file=input_path_file, output_folder=output_folder)
```
b) input is a folder of separate csv files:
With parallelism
```python
   # The input is a directory of many files
   input_folder = "./input/atc_7traj"
   # The output is a folder of multiple PNGs
   output_folder = "./output/plots_folder/"
   plotter.plot_multi_mode(input_folder=input_folder, output_folder=output_folder, max_processors=3)
```
Without Parallelism
```python
   plotter.plot_multi_mode(input_folder=input_folder, output_folder=output_folder)
```
#### 3- Statistics over the trajectory
`run_statistics.py`. It provides statistical summaries about the trajectory: 
- point count
- total duration
- minimum, maximum, median, average, and standard deviation of step length and duration.
Step length is the distance between two consecutive points. Step duration is the temporal gap between them.

#### single mode
``` python
   stats=RunStatistics()
   #statistics in single mode
   input_file="./input/atc_7traj/10340900.csv"
   output_file = "./output/stats_10340900.csv"
   stats.run_statistics_single_mode(input_file, output_file)
```
#### bulk mode
a) input is a single file of multiple entities:
With parallelism
``` python
   #statistics in bulk mode, single file as input
   input_path_f = "./input/atc_7traj.csv"
   output_path_f = "./output/atc_stats_7traj.csv"
   stats.run_statistics_multi_mode(input_file=input_path_f, output_file=output_path_f, max_processors=3)
```
Without parallelism
``` python
   stats.run_statistics_multi_mode(input_file=input_path_f, output_file=output_path_f)
```

b) input is a folder of separate csv files:
With parallelism
``` python
   #statistics in bulk mode, folder as input
   input_path_folder = "./input/atc_7traj/"
   output_path_folder = "./output/atc_stats/"
   stats.run_statistics_multi_mode(input_folder=input_path_folder, output_folder=output_path_folder, max_processors=3)
```
Without parallelism
``` python
   stats.run_statistics_multi_mode(input_folder=input_path_folder, output_folder=output_path_folder)
```

#### 4- Statistics over the symbolic trajectories
`run_statistics_on_stops.py`. It provides statistics over the stops, results of SeqScan. More specifically it operates over the point classification file. The statistics include:
- The number of stops 
- minimum, maximum, median, average, and standard deviation of their duration.
- average presence/duration (P/D) of the stops. It is a value in ]0,1] to quantify the quality of the stops. For details please refere to [5]

#### single mode
``` python
   # The input is a point classifications file obtained as a result of SeqScan
   input_file = "./output/seqscan_output/output_10340900.csv"
   output_file = "./output/stats_stops_output_10340900.csv"
   stops_stats.run_statistics_single_mode(input_file, output_file)
   ```
#### bulk mode
a) input is a single file of multiple entities:
With parallelism
``` python
   input_path_f = "./output/seqscan_atc_7traj.csv"
   output_path_f = "./output/stats_stops_atc_7traj.csv"
   stops_stats.run_statistics_multi_mode(input_file=input_path_f, output_file=output_path_f, max_processors=4)
```
Without parallelism
``` python
   stops_stats.run_statistics_multi_mode(input_file=input_path_f, output_file=output_path_f)
```

b) input is a folder of separate csv files:
With parallelism
``` python
   input_path_folder = "./output/seqscan_output"
   output_path_folder = "./output/stats_stops_atc_7traj/"
   stops_stats.run_statistics_multi_mode(input_folder=input_path_folder, output_folder=output_path_folder,max_processors=4)
```
Without parallelism
``` python
stops_stats.run_statistics_multi_mode(input_folder=input_path_folder, output_folder=output_path_folder)
  ```
## Citations
Please cite the references below when using this software:

1. Damiani, Maria Luisa, Fatima Hachem, Hamza Issa, Nathan Ranc, Paul Moorcroft, and Francesca Cagnacci. "Cluster-based trajectory segmentation with local noise." Data Mining and Knowledge Discovery 32 (2018): 1017-1055.
2. Hachem, Fatima, Davide Vecchia, Maria Luisa Damiani, and Gian Pietro Picco. "Fine-grained stop-move detection in UWB-based trajectories." In 2022 IEEE International Conference on Pervasive Computing and Communications (PerCom), pp. 111-118. IEEE, 2022.

## References
1. Maria Luisa Damiani, Fatima Hachem, Hamza Issa, Nathan Ranc, Paul Moorcroft, and Francesca Cagnacci. ’Cluster-based trajectory segmentation with local noise’.Data Min. Knowl. Discov. 32, no.4 (2018): 1017–1055
2. GeoLife GPS Trajectories, https://www.microsoft.com/en-us/download/details.aspx?id=52367
3. Brˇsˇcic, Draˇzen, Takayuki Kanda, Tetsushi Ikeda, and Takahiro Miyashita. ’Person tracking in large public spaces using 3-D range sensors’. IEEE Transactions on Human-Machine Systems 43, no. 6 (2013):522-534.
4. Datasets from the ATC shopping center, https://dil.atr.jp/crest2010 HRI/ATC dataset/
5. Maria Luisa Damiani, Hamza Issa, Giuseppe Fotino, Marco Heurich, and Francesca Cagnacci. ’Introducing presence and stationarity index to study partial migration patterns: an application of a spatio-temporal clustering technique’.Int. J. Geogr. Inf. Sci. 30, no.5 (2016): 907–928.

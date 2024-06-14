# Standard modules
import os
import numpy as np
import statistics
import sys
import math
import time

from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict



from seqscan.data.symbolic_trajectory import Symbolic_Trajectory
from seqscan.data.stop import Stop as TrajectoryStop

import pandas as pd
import matplotlib.pyplot as plt
import os
import geopandas as gpd
import contextily as ctx

class PlotSymbolicTrajectories():

    def __init__(self, symbolic_trajectory: Symbolic_Trajectory, output_path, multi_mode=0):
        self.dataset = symbolic_trajectory._data
        self.output_path = output_path
        self.multi_mode = multi_mode
        self.is_cartesian = symbolic_trajectory.is_cartesian
        output_directory = os.path.dirname(self.output_path)
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

    def plot(self, padding=0.1):
        # Check if the dataset is empty
        if not self.dataset:
            print("The dataset is empty. No data to plot.")
            return

        data = {
            'start_time': [s.start_time for s in self.dataset],
            'end_time': [s.end_time for s in self.dataset],
            'label': [s.stop_id for s in self.dataset],
            'x': [s.centroid_x for s in self.dataset],
            'y': [s.centroid_y for s in self.dataset]
        }

        data = pd.DataFrame(data)

        # Check if 'start_time' and 'end_time' columns contain valid datetime values
        valid_start_time = pd.to_datetime(data['start_time'], errors='coerce')
        valid_end_time = pd.to_datetime(data['end_time'], errors='coerce')
        invalid_rows = data[valid_start_time.isna() | valid_end_time.isna()]

        if not invalid_rows.empty:
            print("Invalid or missing datetime values in the following rows:")
            print(invalid_rows)
            return

        # Calculate duration for each point
        data['start_time'] = valid_start_time
        data['end_time'] = valid_end_time
        data['duration'] = (data['end_time'] - data['start_time']).dt.total_seconds()

        # Normalize the duration for marker size
        min_duration = data['duration'].min()
        max_duration = data['duration'].max()

        if min_duration == max_duration:
            # Handle the case where all durations are the same
            data['normalized_duration'] = 1
        else:
            data['normalized_duration'] = (data['duration'] - min_duration) / (max_duration - min_duration)

        # Set a minimum and maximum marker size
        min_marker_size = 50
        max_marker_size = 500

        # Calculate sizes
        sizes = min_marker_size + (max_marker_size - min_marker_size) * data['normalized_duration']

        # Plot setup
        fig, ax = plt.subplots(figsize=(14, 8))

        if self.is_cartesian:
            # Cartesian plot
            ax.scatter(data['x'], data['y'], s=sizes, c='blue', alpha=0.5)
            for i, label in enumerate(data['label']):
                ax.text(data['x'][i], data['y'][i], label)

            ax.set_xlabel('X Coordinate')
            ax.set_ylabel('Y Coordinate')
            ax.set_title('Trajectory in Cartesian Plane')
        else:
            # Geographic plot
            gdf = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data['y'], data['x']), crs="EPSG:4326")

            if gdf.empty:
                print("GeoDataFrame is empty, no data to plot.")
                return

            # Calculate padding
            x_min, y_min, x_max, y_max = gdf.total_bounds

            # Ensure padding does not result in invalid bounding box
            if np.isnan([x_min, y_min, x_max, y_max]).any() or (x_min == x_max) or (y_min == y_max):
                print("Invalid bounding box for GeoDataFrame, cannot plot basemap.")
                return

            # Set axis limits with padding
            x_padding = (x_max - x_min) * padding if x_max > x_min else padding
            y_padding = (y_max - y_min) * padding if y_max > y_min else padding
            ax.set_xlim(x_min - x_padding, x_max + x_padding)
            ax.set_ylim(y_min - y_padding, y_max + y_padding)

            gdf.plot(ax=ax, marker='o', color='blue', markersize=sizes, alpha=0.5)
            for i, row in gdf.iterrows():
                ax.text(row.geometry.x, row.geometry.y, row['label'])

            # Add basemap
            try:
                ctx.add_basemap(ax, crs=gdf.crs.to_string())
            except Exception as e:
                print(f"Error adding basemap: {e}")
            ax.set_title('Trajectory on Spatial Map')

        plt.tight_layout()

        try:
            plt.savefig(self.output_path)
            print(f"Plot saved successfully to {self.output_path}")
        except Exception as e:
            print(f"Error saving plot: {e}")

        plt.close(fig)






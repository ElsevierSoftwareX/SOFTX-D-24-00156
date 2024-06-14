import os
import numpy as np
import pandas as pd
import math
import csv
import json

from datetime import datetime, timedelta

# Assuming Stop_Point and other necessary definitions are imported correctly

with open('.\config.json') as f:
    config = json.load(f)

TAG_COLUMN = config["CSV_columns"]["TAG_COLUMN"]
TIME_UNIT = config["UNITS"]["TIME"]


class StatisticsMoves():

    def __init__(self, list_seqscan_points, output_path, tag_id=None, multi_mode=0, is_cartesian=True):
        self.list_seqscan_points = list_seqscan_points
        self.output_path = output_path
        self.multi_mode = multi_mode
        self.tag_id = tag_id
        self.is_cartesian = is_cartesian

        output_directory = os.path.dirname(self.output_path)
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

    def calculate_distance(self, row1, row2):
        if self.is_cartesian:
            return np.sqrt((row2.x - row1.x) ** 2 + (row2.y - row1.y) ** 2)
        else:
            return self._haversine_distance(row1.x, row1.y, row2.x, row2.y)

    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        dlon = math.radians(lon2) - math.radians(lon1)
        dlat = math.radians(lat2) - math.radians(lat1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(
            dlon / 2) ** 2
        return 2 * math.asin(math.sqrt(a)) * 6371009

    def convert_duration_from_s(self, t):
        if TIME_UNIT == 'min':
            return float(t) / 60.0
        elif TIME_UNIT == 'd':
            return float(t) / (3600.0 * 24.0)
        return t

    def calculate_radius_of_gyration(self, move_coords):
        if len(move_coords) == 0:
            return None
        mean_coords = np.mean(move_coords, axis=0)
        squared_distances = np.sum((move_coords - mean_coords) ** 2, axis=1)
        return np.sqrt(np.mean(squared_distances))

    def run(self):
        data = pd.DataFrame([{
            'x': sp.x,
            'y': sp.y,
            'timestamp': sp.timestamp,
            'cl': sp.cl,
            'type': sp.type,
            'details': sp.details,
            'tag_id': sp.tag_id
        } for sp in self.list_seqscan_points])

        if data.empty:
            print("No data available.")
            return

        data['timestamp'] = pd.to_datetime(data['timestamp'])

        move_points_count = 0
        move_parts_count = 0
        step_lengths = []
        speeds = []
        step_durations = []
        move_parts_durations = []
        move_parts_radii = []

        previous_row = None
        in_move_part = False
        move_start_time = None
        current_move_coords = []

        for index, row in data.iterrows():
            if row['cl'] == -1:
                move_points_count += 1
                current_move_coords.append([row['x'], row['y']])
                if not in_move_part:
                    move_parts_count += 1
                    in_move_part = True
                    move_start_time = row['timestamp']
                if previous_row is not None and previous_row['cl'] == -1:
                    step_length = self.calculate_distance(previous_row, row)
                    step_lengths.append(step_length)
                    step_duration = self.convert_duration_from_s(
                        (row['timestamp'] - previous_row['timestamp']).total_seconds())
                    step_durations.append(step_duration)
                    if step_duration > 0:
                        speeds.append(step_length / step_duration)
            else:
                if in_move_part:
                    move_duration = self.convert_duration_from_s((row['timestamp'] - move_start_time).total_seconds())
                    move_parts_durations.append(move_duration)
                    in_move_part = False
                    # Calculate radius of gyration for the completed move part
                    radius = self.calculate_radius_of_gyration(np.array(current_move_coords))
                    move_parts_radii.append(radius)
                    current_move_coords = []  # reset move_coords for the next move part

            previous_row = row

        if in_move_part:
            move_duration = self.convert_duration_from_s((data.iloc[-1]['timestamp'] - move_start_time).total_seconds())
            move_parts_durations.append(move_duration)
            # Calculate radius of gyration for the last move part
            radius = self.calculate_radius_of_gyration(np.array(current_move_coords))
            move_parts_radii.append(radius)

        step_length_stats = self.calculate_stats(step_lengths)
        speed_stats = self.calculate_stats(speeds)
        step_duration_stats = self.calculate_stats(step_durations)
        move_parts_duration_stats = self.calculate_stats(move_parts_durations)

        # Calculate statistics for move parts radii
        move_parts_radii_stats = self.calculate_stats(move_parts_radii)

        statistics = {
            'number_of_move_points': move_points_count,
            'number_of_move_parts': move_parts_count,
            'min_step_length': step_length_stats['min'],
            'max_step_length': step_length_stats['max'],
            'average_step_length': step_length_stats['average'],
            'std_step_length': step_length_stats['std'],
            'median_step_length': step_length_stats['median'],
            'min_speed': speed_stats['min'],
            'max_speed': speed_stats['max'],
            'average_speed': speed_stats['average'],
            'std_speed': speed_stats['std'],
            'median_speed': speed_stats['median'],
            'min_step_duration': step_duration_stats['min'],
            'max_step_duration': step_duration_stats['max'],
            'average_step_duration': step_duration_stats['average'],
            'std_step_duration': step_duration_stats['std'],
            'median_step_duration': step_duration_stats['median'],
            'min_move_parts_duration': move_parts_duration_stats['min'],
            'max_move_parts_duration': move_parts_duration_stats['max'],
            'average_move_parts_duration': move_parts_duration_stats['average'],
            'std_move_parts_duration': move_parts_duration_stats['std'],
            'median_move_parts_duration': move_parts_duration_stats['median'],
            'min_radius_of_gyration': move_parts_radii_stats['min'],
            'max_radius_of_gyration': move_parts_radii_stats['max'],
            'average_radius_of_gyration': move_parts_radii_stats['average'],
            'std_radius_of_gyration': move_parts_radii_stats['std'],
            'median_radius_of_gyration': move_parts_radii_stats['median']
        }

        csv_columns = list(statistics.keys())
        csv_data = statistics

        if self.tag_id is not None:
            csv_columns.insert(0, TAG_COLUMN)
            csv_data[TAG_COLUMN] = self.tag_id

        if self.multi_mode == 0 or self.multi_mode == 1:
            with open(self.output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_columns)
                writer.writeheader()
                writer.writerow(csv_data)
        elif self.multi_mode == 2:
            with open(self.output_path, mode='a', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=csv_columns)
                writer.writerow(csv_data)

        print(f"Statistics saved to {self.output_path}")

    def calculate_stats(self, series):
        return {
            'min': np.min(series) if len(series) > 0 else None,
            'max': np.max(series) if len(series) > 0 else None,
            'average': np.mean(series) if len(series) > 0 else None,
            'std': np.std(series) if len(series) > 0 else None,
            'median': np.median(series) if len(series) > 0 else None
        }

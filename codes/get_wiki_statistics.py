import gzip
import argparse
import os
import numpy as np

from collections import Counter

LOG_INTERVAL = 1000000

parser = argparse.ArgumentParser()
parser.add_argument("--wikifile", help="File path for wikipedia passages file", type=str, required=True)
args = parser.parse_args()
data_path = args.wikifile

print("Processing", data_path, "...")

data = []

log_index = 0
if data_path[-3:] == ".gz":
   with gzip.open(data_path, "rb") as f:
      _ = f.readline()
      for line in f:
         data.append(line.decode().strip().split("\t")[2])
         if log_index % LOG_INTERVAL == 0:
            print("Currently at line", log_index)
         log_index += 1
else:
   with open(data_path, "r") as f:
      _ = f.readline()
      for line in f:
         data.append(line.strip().split("\t")[2])
         if log_index % LOG_INTERVAL == 0:
            print("Currently at line", log_index)
         log_index += 1
print("Finished processing file.")

data = np.asarray(data, dtype=str)
print("\nDataset statistics:")
print(data.shape[0], "passages")
print(len(set(data)), "unique titles")
import random
import numpy as np

def local_computation():
    return random.randint(1, 6)

def global_aggregation(data_incoming):
    return np.sum(data_incoming)

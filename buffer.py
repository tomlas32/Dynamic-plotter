import numpy as np


# define buffer - using circular approach
class CircularBuffer:
    # constructor for circular buffer
    def __init__(self, max_size):
        self.max_size = max_size
        self.buffer = np.empty(max_size, dtype=object)
        self.index = 0
        self.full = False

    # get function for fetching data from the buffer
    def get_data(self):
        if self.full:
            return np.concatenate(
                (self.buffer[self.index :], self.buffer[: self.index])
            )
        else:
            return self.buffer[: self.index]

    def get_data_for_plot(self):
        data = self.get_data()
        if data.size > 0:
            timestamp, values = zip(*data)
            return np.array(timestamp, dtype=np.float64), np.array(
                values, dtype=np.float64
            )
        else:
            return np.array([], dtype=np.float64), np.array([], dtype=np.float64)

    # push function for adding data to the buffer
    def push(self, item):
        self.buffer[self.index] = item
        self.index = (self.index + 1) % self.max_size
        if self.index == 0:
            self.full = True

import numpy as np
import scipy as sc
import pandas as pd
import app.PCA.spreadsheet_import as spi
import traceback
class TabData:
    def __init__(self, data, columns, rows, scaled):
        self.data = data
        self.columns = columns
        self.rows = rows
        self.scaled = scaled
        self.row_count = data.shape[0]
        self.col_count = data.shape[1]

    @classmethod
    def from_param(cls, data, columns, rows, scaled) -> 'TabData':
        "Initialize MyData from a dict's items"
        return cls(data, columns, rows, scaled)

    @classmethod
    def empty(cls) -> 'TabData':
        """
        Initialise an empty TabData object
        :return:
        """
        return cls(None, None, None, None)

    @classmethod
    def from_file(cls, filename, header=True, index=True, sep ='\t') -> 'TabData':
        """

        :param filename:
        :param header:
        :param index:
        :param sep:
        :return:
        """
        if header:
            header = 0
        else:
            header = None

        if index:
            index = 0
        else:
            index = None
        try:
            data = pd.read_csv(filepath_or_buffer=filename, header=header, sep=sep, index_col=index)
            sample_ids = data.index
            variable_names = data.columns.values
            data = data.values
        except Exception:
            traceback.print_exc()
        #data, rows, columns = spi.data_import(filename, header=header, rownames=index, sep=sep)
        return cls(data, variable_names, sample_ids, None)


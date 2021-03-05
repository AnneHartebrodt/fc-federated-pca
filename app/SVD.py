import app.TabData as TabData
import app.PCA.shared_functions as sh

class SVD:
    def __init__(self, H, G, S, tabdata: 'TabData', k: int):
        self.H = H
        self.G = G
        self.S = S
        self.tabdata = tabdata
        self.k = k

    @classmethod
    def init_random(cls,  tabdata, k=10) -> 'SVD':
        """
        Initialise an SVD object with random matrices
        :param k: number of eigenvectors, (default: 10)
        :param tabdata: TabData object.
        :return:
        """

        H = sh.generate_random_gaussian(tabdata.row_count, k)
        G = sh.generate_random_gaussian(tabdata.col_count, k)
        S = sh.generate_random_gaussian(k, 1).flatten()
        return cls(H, G, S, tabdata, k)

    @classmethod
    def init_param(cls, H, G, S, tabdata, k=10) -> 'SVD':
        """
        Initialise an SVD object from pre-existing vector
        :param H: right eigenvector matrix
        :param G: left eigenvector matrix
        :param S: eigenvalues
        :param tabdata: TabData object
        :param k: number of eigenvectors
        :return: instance of class 'SVD'
        """
        return cls(H, G, S, tabdata, k)

    @classmethod
    def from_file(cls, filename) -> 'SVD':
        #TODO: implement this
        return (None, None, None, None, None)

    @classmethod
    def from_json(cls, json_file) -> 'SVD':
        # TODO: implement this
        return (None, None, None, None, None)
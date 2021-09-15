from enum import Enum

class QR(Enum):
    FEDERATED_QR = 'federated_qr'
    CENTRALISED_QR = 'centralised_qr'
    NO_QR = 'no_qr'

    @staticmethod
    def from_str(label):
        if label == 'federated_qr':
            return QR.FEDERATED_QR
        else:
            return QR.NO_QR
from ABM.TransportationGraph import TransportationGraph


class AirGraph(TransportationGraph):
    """Basically nx graph wrapper with some airway-specific characteristics"""
    def __init__(self, orig=None):
        super().__init__(orig)

from ABM.TransportationGraph import TransportationGraph


class SubwayGraph(TransportationGraph):
    """Basically nx graph wrapper with some subway-specific characteristics"""
    def __init__(self, orig=None, route_dict=None):
        super().__init__(orig)

        if route_dict is not None:
            self._routing_dict = route_dict
        else:
            print('Warning, missing route dict currently not supported!')

    @property
    def routing_dict(self):
        return self._routing_dict

    @routing_dict.setter
    def routing_dict(self, value):
        self._routing_dict = value


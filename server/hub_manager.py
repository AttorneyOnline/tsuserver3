
import oyaml as yaml #ordered yaml

from server.area_manager import AreaManager
from server.exceptions import AreaError

class HubManager:
    """Holds the list of all Area Managers (Hubs)."""

    def __init__(self, server):
        self.server = server
        self.hubs = []
        self.load_hubs()

    def load_hubs(self):
        with open('config/areas.yaml', 'r', encoding='utf-8') as chars:
            hubs = yaml.safe_load(chars)

        for hub in hubs:
            _hub = AreaManager(self.server)
            _hub.load(hub)
            self.hubs.append(_hub)

    def default_hub(self):
        return self.hubs[0]

    def get_hub_by_name(self, name):
        for hub in self.hubs:
            if hub.name.lower() == name.lower():
                return hub
        raise AreaError('Hub not found.')

    def get_hub_by_id(self, num):
        for hub in self.hubs:
            if hub.id == num:
                return hub
        raise AreaError('Hub not found.')
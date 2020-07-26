
import oyaml as yaml #ordered yaml

from server.area_manager import AreaManager
from server.exceptions import AreaError

class HubManager:
    """Holds the list of all Area Managers (Hubs)."""

    def __init__(self, server):
        self.server = server
        self.hubs = []
        self.load()

    @property
    def clients(self):
        clients = set()
        for hub in self.hubs:
            clients = clients | hub.clients
        return clients

    def load(self, path='config/areas.yaml'):
        try:
            with open(path, 'r', encoding='utf-8') as stream:
                hubs = yaml.safe_load(stream)
        except:
            raise AreaError(f'File path {path} is invalid!')
        for hub in hubs:
            if 'area' in hub:
                # Legacy support triggered! Abort operation
                _hub = AreaManager(self)
                _hub.load_areas(hubs)
                self.hubs.append(_hub)
                break
            _hub = AreaManager(self)
            _hub.load(hub)
            self.hubs.append(_hub)

    def save(self, path='config/areas.yaml'):
        try:
            with open(path, 'w', encoding='utf-8') as stream:
                hubs = []
                for hubs in self.hubs:
                    hubs.append(hub.save())
                yaml.dump(hubs, stream, default_flow_style=False)
        except:
            raise AreaError(f'File path {path} is invalid!')

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
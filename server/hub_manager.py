
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

    def load(self, path='config/areas.yaml', hub_id=-1):
        try:
            with open(path, 'r', encoding='utf-8') as stream:
                hubs = yaml.safe_load(stream)
        except:
            raise AreaError(f'File path {path} is invalid!')

        if hub_id != -1:
            try:
                self.hubs[hub_id].load(hubs[hub_id], destructive=True)
            except ValueError:
                raise AreaError(f'Invalid Hub ID {hub_id}! Please contact the server host.')
            return

        if 'area' in hubs[0]:
            # Legacy support triggered! Abort operation
            if len(self.hubs) <= 0:
                self.hubs.append(AreaManager(self, f'Hub 0'))
            self.hubs[0].load_areas(hubs)
            return

        i = 0
        for hub in hubs:
            while len(self.hubs) < len(hubs):
                # Make sure that the hub manager contains enough hubs to update with new information
                self.hubs.append(AreaManager(self, f'Hub {len(self.hubs)}'))
            while len(self.hubs) > len(hubs):
                # Clean up excess hubs
                h = self.hubs.pop()
                clients = h.clients.copy()
                for client in clients:
                    client.set_area(self.default_hub().default_area())

            self.hubs[i].load(hub)
            self.hubs[i].o_name = self.hubs[i].name
            self.hubs[i].o_abbreviation = self.hubs[i].abbreviation
            i += 1

    def save(self, path='config/areas.yaml'):
        try:
            with open(path, 'w', encoding='utf-8') as stream:
                hubs = []
                for hub in self.hubs:
                    hubs.append(hub.save())
                yaml.dump(hubs, stream, default_flow_style=False)
        except:
            raise AreaError(f'File path {path} is invalid!')

    def default_hub(self):
        """Get the default hub."""
        return self.hubs[0]

    def get_hub_by_name(self, name):
        """Get a hub by name."""
        for hub in self.hubs:
            if hub.name.lower() == name.lower():
                return hub
        raise AreaError('Hub not found.')

    def get_hub_by_id(self, num):
        """Get a hub by ID."""
        for hub in self.hubs:
            if hub.id == num:
                return hub
        raise AreaError('Hub not found.')

    def get_hub_by_abbreviation(self, abbr):
        """Get a hub by abbreviation."""
        for hub in self.hubs:
            if hub.abbreviation.lower() == abbr.lower():
                return hub
        raise AreaError('Hub not found.')
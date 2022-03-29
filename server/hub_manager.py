import oyaml as yaml  # ordered yaml

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

    def load(self, path="config/areas.yaml", hub_id=-1):
        try:
            with open(path, "r", encoding="utf-8") as stream:
                hubs = yaml.safe_load(stream)
        except Exception:
            raise AreaError(f"File path {path} is invalid!")

        if hub_id != -1:
            try:
                self.hubs[hub_id].load(hubs[hub_id], destructive=True)
            except ValueError:
                raise AreaError(
                    f"Invalid Hub ID {hub_id}! Please contact the server host."
                )
            return

        if "area" in hubs[0]:
            # Legacy support triggered! Abort operation
            if len(self.hubs) <= 0:
                self.hubs.append(AreaManager(self, "Hub 0"))
            self.hubs[0].load_areas(hubs)

            is_dr_hub = False
            # tsuserverDR conversion hell
            for i, area in enumerate(hubs):
                # oh God why did they do it this way
                if "reachable_areas" in area:
                    reachable_areas = area["reachable_areas"].split(",")
                    # I hate this
                    for a_name in reachable_areas:
                        a_name = a_name.strip()
                        target_area = self.hubs[0].get_area_by_name(
                            a_name, case_sensitive=True
                        )
                        self.hubs[0].areas[i].link(target_area.id)
                        print(
                            f"[tsuDR conversion] Linking area {self.hubs[0].areas[i].name} to {target_area.name}"
                        )
                        is_dr_hub = True
                if "default_description" in area:
                    self.hubs[0].areas[i].desc = area["default_description"]
                if "song_switch_allowed" in area:
                    self.hubs[0].areas[i].can_dj = area["song_switch_allowed"]
            if is_dr_hub:
                self.hubs[0].arup_enabled = False
                print(
                    "[tsuDR conversion] Setting hub 0 ARUP to False due to TsuserverDR yaml supplied. Please use /save_hub as a mod to adapt the areas.yaml to KFO style."
                )
            return

        i = 0
        for hub in hubs:
            while len(self.hubs) < len(hubs):
                # Make sure that the hub manager contains enough hubs to update with new information
                self.hubs.append(AreaManager(self, f"Hub {len(self.hubs)}"))
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

    def save(self, path="config/areas.yaml"):
        try:
            with open(path, "w", encoding="utf-8") as stream:
                hubs = []
                for hub in self.hubs:
                    hubs.append(hub.save())
                yaml.dump(hubs, stream, default_flow_style=False)
        except Exception:
            raise AreaError(f"File path {path} is invalid!")

    def default_hub(self):
        """Get the default hub."""
        return self.hubs[0]

    def get_hub_by_name(self, name):
        """Get a hub by name."""
        for hub in self.hubs:
            if hub.name.lower() == name.lower():
                return hub
        raise AreaError("Hub not found.")

    def get_hub_by_id(self, num):
        """Get a hub by ID."""
        for hub in self.hubs:
            if hub.id == num:
                return hub
        raise AreaError("Hub not found.")

    def get_hub_by_abbreviation(self, abbr):
        """Get a hub by abbreviation."""
        for hub in self.hubs:
            if hub.abbreviation.lower() == abbr.lower():
                return hub
        raise AreaError("Hub not found.")

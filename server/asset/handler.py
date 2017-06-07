from server.exceptions import ClientError, ServerError

class AssetProtocolHandler:
    """
    Manages the entire network protocol during the
    asset download process.
    """

    def __init__(self, client):
        self.client = client
        raise NotImplementedError
    
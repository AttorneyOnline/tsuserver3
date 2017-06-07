import logger


class AssetIndex:
    """
    Object representation of everything that is in the index.
    """

    __slots__ = 'backgrounds', 'characters', 'evidence', 'music', 'misc'

    def __init__(self):
        self.backgrounds = []
        self.characters  = []
        self.evidence    = []
        self.music       = []
        self.misc        = []

    def generate():
        """ Create a fresh asset index by
        scanning the server's folders.
        """

        index = AssetIndex()

        raise NotImplementedError
        #return index

    def soft_reload():
        """ Check the hash of each known asset
        and modify their hash if needed.
        """
        for asset_type in self.__slots__:
            for asset in self[asset_type]:
                new_hash = asset.calculate_hash()
                if new_hash != asset.hash:
                    logger.log_debug(
                        "Hash for {} ({}) changed from {} to {}"
                        .format(asset.name, asset.type,
                            asset.hash, asset.new_hash)
                    )
                    asset.hash = new_hash

    def from_file(path):
        """ Load an asset index from a file.

        :return: New instance of AssetIndex
        """
        raise NotImplementedError

    def save_to_file(self, path):
        """ Save an asset index to a file.
        """
        raise NotImplementedError
import hashlib
import warnings


class Asset:
    """
    The basic structure of any asset that is to be transferred
    over the network.
    """

    def __init__(self, hash, name):
        self.hash = hash
        self.name = name
        self.files = []  # Virtual path to each file

    def calculate_hash(self):
        """ Calculate the hash (checksum) of the asset based on the
        data of all files which the asset consists of. Uses MD5.

        :return: Hexadecimal representation of the hash, truncated
        to 24 characters
        """

        hasher = hashlib.md5()

        try:
            for filename in files:
                with open(filename, "rb") as file:
                    for chunk in iter(lambda: file.read(4096), b""):
                        hasher.update(chunk)
        except OSError as e:
            warnings.warn("Couldn't calculate an accurate hash: {}".format(str(e)),
                RuntimeWarning)

        return hasher.hexdigest()

    @property
    def type(self):
        return type(self).__name__

class Background(Asset):
    """
    Holds background assets.
    """

    def __init__(self, hash, name):
        __super__.__init__(hash, name)


class Character(Asset):
    """
    Holds character assets.
    """
    
    def __init__(self, hash, name):
        __super__.__init__(hash, name)


class Evidence(Asset):
    """
    Holds evidence assets.
    """
    
    def __init__(self, hash, name):
        __super__.__init__(hash, name)


class SingleFileAsset(Asset):
    """
    A special type of asset that can only hold one file.
    """

    def __init__(self, hash, name, path):
        __super__.__init__(hash, name)
        self.files = [path]


class Music(SingleFileAsset):
    """
    Holds a single music file.
    """
    
    def __init__(self, hash, name, path):
        __super__.__init__(hash, name, path)


class CustomAsset(SingleFileAsset):
    """
    A custom asset that doesn't fit anywhere else.
    """
    pass

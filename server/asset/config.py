import warnings


class TransferConfig:
    """
    Configuration data for how the server should transfer data
    to clients.
    """

    class TransferMethod(Enum):
        DIRECT = 1
        REMOTE = 2
        BIGONLY = 3

    def __init__(self, uuid, method, big_archive = None, remote_location = None)
        self.uuid = uuid
        self.method = method
        self.big_archive = big_archive
        self.remote_location = remote_location

        if self.method == TransferMethod.REMOTE and \
                self.remote_location is None:
            warnings.warn(
                ("Preferred transfer method is via remote server, "
                 "but no specified remote location! Correcting to "
                 "direct mode"),
                RuntimeWarning
            )
            self.method = TransferMethod.DIRECT
        elif self.method == TransferMethod.BIGONLY and \
                self.big_archive is None:
            warnings.warn(
                ("Preferred transfer method is via big archive, "
                 "but no specified big archive info! Correcting "
                 "to direct mode"),
                RuntimeWarning
            )
            self.method = TransferMethod.DIRECT

    def generate_default_config():
        """ Instantiate a default transfer config. """
        return TransferConfig()

    def from_file(path):
        """ Load a transfer config from a file.

        :return: New instance of TransferConfig
        """
        raise NotImplementedError


class BigArchive:
    """
    Represents a large archive file that can be downloaded from the Web.
    """

    __slots__ = 'url', 'revision'

    def __init__(self, url, revision):
        self.url = url
        self.revision = revision
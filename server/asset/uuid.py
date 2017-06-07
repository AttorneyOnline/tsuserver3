from uuid import getnode, uuid5


AOSERVER_NAMESPACE_UUID = "7d9a2ae2-86e9-4162-a09e-c878e937f084"

def generate_uuid():
    """ Generate a deterministic UUID.
    This is made deterministic in case the server owner
    accidentally deletes the config.

    It uses the MAC address of the server and a randomly generated UUID
    representing the namespace of all Attorney Online servers, takes the
    SHA-1 hash of the combination, and turns it into a Version 5 UUID.

    :return: String representation of version 5 UUID
    """

    return str(uuid5(AOSERVER_NAMESPACE_UUID, getnode()))
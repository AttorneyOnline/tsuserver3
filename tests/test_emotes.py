from configparser import ConfigParser
from server.emotes import Emotes


def test_create_config_parser_return_type():
    assert Emotes._create_config_parser() == ConfigParser()

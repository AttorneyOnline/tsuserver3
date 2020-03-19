from server.fantacrypt import fanta_decrypt, fanta_encrypt

def test_fanta_decrypt():
    assert fanta_decrypt("4D90") == "MS"

def test_fanta_encrypt():
    assert fanta_encrypt("MS") == "4D90"
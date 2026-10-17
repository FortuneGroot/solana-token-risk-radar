ALPHABET="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def base58_decode(value:str)->bytes:
    number=0
    for char in value:
        if char not in ALPHABET: raise ValueError("Invalid Solana contract address")
        number=number*58+ALPHABET.index(char)
    body=number.to_bytes((number.bit_length()+7)//8,"big") if number else b""
    return b"\0"*(len(value)-len(value.lstrip("1")))+body


def validate_contract(value:str)->str:
    value=value.strip()
    if not 32<=len(value)<=44 or len(base58_decode(value))!=32: raise ValueError("Enter a valid Solana token contract address.")
    return value

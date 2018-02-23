import codecs

def str_to_b64(string,to_bytestring = False):
    if not type(string) == bytes:
        string = string.encode()  # Ensure the input is in byte format
    result = codecs.encode(string,"base64")
    if not to_bytestring:
        result = result.decode()
    return result

def b64_to_bstr(base64_string):
    if not type(base64_string) == bytes:
        base64_string = base64_string.encode()  # Ensure the input is in byte format
    return codecs.decode(base64_string,"base64")

##def string_to_base64(string,to_bytestring = False):
##    return bstring_to_base64(string.encode(),to_bytestring)

def b64_to_str(base64_string):
    return base64_to_bstring(base64_string).decode()

    

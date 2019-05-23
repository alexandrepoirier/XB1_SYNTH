import configparser

def read(path, replacewithnone=False):
    parser = configparser.ConfigParser()
    parser.read(path)
    config = {}
    for key, value in parser.items():
        config[key] = value
        if isinstance(value, configparser.SectionProxy):
            config[key] = dict(value.items())

    if config['DEFAULT'] == {}:
        config.pop('DEFAULT')

    types = []

    # format data according to specified types, if any
    for key in config:
        if 'types' in key:
            types.append(key)
            data_key = key[:key.find('_types')]
            for elem in config[data_key]:
                if config[data_key][elem] == "None":
                    config[data_key][elem] = None
                elif config[data_key][elem] != "":
                    exec("config[data_key][elem] = {}(config[data_key][elem])".format(config[key][elem]))
                else:
                    if replacewithnone:
                        config[data_key][elem] = None

    # remove types keys from dict
    for key in types:
        config.pop(key)

    return config

import configparser 

class Configurations:
    def __init__(self, configFile) -> None:
        self.config = configparser.ConfigParser()
        self.config.read_file(open(configFile))
    
    def readConfig(self, section, conf):
        try:
            return self.config.get(section, conf)
        except configparser.NoOptionError:
            return None
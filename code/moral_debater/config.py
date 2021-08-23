import configparser
from importlib_resources import files

class Config:
  __conf = None

  @staticmethod
  def config():
    if Config.__conf is None:  # Read only once, lazy.
      Config.__conf = configparser.ConfigParser()
      Config.__conf.read(files('moral_debater.resources').joinpath('config.ini'))
    return Config.__conf
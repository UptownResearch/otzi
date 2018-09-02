import importlib
import os
import sys
import json
import os.path


class ModifiableSettings:
    # Here will be the instance stored.
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if ModifiableSettings.__instance == None:
            ModifiableSettings()
        return ModifiableSettings.__instance 

    def __init__(self):
        """ Virtually private constructor. """
        if ModifiableSettings.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            ModifiableSettings.__instance = self
        print("ModifiableSetting Loading...")
        path = os.path.abspath(__file__)
        dir_path = os.path.dirname(path)
        settings_file_location = os.path.join(dir_path , 'settings.json')
        settings = {}
        if os.path.exists(settings_file_location):
            with open(settings_file_location, 'r') as settings_file:
                settings = json.load(settings_file)
        self.__dict__ = settings

    def reload(self):
        path = os.path.abspath(__file__)
        dir_path = os.path.dirname(path)
        settings_file_location = os.path.join(dir_path , 'settings.json')
        settings = {}
        if os.path.exists(settings_file_location):
            with open(settings_file_location, 'r') as settings_file:
                settings = json.load(settings_file)
        self.__dict__ = settings
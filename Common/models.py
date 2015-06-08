__author__ = 'Saurabh'

class IncompleteDataException(Exception):
    def __init__(self, message):
        self.value = message
    def __str__(self):
        return repr('Missing '+self.value)

class DuplicateDataException(Exception):
    def __init__(self, message):
        self.value = message
    def __str__(self):
        return repr('Duplicate '+self.value)

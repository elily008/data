
#from _pyio import __metaclass__
from abc import ABC, ABCMeta, abstractmethod
#from exceptions import Exception


# An Experiment must extend this class.
class Experiment(ABC):

    # Implementing this function allows to define how an experiment
    # has to be invoked.
    @abstractmethod
    def run(self, *args):
        pass

# Factory for Experiment.
# Every Experiment should define its own factory method (and class).
class ExperimentFactory(ABC):

    @abstractmethod
    def build(self, *args):
        pass

class ExperimentOutput(ABC):

    @abstractmethod
    def getRequestedTxRate(self):
        pass

    @abstractmethod
    def getAverageDR(self):
        pass

    @abstractmethod
    def getStdDR(self):
        pass

    @abstractmethod
    def toString(self):
        pass

class ExperimentException(Exception):
    
    def __init__(self, message):
        super(Exception, self).__init__(message)

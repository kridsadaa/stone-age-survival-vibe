from abc import ABC, abstractmethod

class System(ABC):
    """
    Abstract Base Class for all systems.
    Systems contain logic and mutate the WorldState.
    """
    @abstractmethod
    def update(self, state):
        """
        Executes one tick of logic.
        :param state: The shared WorldState object
        """
        pass

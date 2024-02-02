"""19.io class & function for event input."""
# Standard libraries
from abc import ABCMeta, abstractmethod
from typing import Generic

# Custom libraries
from ...colorized import ColoredOutput, bold, green
from ...skiboard import Event, RawInput, get_event
from ._classes import VALUE, Representation

__all__: list[str] = ['BaseInputEvent', 'InputEvent']
__all__ += ['input_event']


class BaseInputEvent(Generic[VALUE], metaclass=ABCMeta):
    """Base class for input events."""

    def __init__(
        self, prompt: object, *, representation: type[str] = Representation
    ) -> None:
        self.representation: type[str] = representation
        self.prompt:         str = representation(prompt)

    def display(self) -> None:
        """Display information."""
        print(green('?'), bold(self.get_prompt()), end=' ', flush=True)

    def get_prompt(self) -> str:
        """Get prompt for user."""
        return self.prompt

    @RawInput()
    @ColoredOutput()
    @abstractmethod
    def get_value(self) -> VALUE:
        """Get value from user."""


class InputEvent(BaseInputEvent[Event]):
    """Class for input events."""

    @RawInput()
    @ColoredOutput()
    def get_value(self) -> Event:
        self.display()
        event: Event = get_event()
        while not event.ispressed():
            event = get_event()

        print()
        return event


def input_event(
    prompt: object, *, representation: type[str] = Representation
) -> Event:
    """Read event from console input."""
    return InputEvent(prompt, representation=representation).get_value()
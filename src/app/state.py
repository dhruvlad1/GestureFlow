"""Application lifecycle states and their valid transitions."""

from enum import Enum


class ApplicationState(Enum):
    """Authoritative lifecycle states for the camera pipeline."""

    INACTIVE = "Inactive"
    STARTING = "Starting"
    ACTIVE = "Active"
    PAUSED = "Paused"
    STOPPING = "Stopping"
    ERROR = "Error"


VALID_TRANSITIONS = {
    ApplicationState.INACTIVE: {
        ApplicationState.STARTING,
    },
    ApplicationState.STARTING: {
        ApplicationState.ACTIVE,
        ApplicationState.ERROR,
        ApplicationState.INACTIVE,
    },
    ApplicationState.ACTIVE: {
        ApplicationState.PAUSED,
        ApplicationState.STOPPING,
        ApplicationState.ERROR,
    },
    ApplicationState.PAUSED: {
        ApplicationState.ACTIVE,
        ApplicationState.STOPPING,
        ApplicationState.ERROR,
    },
    ApplicationState.STOPPING: {
        ApplicationState.INACTIVE,
        ApplicationState.ERROR,
    },
    ApplicationState.ERROR: {
        ApplicationState.INACTIVE,
        ApplicationState.STARTING,
    },
}


def can_transition(current, target):
    """Return whether the requested lifecycle transition is valid."""

    return target in VALID_TRANSITIONS.get(current, set())
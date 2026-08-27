"""
HK NPU STUDIO

Batch State Machine

Created by Holger Kreuzhofen
Phoenix Engine Layer
"""

from engine.batch_state import BatchState


class BatchStateMachine:
    """Central state machine for batch lifecycle handling."""

    def __init__(self):
        self.state = BatchState.IDLE
        self.last_error = None

    def get_state(self):
        return self.state.value

    def get_last_error(self):
        return self.last_error

    def reset(self):
        self.state = BatchState.IDLE
        self.last_error = None

    def set_ready(self):
        self._transition_to(BatchState.READY)

    def start(self):
        self.last_error = None
        self._transition_to(BatchState.RUNNING)

    def request_stop(self):
        self._transition_to(BatchState.STOPPING)

    def finish(self):
        self.last_error = None
        self._transition_to(BatchState.FINISHED)

    def fail(self, error):
        self.last_error = str(error)
        self.state = BatchState.ERROR

    def can_start(self):
        return self.state in (
            BatchState.IDLE,
            BatchState.READY,
            BatchState.FINISHED,
            BatchState.ERROR,
        )

    def can_stop(self):
        return self.state == BatchState.RUNNING

    def is_running(self):
        return self.state == BatchState.RUNNING

    def is_stopping(self):
        return self.state == BatchState.STOPPING

    def is_busy(self):
        return self.state in (
            BatchState.RUNNING,
            BatchState.STOPPING,
        )

    def _transition_to(self, new_state):
        if not self._is_valid_transition(new_state):
            raise RuntimeError(
                f"Invalid batch state transition: "
                f"{self.state.value} -> {new_state.value}"
            )

        self.state = new_state

    def _is_valid_transition(self, new_state):
        allowed = {
            BatchState.IDLE: {
                BatchState.READY,
                BatchState.RUNNING,
                BatchState.ERROR,
            },
            BatchState.READY: {
                BatchState.RUNNING,
                BatchState.IDLE,
                BatchState.ERROR,
            },
            BatchState.RUNNING: {
                BatchState.STOPPING,
                BatchState.FINISHED,
                BatchState.ERROR,
            },
            BatchState.STOPPING: {
                BatchState.FINISHED,
                BatchState.ERROR,
                BatchState.IDLE,
            },
            BatchState.FINISHED: {
                BatchState.IDLE,
                BatchState.READY,
                BatchState.RUNNING,
                BatchState.ERROR,
            },
            BatchState.ERROR: {
                BatchState.IDLE,
                BatchState.READY,
                BatchState.RUNNING,
            },
        }

        return new_state in allowed[self.state]
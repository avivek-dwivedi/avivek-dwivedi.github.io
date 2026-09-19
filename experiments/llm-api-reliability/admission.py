"""Token-aware admission controller.

Reference lab implementation.
"""
from dataclasses import dataclass


@dataclass
class Reservation:
    request_tokens: int
    reserved_tokens: int


class AdmissionController:
    def __init__(self, budgets):
        self.budgets = budgets
        self.last_reason: str = ""

    def reserve(self, input_tokens: int, max_output: int) -> Reservation | None:
        reserved = input_tokens + max_output

        if not self.budgets.can_take_rpm(1):
            self.last_reason = "rpm"
            return None

        if not self.budgets.can_take_tpm(reserved):
            self.last_reason = "tpm"
            return None

        if not self.budgets.concurrency_available():
            self.last_reason = "concurrency"
            return None

        self.budgets.take_rpm(1)
        self.budgets.take_tpm(reserved)
        self.last_reason = ""
        return Reservation(request_tokens=input_tokens, reserved_tokens=reserved)
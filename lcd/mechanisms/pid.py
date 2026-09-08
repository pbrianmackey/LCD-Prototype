"""Generic PID controller (donor mechanism: control_theory_pid)."""


class PIDController:
    def __init__(self, kp, ki, kd, setpoint, output_limits=(None, None), integral_limits=(None, None)):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.setpoint = setpoint
        self.output_limits = output_limits
        self.integral_limits = integral_limits
        self._integral = 0.0
        self._prev_error = None

    def step(self, measured_value, dt=1.0):
        error = self.setpoint - measured_value
        self._integral += error * dt
        lo_i, hi_i = self.integral_limits
        if lo_i is not None:
            self._integral = max(lo_i, self._integral)
        if hi_i is not None:
            self._integral = min(hi_i, self._integral)
        derivative = 0.0 if self._prev_error is None else (error - self._prev_error) / dt
        self._prev_error = error
        output = self.kp * error + self.ki * self._integral + self.kd * derivative
        lo, hi = self.output_limits
        if lo is not None:
            output = max(lo, output)
        if hi is not None:
            output = min(hi, output)
        return output

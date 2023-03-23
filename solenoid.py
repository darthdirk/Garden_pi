import logging

logger = logging.getLogger(__name__)

# solenoid rate in ms/s (4.3 L/min)
_solenoid_RATE_MS_PER_SEC = 4300.0 / 60.0

# Default amount of time to add to the plant (in ms) when solenoid manager detects
# low soil moisture.
DEFAULT_solenoid_AMOUNT = 200


class solenoid(object):
    """Wrapper for a time solenoid."""

    def __init__(self, pi_io, clock, solenoid_pin):
        """Creates a new solenoid wrapper.
        Args:
            pi_io: Raspberry Pi I/O interface.
            clock: A clock interface.
            solenoid_pin: Raspberry Pi pin to which the solenoid is connected.
        """
        self._pi_io = pi_io
        self._clock = clock
        self._solenoid_pin = solenoid_pin

    def solenoid_time(self, amount_ms):
        """solenoids the specified amount of time.
        Args:
            amount_ms: Amount of time to solenoid (in ms).
        Raises:
            ValueError: The amount of time to be solenoided is invalid.
        """
        if amount_ms == 0:
            return
        elif amount_ms < 0:
            raise ValueError('Cannot solenoid a negative amount of time')
        else:
            logger.info('turning solenoid on (with GPIO pin %d)', self._solenoid_pin)
            self._pi_io.turn_pin_on(self._solenoid_pin)

            wait_time_seconds = amount_ms / _solenoid_RATE_ms
            self._clock.wait(wait_time_seconds)

            logger.info('turning solenoid off (with GPIO pin %d)', self._solenoid_pin)
            self._pi_io.turn_pin_off(self._solenoid_pin)
            logger.info('solenoided %.f ms of time', amount_ms)

        return


class solenoidManager(object):
    """solenoid Manager manages the time solenoid."""

    def __init__(self, solenoid, solenoid_scheduler, moisture_threshold, solenoid_amount,
                 timer):
        """Creates a solenoidManager object, which manages a time solenoid.
        Args:
            solenoid: A solenoid instance, which supports time solenoiding.
            solenoid_scheduler: A solenoid scheduler instance that controls the time
                periods in which the solenoid can be run.
            moisture_threshold: Soil moisture threshold. If soil moisture is
                below this value, manager solenoids time on solenoid_if_needed calls.
            solenoid_amount: Amount (in ms) to solenoid every time the time solenoid runs.
            timer: A timer that counts down until the next forced solenoid. When
                this timer expires, the solenoid manager runs the solenoid once,
                regardless of the moisture level.
        """
        self._solenoid = solenoid
        self._solenoid_scheduler = solenoid_scheduler
        self._moisture_threshold = moisture_threshold
        self._solenoid_amount = solenoid_amount
        self._timer = timer

    def solenoid_if_needed(self, moisture):
        """Run the time solenoid if there is a need to run it.
        Args:
            moisture: Soil moisture level
        Returns:
            The amount of time solenoided, in ms.
        """
        if self._should_solenoid(moisture):
            self._solenoid.solenoid_time(self._solenoid_amount)
            self._timer.reset()
            return self._solenoid_amount

        return 0

    def _should_solenoid(self, moisture):
        """Returns True if the solenoid should be run."""
        if not self._solenoid_scheduler.is_running_solenoid_allowed():
            return False
        return (moisture < self._moisture_threshold) or self._timer.expired()


class solenoidScheduler(object):
    """Controls when the solenoid is allowed to run."""

    def __init__(self, local_clock, sleep_windows):
        """Creates new solenoidScheduler instance.
        Args:
            local_clock: A local clock interface
            sleep_windows: A list of 2-tuples, each representing a sleep window.
                Tuple items are datetime.time objects.
        """
        self._local_clock = local_clock
        self._sleep_windows = sleep_windows

    def is_running_solenoid_allowed(self):
        """Returns True if OK to run solenoid, otherwise False.
        solenoid is not allowed to run from the start of a sleep window (inclusive)
        to the end of a sleep window (exclusive).
        """
        current_time = self._local_clock.now().time()

        for sleep_time, wake_time in self._sleep_windows:
            # Check if sleep window wraps midnight.
            if wake_time < sleep_time:
                if current_time >= sleep_time or current_time < wake_time:
                    return False
            else:
                if sleep_time <= current_time < wake_time:
                    return False

        return True
import threading

import krpc
import time

ALL_FUELS = ('LiquidFuel', 'SolidFuel')


class Thread(threading.Thread):
    def __init__(self, name, vessel):
        self._stopevent = threading.Event()
        self._sleepperiod = 1
        self.vessel = vessel
        threading.Thread.__init__(self, name=name)

    def run(self):
        print("Starting " + self.name)
        while not self._stopevent.is_set():
            if not auto_staging(self.vessel):
                break
        print("Stopped " + self.name)

    def stop(self, timeout=None):
        self._stopevent.set()
        threading.Thread.join(self, timeout)


def auto_staging(vessel):  # todo support for asparagus staging
    """
    Activate next stage when current stage is empty
    :param vessel: takes vessel as a parameter

    """
    for part in vessel.parts.in_stage(vessel.control.current_stage - 1):  # if the next stage has a fairing
        if part.fairing:  # todo also check if there is a parachute
            return False  # todo I want it to stage the fairing automatically also, if possible

    res = get_resources(vessel)
    interstage = True

    for fuelType in ALL_FUELS:
        if out_of_specific_fuel(res, fuelType):
            stage(vessel)
            continue
        if res.has_resource(fuelType):
            interstage = False

    if interstage:
        stage(vessel)
    time.sleep(2)
    return True


def get_resources(vessel):
    """
    Gets the resources of the vessel in decouple stage
    :param vessel:
    :return: the resources
    """
    return vessel.resources_in_decouple_stage(vessel.control.current_stage - 1, cumulative=False)


def out_of_specific_fuel(resource, fueltype):
    """
    Checks whether the vessel has capacity for a fueltype, but no fuel
    :param resource:
    :param fueltype:
    :return: boolean
    """
    return resource.max(fueltype) > 0 and resource.amount(fueltype) == 0


def stage(vessel):
    """
    Stage the vessel
    :param vessel:
    :return:
    """
    vessel.control.activate_next_stage()

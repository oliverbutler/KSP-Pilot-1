import time
import krpc

from pilot import plotting
from pilot import auto_stage
from pilot import node

ASCENT_MAX_WARP = 1
MAX_PHYSICS_WARP = 3


class MissionParameters(object):  # todo make actually adjustable
    def __init__(self,
                 orbit_target=80000,
                 gravity_turn_start=3000,
                 gravity_turn_end=50000,
                 inclination=0,
                 force_roll=False,
                 roll=90,
                 deploy_solar=False,
                 max_q=30000,  # todo implement max_q
                 warp_on_ascent=False):  # todo FIX auto-stage when physics warping
        self.orbit_target = orbit_target
        self.gravity_turn_start = gravity_turn_start
        self.gravity_turn_end = gravity_turn_end
        self.inclination = inclination
        self.force_roll = force_roll
        self.roll = roll
        self.deploy_solar = deploy_solar
        self.max_q = max_q
        self.warp_on_ascent = warp_on_ascent


class Launch:  # todo fix random nosedive on launch, randomly sometimes happens
    def __init__(self):
        self.launch_params = MissionParameters()
        self.conn = krpc.connect(name='PyPilot', address='10.13.201.84', rpc_port=50000, stream_port=50001)
        self.vessel = self.conn.space_center.active_vessel

        self.ut = self.conn.add_stream(getattr, self.conn.space_center, 'ut')
        self.altitude = self.conn.add_stream(getattr, self.vessel.flight(), 'mean_altitude')
        self.apoapsis = self.conn.add_stream(getattr, self.vessel.orbit, 'apoapsis_altitude')

        self.plot = plotting.Thread("Plot", self.vessel)
        self.auto_stage = auto_stage.Thread("Auto Stage", self.vessel)

    def gravity_turn(self):
        heading = 90

        for i in range(3, 0, -1):
            print("Launch in T-" + str(i))
            time.sleep(1)
        print("Launch!")

        self.vessel.control.sas = False
        self.vessel.control.rcs = False
        self.vessel.auto_pilot.engage()
        self.vessel.auto_pilot.target_pitch_and_heading(0, 90)
        self.vessel.control.throttle = 1

        if self.launch_params.force_roll:
            self.vessel.auto_pilot.target_roll = self.launch_params.roll

        # self.auto_stage.start()
        self.plot.start()

        if self.launch_params.warp_on_ascent:
            self.conn.space_center.physics_warp_factor = ASCENT_MAX_WARP

        print("Gravity turn...")
        throttle = 1

        while self.apoapsis() < self.launch_params.orbit_target + 1000:  # 1km overshoot to account for aerodynamic drag
            progress = (self.altitude() - self.launch_params.gravity_turn_start) / (
                    self.launch_params.gravity_turn_end - self.launch_params.gravity_turn_start)
            pitch = min(90 - (-90 * progress * (progress - 2)), 90)
            self.vessel.auto_pilot.target_pitch_and_heading(pitch, heading)
            time.sleep(0.05)

        self.vessel.control.throttle = 0

        while self.altitude() < self.vessel.orbit.body.atmosphere_depth - 2000:
            self.conn.space_center.physics_warp_factor = MAX_PHYSICS_WARP
            time.sleep(0.5)

        # todo fix the roll when out of warp
        self.conn.space_center.physics_warp_factor = 0

        if has_fairing(self.vessel):  # todo maybe integrate into autostage?
            jettison_fairing(self.vessel)

        self.plot.stop()

    def circularize(self):
        print("Node...")
        node.circularize_at_apoapsis(self.conn, self.vessel)
        node.execute(self.conn, self.vessel)


def has_fairing(vessel):  # todo add these functions to new "Functions" .py
    for part in vessel.parts.all:
        if part.fairing:
            return True
    return False


def jettison_fairing(vessel):
    for part in vessel.parts.all:
        if part.fairing:
            part.fairing.jettison()


if __name__ == '__main__':  # todo implement gui
    launch = Launch()
    launch.gravity_turn()

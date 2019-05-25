import time
import krpc

from pilot import plotting
from pilot import node

ASCENT_MAX_WARP = 1
MAX_PHYSICS_WARP = 3


class MissionParameters(object):
    def __init__(self,
                 orbit_target=80000,
                 initial_angle=10,
                 initial_target_speed=1450,
                 initial_target_height=21000,
                 closed_cycle_start=25000,
                 closed_cycle_angle=7,
                 closed_cycle_level=31000,
                 level_height=34000):
        self.orbit_target = orbit_target
        self.initial_angle = initial_angle
        self.initial_target_speed = initial_target_speed
        self.initial_target_height = initial_target_height
        self.closed_cycle_start = closed_cycle_start
        self.closed_cycle_angle = closed_cycle_angle
        self.closed_cycle_level = closed_cycle_level
        self.level_height = level_height


class Launch:
    def __init__(self):
        self.params = MissionParameters()
        self.conn = krpc.connect(name='SSTO', address='86.171.134.103', rpc_port=50000, stream_port=50001)
        self.vessel = self.conn.space_center.active_vessel

        self.altitude = self.conn.add_stream(getattr, self.vessel.flight(), 'mean_altitude')

        self.plot = plotting.Thread("Plot", self.vessel)
        self.plot.start()

        self.vessel.control.sas = False
        self.vessel.control.rcs = False
        self.vessel.auto_pilot.engage()
        self.vessel.auto_pilot.target_pitch_and_heading(self.params.initial_angle, 90)
        self.vessel.auto_pilot.target_roll = 0
        self.vessel.control.throttle = 1
        self.vessel.control.activate_next_stage()
        print("Launching")
        while True:
            if self.altitude() > 100:
                self.vessel.control.gear = False
                break
        while True:
            if self.altitude() > self.params.initial_target_height:
                print("Closed cycle mode")
                self.vessel.control.toggle_action_group(3)
                break

        while True:
            if self.vessel.orbit.apoapsis_altitude > self.params.orbit_target * 1.02:
                print("Target reached")
                self.vessel.control.throttle = 0
                break

        while True:
            if self.altitude() > 70000:
                print("Make node")
                node.circularize_at_apoapsis(self.conn, self.vessel)
                self.vessel.control.rcs = True
                node.execute(self.conn, self.vessel)
                break

        self.plot.stop()


if __name__ == '__main__':
    launch = Launch()

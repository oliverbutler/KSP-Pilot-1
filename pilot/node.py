import time
import math


def circularize_at_apoapsis(conn, vessel):  # todo node isn't been made evenly, debug this.
    make_node(conn, vessel, vessel.orbit.apoapsis_altitude, vessel.orbit.apoapsis_altitude,
              vessel.orbit.time_to_apoapsis)


def make_node(conn, vessel, node_altitude, target_altitude, node_ut):
    orbit = vessel.orbit
    mu = orbit.body.gravitational_parameter

    r1 = node_altitude + orbit.body.equatorial_radius
    a1 = orbit.semi_major_axis
    v1 = math.sqrt(mu * ((2 / r1) - (1 / a1)))

    r2 = node_altitude + orbit.body.equatorial_radius
    a2 = (node_altitude + target_altitude + 2 * orbit.body.equatorial_radius) / 2
    v2 = math.sqrt(mu * ((2 / r2) - (1 / a2)))

    delta_v = v2 - v1
    vessel.control.add_node(conn.space_center.ut + node_ut, delta_v, 0, 0)


def execute(conn, vessel):
    ap = vessel.auto_pilot
    node = vessel.control.nodes[0]
    ap.disengage()
    ap.sas = False
    ap.engage()
    ap.reference_frame = vessel.orbital_reference_frame
    ap.target_direction = node.burn_vector(vessel.orbital_reference_frame)
    ap.wait()  # todo instead of wait, keep adjusting until error is < 2%
    ap.disengage()

    orig_dv = node.remaining_delta_v
    prev_dv = orig_dv

    delta_v = node.delta_v
    mi = vessel.mass
    isp = specific_impulse(vessel)
    g0 = vessel.orbit.body.surface_gravity
    t = vessel.available_thrust
    delta_t = g0 * mi * isp * ((1 - math.exp(-delta_v / (g0 * isp))) / t)
    start_time = node.ut - 0.5 * delta_t

    conn.space_center.warp_to(start_time - 5, 100000, 3)
    ap.engage()
    ap.target_direction = node.burn_vector(vessel.orbital_reference_frame)
    time.sleep(5)

    while True:
        ap.target_direction = node.burn_vector(vessel.orbital_reference_frame)

        if node.remaining_delta_v > prev_dv and prev_dv < orig_dv * 0.9:
            vessel.control.throttle = 0
            print("Node execution finished")
            ap.disengage()
            node.remove()
            break
        elif node.remaining_delta_v < 0.2:
            vessel.control.throttle = 0.001
        elif node.remaining_delta_v < 2:
            vessel.control.throttle = 0.005
        elif node.remaining_delta_v < 5:
            vessel.control.throttle = 0.01
        elif node.remaining_delta_v < 10:
            vessel.control.throttle = 0.1
        elif node.remaining_delta_v < 25:
            vessel.control.throttle = 0.2
        else:
            vessel.control.throttle = 1

        prev_dv = node.remaining_delta_v

        time.sleep(0.05)


def specific_impulse(vessel):
    active_engines = [e for e in vessel.parts.engines if e.active and e.has_fuel]
    thrust = sum(engine.available_thrust for engine in active_engines)
    fuel_consumption = sum(engine.available_thrust / engine.specific_impulse
                           for engine in active_engines)
    return thrust / fuel_consumption

# todo more node options
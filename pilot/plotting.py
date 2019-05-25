import threading
import time

import matplotlib.pyplot as plt
# import numpy as np
#
# import plotly.plotly as py

x_time = []
altitude = []
speed = []
g_force = []
dynamic_pressure = []



class Thread(threading.Thread):
    def __init__(self, name, vessel):
        self._stopevent = threading.Event()
        self._sleepperiod = 1
        self.vessel = vessel
        threading.Thread.__init__(self, name=name)

    def run(self):  # todo all plots on one screen, live plots if possible
        print("Starting " + self.name)
        while not self._stopevent.is_set():
            plot_data(self.vessel)
        plt.plot(x_time, altitude)
        plt.title('Altitude')
        plt.show()
        plt.plot(x_time, speed)
        plt.title('Speed')
        plt.show()
        plt.plot(x_time, g_force)
        plt.title('G Force')
        plt.show()
        plt.plot(x_time, dynamic_pressure)
        plt.title('Dynamic Pressure')
        plt.show()
        print("Stopped " + self.name)

    def stop(self, timeout=None):
        self._stopevent.set()
        threading.Thread.join(self, timeout)


def plot_data(vessel):
    x_time.append(vessel.met)
    altitude.append(vessel.flight().mean_altitude)
    speed.append(vessel.flight(vessel.orbit.body.reference_frame).speed)
    g_force.append(vessel.flight().g_force)
    dynamic_pressure.append(vessel.flight().dynamic_pressure)
    time.sleep(0.5)


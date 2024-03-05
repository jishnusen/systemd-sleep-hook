import dbus
from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop

import logging
import argparse
import os
import fcntl

PROG_NAME = "systemd-sleep-hook"
LOGIND_SERVICE = "org.freedesktop.login1"
LOGIND_INTERFACE = LOGIND_SERVICE + ".Manager"
LOGIND_PATH = "/org/freedesktop/login1"

class SystemdSleepHook:
    def __init__(self, sleep, resume):
        self.sleep = sleep
        self.resume = resume

    def init_listeners(self):
        bus = dbus.SystemBus()
        bus.add_signal_receiver(lambda active: self.wait_for_sleep(active),
                                signal_name="PrepareForSleep",
                                dbus_interface=LOGIND_INTERFACE)


    def start_inhibit(self):
        if self.sleep is None:
            return

        bus = dbus.SystemBus()
        login = bus.get_object(LOGIND_SERVICE, LOGIND_PATH)
        pm = dbus.Interface(login, LOGIND_INTERFACE)
        self.sleep_lock = pm.Inhibit("sleep", PROG_NAME, f"running {self.sleep} as hook before sleep", "block").take()
        flags = fcntl.fcntl(self.sleep_lock, fcntl.F_GETFD)
        fcntl.fcntl(self.sleep_lock, fcntl.F_SETFD, flags | fcntl.FD_CLOEXEC)
        logging.info("grabbed inhibit")

    def wait_for_sleep(self, active):
        if active:
            logging.info("received PrepareForSleep; releasing inhibitor")
            os.system(self.sleep)
            os.close(self.sleep_lock)
            logging.info("closed sleep inhibitor")
        else:
            logging.info("received PrepareForSleep; resuming inhibitor")
            self.start_inhibit()
            if self.resume:
                os.system(self.resume)


def main():
    parser = argparse.ArgumentParser(
            prog="systemd-sleep-hook",
            description="run command on systemd sleep/resume")
    parser.add_argument('-s', '--sleep')
    parser.add_argument('-r', '--resume')

    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)

    DBusGMainLoop(set_as_default=True)
    sleep_hook = SystemdSleepHook(args.sleep, args.resume)

    sleep_hook.init_listeners()
    sleep_hook.start_inhibit()

    loop = GLib.MainLoop()
    loop.run()

if __name__ == "__main__":
    main()

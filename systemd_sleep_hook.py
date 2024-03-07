import dbus
from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop

import logging
import argparse
import os

PROG_NAME = "systemd-sleep-hook"
LOGIND_SERVICE = "org.freedesktop.login1"
LOGIND_INTERFACE = LOGIND_SERVICE + ".Manager"
LOGIND_PATH = "/org/freedesktop/login1"

class SystemdSleepHook:
    def __init__(self, sleep, resume):
        self.sleep = sleep
        self.resume = resume
        self.sleep_lock = -1

    def init_listeners(self):
        bus = dbus.SystemBus()
        bus.add_signal_receiver(lambda active: self.wait_for_sleep(active),
                                signal_name="PrepareForSleep",
                                dbus_interface=LOGIND_INTERFACE)


    def start_inhibit(self):
        if self.sleep is None:
            return
        if self.sleep_lock > 0:
            # shouldn't happen, but just in case we do _not_ want to have
            # multiple fd's open since that means we are dangling locks!
            return

        bus = dbus.SystemBus()

        login = bus.get_object(LOGIND_SERVICE, LOGIND_PATH)
        pm = dbus.Interface(login, LOGIND_INTERFACE)
        self.sleep_lock = pm.Inhibit("sleep", PROG_NAME, f"running {self.sleep} as hook before sleep", "block").take()
        logging.info("opened sleep inhibitor")

    def wait_for_sleep(self, active):
        if active:
            logging.info("received PrepareForSleep; closing sleep inhibitor")
            if os.system(self.sleep) != 0:
                logging.warn(f"sleep command {self.sleep} returned non-zero exit code")
            os.close(self.sleep_lock)
            self.sleep_lock = -1
            logging.info("closed sleep inhibitor")
        else:
            logging.info("received PrepareForSleep; opening sleep inhibitor")
            self.start_inhibit()
            if self.resume is None:
                return
            if os.system(self.resume) != 0:
                logging.warn(f"resume command {self.resume} returned non-zero exit code")


def main():
    parser = argparse.ArgumentParser(
            prog=PROG_NAME,
            description="run command on systemd sleep/resume")
    parser.add_argument('-s', '--sleep', metavar="SLEEP_COMMAND", help="command to run before sleep")
    parser.add_argument('-r', '--resume', metavar="RESUME_COMMAND", help="command to run on resume")

    args = parser.parse_args()
    logging.basicConfig(
        level=os.environ.get('LOGLEVEL', 'INFO').upper()
    )

    DBusGMainLoop(set_as_default=True)
    sleep_hook = SystemdSleepHook(args.sleep, args.resume)

    sleep_hook.init_listeners()
    sleep_hook.start_inhibit()

    loop = GLib.MainLoop()
    loop.run()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import subprocess
import re
import time
import select
import typing
from typing import List, Any
Process = Any


timeout_s: int = 5 * 60    # Timeout in lockscreen in seconds, i.e. when to turn of screen
poll_period_ms: int = 1    # How quickly to read lines from stdout in ms
stream_timeout_s: int = 1  # How quickly to timeout stdout in seconds (to be able to check the time)
initial_sleep_s: int = 1   # Initially sleep for this duration in seconds


def check_system() -> bool:
    """
    Check if the system has all dependencies
    :return: True if xinput, xset and pgrep can be found
    """
    ret = True
    if ("XDG_CURRENT_DESKTOP=KDE" not in subprocess.check_output(["env"]).decode("utf-8")):
        ret = False
        print("You're not using KDE!")
    for app in ["xinput", "xset", "pgrep"]:
        if (subprocess.run(["which", app], capture_output=True).returncode != 0):
            ret = False
            print("Application \"{}\" is missing!".format(app))
    return ret


def get_device_ids() -> List[int]:
    """
    Get the device IDs of all connected slave input devices via xinput
    return: The list of device IDs as int
    """
    xinput_output = subprocess.check_output(["xinput", "--list", "--short"]) \
                              .decode("utf-8").split("\n")
    r = re.compile(r"id=(.*)\s*\[slave.*\]")
    device_ids = []
    for line in xinput_output:
        if m := r.search(line):
            device_id = int(m.group(1))
            device_ids.append(device_id)
    print("Found device IDs {}".format(device_ids))
    return device_ids


def spawn_xinput_subprocesses(device_ids: List[int]) -> List[Process]:
    """
    Spawn the xinput subprocesses that monitor each input device
    :param device_ids: The device IDs to monitor
    :return: The list of spawned xinput processes
    """
    subprocesses: List[Process] = [None for i in device_ids]
    print("Spawning {} xinput subprocesses…".format(len(subprocesses)))
    for i in range(len(subprocesses)):
        id = device_ids[i]
        subprocesses[i] = subprocess.Popen(["xinput", "--test", str(id)],
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
    return subprocesses


def is_screen_locked() -> bool:
    """
    Check if the screen is locked by checking if kscreenlocker is running
    :return: True if kscreenlocker is running
    """
    return (subprocess.run(["pgrep", "kscreenlocker"], capture_output=True).returncode == 0)


def turn_screen_off() -> None:
    """
    Turn the screen off via xset
    """
    print("Turning screen off…")
    subprocess.run(["xset", "dpms", "force", "off"])


def poll_for_input(subprocesses: List[Process]) -> None:
    """
    Measure the time since the last input on the system.
    This is done by merging all output streams of the processes into one stream
    with a timeout. If this timeout passes, no input was in this period.
    Turn off the screen if the time > timeout_s.
    Exit and kill all subprocesses if the screen is not locked.
    Also exit if all subproccesses terminate for some reason.
    :param subprocesses: The list of xinput subproccesses to monitor
    """
    time_of_last_input = time.time()
    streams = [p.stdout for p in subprocesses]
    while True:
        if not is_screen_locked():
            print("Screen is not locked. Exiting…")
            for p in subprocesses:
                if p != None:
                    p.kill()
            break
        now = time.time()
        time_since_last_input = now - time_of_last_input
        if time_since_last_input > timeout_s:
            print("Time since last input: {} s".format(time_since_last_input))
            turn_screen_off()
        rstreams, _, _ = select.select(streams, [], [], stream_timeout_s)
        for stream in rstreams:
            stream.readline()
            time_of_last_input = time.time()
        if all(p.poll() is not None for p in subprocesses):
            print("Error: All subprocesses terminated! Exiting…")
            break
        time.sleep(poll_period_ms / 1000)


def main() -> None:
    if check_system():
        time.sleep(initial_sleep_s)
        device_ids = get_device_ids()
        subprocesses = spawn_xinput_subprocesses(device_ids)
        poll_for_input(subprocesses)


if __name__ == '__main__':
    main()

# kscreenlocker-auto-screen-off

This is a small Python script that I wrote because I was very annoyed with the
fact that, at the time of writing, the KDE lockscreen doesn't support shutting
off the screen automatically after `n` minutes of time have passed in which
no input (e.g. keyboard / mouse) was detected (like how you would expect a
lockscreen to work).

There is a [workaround](https://askubuntu.com/a/351713) that makes the
screen immediately be turned off when the screen is locked. This is not
ideal because if I wake up the screen and *don't unlock* my computer and walk
away again, the screen will not be locked again, and of course the screen is
also immediately turned off which I do not want.

However, I'm using a part of the answer myself.

## How It Works

The script needs `xinput`, `xset`, `pgrep` and `kscreenlocker` to work.

If you lock your screen and don't touch your mouse and keyboard for 5 minutes,
the screen will automatically be turned off. If you move your mouse, your
screen should wake up and you should see your lockscreen. If you repeat this
and wait another 5 minutes, the screen will be turned off again, until you
unlock your session.

To do this, the script will…

* acquire a list of all slave input devices by running `xinput --list --short`,
* parse out the relevant device IDs,
* for each ID, run `xinput --test $id` as a subprocess, and
* merge all their stdout streams to one stream that has a timeout of one second.
* If this timeout passes, this means, that no `xinput` instance has produced
  any output in the last second, i.e. no input device has been used.
* If however input is done, this is immediately detected and we update a timepoint
  variable.
* We measure the time since the last input.
* If this time is larger than the configured timeout, we lock the screen using
  `xset dpms force off`.
* If the screen is not locked anymore, i.e. `kscreenlocker` is not running,
  the script kills all subprocesses and exits.

## How To Use

Clone the repo whereever you want:
```bash
$ git clone https://github.com/felsenhower/kscreenlocker-auto-screen-off
```

Run the script normally if everything works normally.
Output should look something like this:
```bash
$ cd kscreenlocker-auto-screen-off
$ python3 ./auto-screen-off.py
Found device IDs [4, 8, 9, 11, 5, 6, 7, 10, 12, 13, 14]
Spawning 11 xinput subprocesses…
Screen is not locked. Exiting…
```

Set the variable `timeout_s` in the script to your liking, default is 5 minutes.

Link the Lock screen to the script. Here is how to do it in KDE Plasma 5.20.4:

* Go to the System Settings
* Scroll down to "Personalisation" → "🔔 Notifications"
* Click on "Applications: ⚙️ Configure…" at the very bottom
* Scroll down to "System Services" → "🔒 Screen Saver"
* Click on "🗨️ Configure Events…"
* Select the "Screen locked" event at the top
* Activate the checkbox "☑ ⚙️ Run command"
* Enter `/usr/bin/python3 "/path/to/your/auto-screen-off.py"`
* Click "✔ OK"

# systemd sleep hook

a simple program to run a script before and after sleep. note that the locks are
blocking, so make sure your script finishes!

```
usage: systemd-sleep-hook [-h] [-s SLEEP] [-r RESUME]

run command on systemd sleep/resume

options:
  -h, --help            show this help message and exit
  -s SLEEP, --sleep SLEEP
  -r RESUME, --resume RESUME
```

## Installation
install with pipx is recommended
```
pipx install git+https://github.com/jishnusen/systemd-sleep-hook.git
```

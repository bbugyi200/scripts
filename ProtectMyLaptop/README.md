# Why?
We shouldn't leave our personal belongings in public places unattended. You know it, I know it, and the would-be thieves know it. But most of us do it anyway. Am I really going to pack up my laptop, mouse and mousepad, charger, notebook, pencil and eraser, calculator, and the rest of my belongings every time I need to take a trip to the bathroom? Probably not. So I leave my things where they sit and risk having them stolen. My goal in writing ProtectMyLaptop was to help make this risk a bit more manageable.

# What?

ore of a set of complementary scripts than a cohesive program in and of itself, ProtectMyLaptop uses [Twilio](https://www.twilio.com), [Motion](https://wiki.archlinux.org/index.php/Motion), [i3lock](https://i3wm.org/i3lock/), and [ACPID](https://wiki.archlinux.org/index.php/acpid) in order to provide the user with the following security features which are activated after using the `screenlock` script to lock your screen:

 Locks the screen (using a blurred screenshot of your desktop)
 Upon detecting motion on your laptops built-in webcam, ProtectMyLaptop snaps photos continuously until the motion stops. You should set the photos to be stored (specified with the `motion_root_dir` configuration option) on your Sync (or any other cloud account). This way, if someone does manage to steal your laptop, you can go to your Sync account to get a look at his/her face.
 In the event that your laptop lid is closed or the power button is pressed, ProtectMyLaptop uses Twilio to send a text message to your cell phone to alert you that your laptop is being stolen.

 Configuration

ProtectMyLaptop uses a configuration file which uses an ini like format and can either be stored at either `~/.PML.conf` or (preferably) `~/.config/PML.conf`. The following options are available:

``` ini
[Motion]
# 0 to disable motion from running or 1 to enable motion
motion_enabled=
# Delay (in seconds) before motion starts
motion_delay=
# jpeg files created by motion are stored in this directory
motion_root_dir=

[Twilio]
# 0 or 1. If enabled, it will text you when PML is activated
textme_at_startup=
# Twilio Account SID
account_sid=
# Twilio Auth Token
auth_token=
# Your phone number (prefaced with a +)
to=
# Twilio phone number (also prefaced with a +)
from_=
```

Before running `screenlock`, you should copy this format to one of the acceptable file paths mentioned above and fill in the options accordingly.

# Notes

* In order to get [Motion](https://wiki.archlinux.org/index.php/Motion) to behave as described in this document, you will have to change some of its default configurations. This can be done by making the appropriate alterations to the `/etc/motion/motion.conf` file.
* The `etc/acpi/handler.sh` script included in this repo is merely a demonstration. In order to be texted when your laptop power button is pressed and/or laptop lid is closed, you must copy the `button/power` and `button/lid` sections to your local `/etc/acpi/handler.sh` file, which should already exist if you have installed `acpi` to your machine. In the provided `etc/acpi/handler.sh` demo, make sure to replace `<username>` with your own Linux username.

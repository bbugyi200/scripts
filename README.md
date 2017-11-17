# Why?
We shouldn't leave our personal belongings in public places unattended. You know it, I know it, and the would-be thieves know it. But most of us do it anyway sometimes. Am I really going to pack up my laptop, mouse and mousepad, charger, notebook, pencil and eraser, calculator, and the rest of my belongings every time I need to take a trip to the bathroom? Probably not. So I leave my things where they sit and risk having them stolen. My goal in writing ProtectMyLaptop was to help make this risk a bit more manageable.

# What?

More of a set of complementary scripts than a cohesive program in and of itself, ProtectMyLaptop uses [Twilio](https://www.twilio.com), [Motion](https://wiki.archlinux.org/index.php/Motion), [i3lock](https://i3wm.org/i3lock/), and [ACPID](https://wiki.archlinux.org/index.php/acpid) in order to provide the user with the following security features which are activated after using the `screenlock.sh` script to lock your screen:

* Locks the screen (using a blurred screenshot of your desktop)
* Upon detecting motion on your laptops built-in webcam, ProtectMyLaptop snaps photos continuously until the motion stops. The photos should be stored on your Dropbox (or any other cloud account). This way, if someone does manage to steal your laptop, you can go to your Dropbox account to get a look at his/her face.
* In the event that your laptop lid is closed or the power button is pressed, ProtectMyLaptop uses Twilio to send a text message to your cell phone to alert you that your laptop is being stolen.

# How do I start ProtectMyLaptop?

Run the `screenlock.sh` script.

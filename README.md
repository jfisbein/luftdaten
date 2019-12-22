Luftdaten RaspberryPI script
============================

Simple script to send info to [Luftdaten](https://luftdaten.info/en/home-en/), based on Pimoroni provided example.
Modifications:
- Added log file, with memory buffering and daily rotation.
- Modified screen info to show latest status and information sent date.

### Installation
follow [Pimoroni instructions](https://learn.pimoroni.com/tutorial/sandyj/getting-started-with-enviro-plus).
### Usage
Download file and launch with `sudo python luftdaten.py`.

You can make it launch on start adding the line
`@reboot sudo python <path to your file>luftdaten.py` to the crontab.

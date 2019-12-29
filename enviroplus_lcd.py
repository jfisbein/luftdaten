import datetime

import ST7735
from PIL import Image, ImageDraw


class EnviroplusLCD:
    def __init__(self, font):
        # Create LCD instance
        self.disp = ST7735.ST7735(
            port=0,
            cs=ST7735.BG_SPI_CS_FRONT,
            dc=9,
            backlight=12,
            rotation=270,
            spi_speed_hz=10000000
        )
        # Initialize display
        self.disp.begin()

        self.WIDTH = self.disp.width
        self.HEIGHT = self.disp.height
        self.font = font

    # Display Last request date, last request status and Wi-Fi status on LCD
    def display_status(self, wifi_status, info_status):
        text_colour = (255, 255, 255)
        ok_back_colour = (0, 0, 0)  # Black
        error_back_colour = (85, 15, 15)  # Red
        back_colour = ok_back_colour if wifi_status == 'connected' else error_back_colour
        message = "{:%Y-%m-%d %H:%M:%S}\nLast update: {}\nWi-Fi: {}".format(datetime.datetime.now(), info_status, wifi_status)
        img = Image.new('RGB', (self.WIDTH, self.HEIGHT), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        size_x, size_y = draw.textsize(message, self.font)
        x = (self.WIDTH - size_x) / 2
        y = (self.HEIGHT / 2) - (size_y / 2)
        draw.rectangle((0, 0, 160, 80), back_colour)
        draw.text((x, y), message, font=self.font, fill=text_colour)
        self.disp.display(img)

    def turnoff(self):
        self.disp.set_backlight(0)

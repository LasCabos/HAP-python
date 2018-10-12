"""
An Accessory for Adafruit NeoPixels attached to GPIO Pin18
 Tested using Python 3.5/3.6 Raspberry Pi
 This device uses all available services for the Homekit Lightbulb API
 Note: RPi GPIO must be PWM. Neopixels.py will warn if wrong GPIO is used
       at runtime
 Note: This Class requires the installation of rpi_ws281x lib
       Follow the instllation instructions;
           git clone https://github.com/jgarff/rpi_ws281x.git
           cd rpi_ws281x
           scons

           cd python
           sudo python3.6 setup.py install
 https://learn.adafruit.com/neopixels-on-raspberry-pi/software

 Apple Homekit API Call Order
 User changes light settings on iOS device
 Changing Brightness - State - Hue - Brightness
 Changing Color      - Saturation - Hue
 Changing Temp/Sat   - Saturation - Hue
 Changing State      - State

 Apple Homekit API Values 
 Hue: 0 -360
 Saturuation: 0 - 100
 Brightness: 0 - 100
 State: 0 - 1
"""

from neopixel import *
from random import randrange
import time
import colorsys

from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_LIGHTBULB


class Neo_Color:
    """Class is used for easy passing and converting of colors between
    Apple HomeKit API and NeoPixel Library
    Conversion from HSV to RGB use python colorsys library whos values 
    range from 0 - 1 which require conversions to 8bit rgb and HomeKit API 
    standards"""

    def __init__(self):
        """Do not invoke directly - Use class methods
        We are setting a default red just incase"""
        self._red = 255
        self._green = 0
        self._blue = 0
        self._hue = 0
        self._saturation = 100
        self._brightness = 100

    @classmethod
    def from_rgb(cls, red, green, blue):
        color = cls()
        color.set_color_with_rgb(red, green, blue)
        return color

    @classmethod
    def from_hsv(cls, hue, saturation, brightness):
        color = cls()
        color.set_color_with_hsv(hue, saturation, brightness)
        return color

    # Pre defined Colors
    @classmethod
    def black(cls):
        color = cls()
        color.set_color_with_rgb(0, 0, 0)
        return color

    @classmethod
    def white(cls):
        color = cls()
        color.set_color_with_rgb(255, 255, 255)
        return color
    # End predefined colors

    @classmethod
    def generate_random_color(cls):
        color = cls()
        color.set_color_with_rgb(randrange(256), randrange(256), randrange(256))
        return color

    def _update_member_rgb_values(self, rgb_tuple):
        self._red = rgb_tuple[0] * 255
        self._green = rgb_tuple[1] * 255
        self._blue = rgb_tuple[2] * 255

    def get_rgb(self):
        return self._red, self._green, self._blue

    def set_color_with_rgb(self, red, green, blue):
        self._red = red
        self._green = green
        self._blue = blue
        hsv = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
        self._hue = hsv[0] * 360
        self._saturation = hsv[1] * 100
        self._brightness = hsv[2] * 100

    def get_hsv(self):
        hue = self._hue
        sat = self._saturation
        br = self._brightness
        return hue, sat, br

    def get_hex(self):
        hexColour = int('%02x%02x%02x%02x' % (int(self._red) * 255,
                                              int(self._green) * 255,
                                              int(self._blue) * 255,
                                              1), 16)
        return hexColour

    def set_color_with_hsv(self, hue, saturation, brightness):
        self._hue = hue
        self._saturation = saturation
        self._brightness = brightness
        rgb = colorsys.hsv_to_rgb(hue / 360, saturation / 100, brightness / 100)
        self._red = rgb[0] * 255
        self._green = rgb[1] * 255
        self._blue = rgb[2] * 255

    def set_hue(self, hue):
        self._hue = hue
        rgb = colorsys.hsv_to_rgb(self._hue / 360, self._saturation / 100, self._brightness / 100)
        self._update_member_rgb_values(rgb)

    def set_saturation(self, saturation):
        self._saturation = saturation
        rgb = colorsys.hsv_to_rgb(self._hue / 360, self._saturation / 100, self._brightness / 100)
        self._update_member_rgb_values(rgb)

    def set_brightness(self, brightness):
        self._brightness = brightness
        rgb = colorsys.hsv_to_rgb(self._hue / 360, self._saturation / 100, self._brightness / 100)
        self._update_member_rgb_values(rgb)


class NeoPixelLightStrip_Fader(Accessory):

    category = CATEGORY_LIGHTBULB

    def __init__(self, LED_count, is_GRB, LED_pin,
                 LED_freq_hz, LED_DMA, LED_brightness,
                 LED_invert, *args, **kwargs):

        """
        LED_Count - the number of LEDs in the array
        is_GRB - most neopixels are GRB format - Normal:True
        LED_pin - must be PWM pin 18 - Normal:18
        LED_freq_hz - frequency of the neopixel leds - Normal:800000
        LED_DMA - Normal:10
        LED_Brightness - overall brightness - Normal:255
        LED_invert - Normal:False
        For more information regarding these settings
            please review rpi_ws281x source code
        """

        super().__init__(*args, **kwargs)

        # Set our neopixel API services up using Lightbulb base
        serv_light = self.add_preload_service(
            'Lightbulb', chars=['On', 'Hue', 'Saturation', 'Brightness'])

        # Configure our callbacks
        self.char_hue = serv_light.configure_char(
            'Hue', setter_callback=self.hue_changed)
        self.char_saturation = serv_light.configure_char(
            'Saturation', setter_callback=self.saturation_changed)
        self.char_on = serv_light.configure_char(
            'On', setter_callback=self.state_changed)
        self.char_on = serv_light.configure_char(
            'Brightness', setter_callback=self.brightness_changed)

        # Set our startup color - Red
        self.color = Neo_Color.from_rgb(255, 0, 0)
        print("INIT Color: {}".format(self.color.get_rgb()))
        self.accessory_state = 0
        self.is_GRB = is_GRB  # Most neopixels are Green Red Blue
        self.LED_count = LED_count

        self.neo_strip = Adafruit_NeoPixel(LED_count, LED_pin, LED_freq_hz,
                                           LED_DMA, LED_invert, LED_brightness)
        self.neo_strip.begin()

        # Color Fade
        self.old_time = time.time()
        self.color_fade_array = [self.color]
        self.MAX_COLORFADE_COLORS = 2

    def state_changed(self, value):
        self.accessory_state = value
        if value == 1:  # On
            self.hue_changed(self.color.get_hsv()[0])
        else:
            self.update_neopixel_with_color(Neo_Color.black())  # Off
            if(len(self.color_fade_array) > 1):
                self.color_fade_array.clear()  # Lets clear the array to stop the color fade

# Lets check if we should update our color
    @Accessory.run_at_interval(1)
    def run(self):
        if(len(self.color_fade_array) > 1):
            start_color = self.color_fade_array[0]
            end_color = self.color_fade_array[1]
            current_color = self.color
            # Calc color trantions
            INTERVAL = 1  # seconds - Should be the same as the parameter in this function
            TRANSITION_LENGTH = 60  # seconds
            delta_hue = end_color.get_hsv()[0] - start_color.get_hsv()[0]
            delta_saturation = end_color.get_hsv()[1] - start_color.get_hsv()[1]
            hue_change_per_interval = delta_hue / TRANSITION_LENGTH * INTERVAL
            saturation_change_per_interval = delta_saturation / TRANSITION_LENGTH * INTERVAL

            #TODO: - Update with hex color for check
            if(current_color.get_hex() == end_color.get_hex()):
                # We have reached the end of the color fade lets switch them and go back
                self.color_fade_array[0], self.color_fade_array[1] = self.color_fade_array[1], self.color_fade_array[0]
                print("Reached the end of the color fade array - switching back")
            else:
                new_hue = current_color.get_hsv()[0] + hue_change_per_interval
                new_saturation = current_color.get_hsv()[1] + saturation_change_per_interval
                new_brightness = current_color.get_hsv()[2]
                new_color = Neo_Color.from_hsv(new_hue, new_saturation, new_brightness)
                print("New Color: {}".format(new_color.get_rgb()))
                self.update_neopixel_with_color(new_color)
                self.color = new_color

    def hue_changed(self, value):
        # ---------- New Color Fade Stuff ---------
        new_color = Neo_Color.from_hsv(value, self.color.get_hsv()[1], self.color.get_hsv()[2])
        print("Color HEX: {} RGB: {}".format(self.color.get_hex(), self.color.get_rgb()))
        print("New Color HEX: {} RGB: {}".format(new_color.get_hex(),new_color.get_rgb()))

        if(new_color.get_hex() != self.color.get_hex()):
            new_time = time.time()
            delta_time = new_time - self.old_time
            self.old_time = time.time()
            print("Delta_time: {}".format(delta_time))
            if(0.25 < delta_time < 1.0):
                if(len(self.color_fade_array) < self.MAX_COLORFADE_COLORS):
                    self.color_fade_array.insert(0, new_color)
                    print("Main::hue_changed - inserting new color into array")
                else:
                    self.color_fade_array.pop()
                    self.color_fade_array.insert(0, new_color)
                    print("Main::hue_changed - poping last value and insert")
        else:
            self.color_fade_array.clear()
            self.color_fade_array.append(new_color)
        # ------------ End new color fade -------------

        # Lets only change the LEDs color if the state is on
        self.color.set_hue(value)  # self.color = new_color
        if self.accessory_state == 1:
            self.update_neopixel_with_color(self.color)

    def brightness_changed(self, value):
        self.color.set_brightness(value)
        self.hue_changed(self.color.get_hsv()[0])

    def saturation_changed(self, value):
        self.color.set_saturation(value)
        self.hue_changed(self.color.get_hsv()[0])

    def update_neopixel_with_color(self, color):
        rgb_tuple = color.get_rgb()
        for i in range(self.LED_count):
            if(self.is_GRB):
                self.neo_strip.setPixelColor(i, Color(int(rgb_tuple[1]),
                                                      int(rgb_tuple[0]),
                                                      int(rgb_tuple[2])))
            else:
                self.neo_strip.setPixelColor(i, Color(int(rgb_tuple[0]),
                                                      int(rgb_tuple[1]),
                                                      int(rgb_tuple[2])))
        self.neo_strip.show()

    def flash_pixels(self, number_of_flashes, hsv_hue_color):
        # Note: - Flashing does not work yet because I dont know how to thread
        rgb_tuple = self.hsv_to_rgb(
                hsv_hue_color, self.saturation, self.brightness)
        for x in range(number_of_flashes):
            for i in range(self.LED_count):
                if(self.is_GRB): #On
                    self.neo_strip.setPixelColor(i, Color(int(rgb_tuple[1], rgb_tuple[0], rgb_tuple[2])))
                else:
                    self.neo_strip.setPixelColor(i, Color(int(rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])))
                self.neo_strip.setPixelColor(i, Color(0, 0, 0))

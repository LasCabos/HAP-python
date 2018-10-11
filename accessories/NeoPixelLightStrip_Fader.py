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

    def set_color_with_hsv(self, hue, saturation, brightness):
        self._hue = hue
        self._saturation = saturation
        self._brightness = brightness
        rgb = colorsys.hsv_to_rgb(hue, saturation, brightness)
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
            'Hue', setter_callback=self.set_hue)
        self.char_saturation = serv_light.configure_char(
            'Saturation', setter_callback=self.set_saturation)
        self.char_on = serv_light.configure_char(
            'On', setter_callback=self.set_state)
        self.char_on = serv_light.configure_char(
            'Brightness', setter_callback=self.set_brightness)

        # Set our startup color - Red
        self.color = Neo_Color.from_rgb(255, 0, 0)
        print("INIT Color: {}".format(self.color.get_rgb()))
        self.accessory_state = 0
        self.is_GRB = is_GRB  # Most neopixels are Green Red Blue
        self.LED_count = LED_count

        self.neo_strip = Adafruit_NeoPixel(LED_count, LED_pin, LED_freq_hz,
                                           LED_DMA, LED_invert, LED_brightness)
        self.neo_strip.begin()

        # # Color Fade
        # self.old_time = time.time()
        # self.hue_color_fade_array = [self.color]
        # self.MAX_COLORFADE_COLORS = 3

    def set_state(self, value):
        self.accessory_state = value
        if value == 1:  # On
            self.set_hue(self.color.get_hsv()[0])
        else:
            self.update_neopixel_with_color(Neo_Color.black())  # Off
           # self.hue_color_fade_array.clear()  # Lets clear the array to stop the color fade

# # Lets check if we should update our color
#     @Accessory.run_at_interval(1)
#     def run(self):
#         # NOTE: - The problem with hue is its resolution.1 hue = ~4 RGB value.
#         # therefore we must incriment by 1/4 iterations for smooth transistion
#         # This is just a full rainbow color fade
#         if(len(self.hue_color_fade_array) > 1):
#             new_hue = self.hue + 0.25
#             if(new_hue > 360):
#                 new_hue = 0
#             new_color_tuple = self.hsv_to_rgb(new_hue, self.saturation, self.brightness)
#             if(len(new_color_tuple) == 3):
#                 self.update_neopixel_with_color(new_color_tuple[0], new_color_tuple[1], new_color_tuple[2])
#                 self.hue = new_hue

    def set_hue(self, value):
        # ---------- New Color Fade Stuff ---------
        # print("------ Hue Changed -----")
        # # Check if color fade color
        # if(value != self.hue):  # if we have a new hue value
        #     newTime = time.time()
        #     deltaTime = newTime - self.old_time
        #     # Append our new color if we click bettween times
        #     if(0.25 < deltaTime and deltaTime < 1.0):
        #         if(len(self.hue_color_fade_array) < self.MAX_COLORFADE_COLORS):
        #             self.hue_color_fade_array.insert(0, value)
        #             print("Inserting new hue in array")
        #             # TODO: - Add flashing so user knows they are in color change mode
        #         else:
        #             self.hue_color_fade_array.pop()
        #             self.hue_color_fade_array.insert(0, value)
        #             print("Poping last value and inserting")
        #     else:  # Lets reset our list
        #         self.hue_color_fade_array.clear()
        #         self.hue_color_fade_array.append(value)
        #         print("Resetting array and appending")

        #     print("DeltaTime: ", deltaTime)
        #     print("Color Array: ", self.hue_color_fade_array)
        #     print("----- End Hue ------")

        #     self.old_time = newTime
        # ----------- End New Color Fade Stuff --------

        # Lets only change the LEDs color if the state is on
        self.color.set_hue(value)
        if self.accessory_state == 1:
            self.update_neopixel_with_color(self.color)

    def set_brightness(self, value):
        self.color.set_brightness(value)
        self.set_hue(self.color.get_hsv()[0])

    def set_saturation(self, value):
        self.color.set_saturation(value)
        self.set_hue(self.color.get_hsv()[0])

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

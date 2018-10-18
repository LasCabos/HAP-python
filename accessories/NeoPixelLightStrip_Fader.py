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
 Changing Brightness - Brightness - State
 Changing Color      - Saturation - Hue
 Changing Temp/Sat   - Saturation - Hue
 Changing State On    - State
 First Power On at boot - Brightness - State

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

    @classmethod
    def from_color(cls, color):
        return_color = cls()
        rgb_tuple = color.get_rgb()
        return_color.set_color_with_rgb(rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])
        return return_color

    @classmethod
    def from_24Bit_RGB(cls, WRGB_24Bit):
        color = cls()
        red = WRGB_24Bit >> 16 & 0xFF
        green = WRGB_24Bit >> 8 & 0xFF
        blue = WRGB_24Bit & 0xFF
        print("from_24Bit_RGB: {}, {}, {}".format(red, green, blue))
        color.set_color_with_rgb(red, green, blue)
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

    @classmethod
    def blue(cls):
        color = cls()
        color.set_color_with_rgb(0, 0, 255)
        return color

    @classmethod
    def green(cls):
        color = cls()
        color.set_color_with_rgb(0, 255, 0)
        return color

    @classmethod
    def red(cls):
        color = cls()
        color.set_color_with_rgb(255, 0, 0)
        return color
    # End predefined colors

    @classmethod  # INFO: - Testing only remove for merge
    def generate_random_color(cls):
        color = cls()
        color.set_color_with_rgb(randrange(256),
                                 randrange(256),
                                 randrange(256))
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
        rgb = colorsys.hsv_to_rgb(hue / 360,
                                  saturation / 100,
                                  brightness / 100)
        self._red = rgb[0] * 255
        self._green = rgb[1] * 255
        self._blue = rgb[2] * 255

    def set_hue(self, hue):
        self._hue = hue
        rgb = colorsys.hsv_to_rgb(self._hue / 360,
                                  self._saturation / 100,
                                  self._brightness / 100)
        self._update_member_rgb_values(rgb)

    def get_hue(self):
        return self._hue

    def get_saturation(self):
        return self._saturation

    def set_saturation(self, saturation):
        self._saturation = saturation
        rgb = colorsys.hsv_to_rgb(self._hue / 360,
                                  self._saturation / 100,
                                  self._brightness / 100)
        self._update_member_rgb_values(rgb)

    def set_brightness(self, brightness):
        self._brightness = brightness
        rgb = colorsys.hsv_to_rgb(self._hue / 360,
                                  self._saturation / 100,
                                  self._brightness / 100)
        self._update_member_rgb_values(rgb)


class ColorFadeColors():
    """ This class stores the color fade colors and allows
    convenience for adding and removing
    Max Storrage = 2 """

    def __init__(self, color1, color2):
        self._primaryColor = color1
        self._secondaryColor = color2
        self._current_pixel_color = self._primaryColor #FIXME: - change to current color

    def insert_new_color(self, color):
        self._secondaryColor = self._primaryColor
        self._primaryColor = color

    def set_primary_color(self, color):
        self._primaryColor = color

    def get_primary_color(self):
        return self._primaryColor

    def set_secondary_color(self, color):
        self._secondaryColor = color

    def get_secondary_color(self):
        return self._secondaryColor

    def set_current_pixel_color(self, color):
        self._current_pixel_color = color

    def get_current_pixel_color(self):
        return self._current_pixel_color

    def print_colors(self, asRGB):
        if(asRGB):
            print("RGB - Pri: {}   Sec: {}   LRPC: {}".format(self._primaryColor.get_rgb(),
                                                              self._secondaryColor.get_rgb(),
                                                              self._current_pixel_color.get_rgb()))
        else:
            print("HSV - Pri: {}   Sec: {}   LRPC: {}".format(self._primaryColor.get_hsv(),
                                                              self._secondaryColor.get_hsv(),
                                                              self._current_pixel_color.get_hsv()))



class NeoPixelLightStrip_Fader(Accessory):

    category = CATEGORY_LIGHTBULB
    COLOR_FADE_INTERVAL = 1

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

        self.accessory_state = 0
        self.is_GRB = is_GRB  # Most neopixels are Green Red Blue
        self.LED_count = LED_count

        self.neo_strip = Adafruit_NeoPixel(LED_count, LED_pin, LED_freq_hz,
                                           LED_DMA, LED_invert, LED_brightness)
        self.neo_strip.begin()

        # Color Fade Mode
        # Current Mode
        self.mode = 0x00  # Mode0x00: Single Color, Mode0x01: Color Fade
        self.mode_timer = time.time()
        self.mode_counter = 0
        self.color_fade_ready_timer = time.time()
        self.color_fade_colors = ColorFadeColors(Neo_Color.red(), Neo_Color.blue())
        self.color_fade_colors.print_colors(True)
        self.old_time = time.time()


    def state_changed(self, value):
        print("state_changed")
        self.accessory_state = value

        if value == 1:  # On
            if(self.wasBrightness != 1):
                if(time.time() - self.mode_timer > 1 and time.time() - self.mode_timer < 5 ):
                    self.mode_counter += 1
                    print("Counter: {}  deltaTime: {}".format(self.mode_counter, self.mode_timer))
                    if(self.mode_counter == 3):
                        self.mode ^= 1
                        print("Changing Mode To: {}".format(self.mode))
                        self.mode_counter = 0
                        if(self.mode == 0x00):
                            self.flash_pixels(3, 0.5, Neo_Color.red())  # White indicates single color mode
                        else:
                            self.flash_pixels(3, 0.5, Neo_Color.green())  # Blue indicates color fade mode
                else:
                    self.mode_counter = 0
            print("state")
            self.update_neopixel_with_color(self.color_fade_colors.get_primary_color())
            self.color_fade_colors.set_current_pixel_color(self.color_fade_colors.get_primary_color())

        else:
            self.update_neopixel_with_color(Neo_Color.black())  # Off

        self.mode_timer = time.time()

        self.wasBrightness = 0  # Reset our hack to 0


# Lets check if we should update our color
    @Accessory.run_at_interval(COLOR_FADE_INTERVAL)
    def run(self):
        if(self.accessory_state == 1 and self.mode == 0x01):
            print("----- Start Loop ----")
            start_color = self.color_fade_colors.get_primary_color()
            end_color = self.color_fade_colors.get_secondary_color()
            current_color = self.color_fade_colors.get_current_pixel_color()

            print("Colors: {}, {}, {}".format(start_color.get_rgb(), end_color.get_rgb(), current_color.get_rgb()))

            #Force Fade
            hue_val_inc = 1

            # Set new values 
            new_hue = current_color.get_hue() + hue_val_inc
            if(new_hue > 360):
                new_hue = 0

            current_color.set_hue(new_hue)
            self.update_neopixel_with_color(current_color)
            self.color_fade_colors.set_current_pixel_color(current_color)


            

            print("Current Color RGB/HSV: {} - {}".format(current_color.get_rgb(),current_color.get_hsv()))

            if(new_hue > 360):
                new_hue = 0
                print("Hue maxed")

            # new_color = Neo_Color.from_hsv(new_hue, current_color.get_saturation(), 100)
            # print("Applying New Color RGB/HSV: {} - {}".format(new_color.get_rgb(), new_color.get_hsv()))
            # self.update_neopixel_with_color(new_color)
            # self.update_last_recorded_pixel_color(new_color)
            # print("----- End Loop ----")
            # print("")
            #self.update_neopixel_with_color(new_color)
            #self.last_recorded_pixel_color = new_color

            # TRANSITION_LENGTH = 60 * 10  # seconds
            # delta_hue = end_color.get_hsv()[0] - start_color.get_hsv()[0]
            # delta_saturation = end_color.get_hsv()[1] - start_color.get_hsv()[1]
            # print("Detlas: {}, {}".format(delta_hue, delta_saturation))

            # hue_change_per_interval = delta_hue / TRANSITION_LENGTH * self.COLOR_FADE_INTERVAL
            # saturation_change_per_interval = delta_saturation / TRANSITION_LENGTH * self.COLOR_FADE_INTERVAL
            # print("Changes: {}, {}".format(hue_change_per_interval, saturation_change_per_interval))

            # if(abs(hue_change_per_interval) > 0.25 or abs(saturation_change_per_interval) > 0.25):
            #         print("""Your transition may contain visable flashing.
            #                Please increase your transition length or decrease
            #                your color fade interval""")

            # if(current_color.get_hex() == end_color.get_hex()):
            #     # We have reached the end of the color fade lets switch them and go back
            #     self.color_fade_colors_array[0], self.color_fade_colors_array[1] = self.color_fade_colors_array[1], self.color_fade_colors_array[0]
            #     print("Reached the end of the color fade array - switching back")
            # else:
            #     new_hue = current_color.get_hsv()[0] + hue_change_per_interval
            #     new_saturation = current_color.get_hsv()[1] + saturation_change_per_interval
            #     new_brightness = current_color.get_hsv()[2]
            #     new_color = Neo_Color.from_hsv(new_hue, new_saturation, new_brightness)
            #     print("New Color: {}".format(new_color.get_rgb()))
            #     #FIXME: - this needs to be only called after the flashing has finished... right now its broken
            #     #self.update_neopixel_with_color(new_color)
            #     self.color = new_color

            # if(len(self.color_fade_colors_array) > 1):
            #     start_color = self.color_fade_colors_array[0]
            #     end_color = self.color_fade_colors_array[1]
            #     current_color = self.color
            #     # Calc color trantions
            #     TRANSITION_LENGTH = 60 * 10  # seconds
            #     delta_hue = end_color.get_hsv()[0] - start_color.get_hsv()[0]
            #     delta_saturation = end_color.get_hsv()[1] - start_color.get_hsv()[1]

            #     hue_change_per_interval = delta_hue / TRANSITION_LENGTH * self.COLOR_FADE_INTERVAL
            #     saturation_change_per_interval = delta_saturation / TRANSITION_LENGTH * self.COLOR_FADE_INTERVAL
            #     if(abs(hue_change_per_interval) > 0.25 or abs(saturation_change_per_interval) > 0.25):
            #         print("""Your transition may contain visable flashing.
            #                Please increase your transition length or decrease
            #                your color fade interval""")

            #     #TODO: - Update with hex color for check
            #     if(current_color.get_hex() == end_color.get_hex()):
            #         # We have reached the end of the color fade lets switch them and go back
            #         self.color_fade_colors_array[0], self.color_fade_colors_array[1] = self.color_fade_colors_array[1], self.color_fade_colors_array[0]
            #         print("Reached the end of the color fade array - switching back")
            #     else:
            #         new_hue = current_color.get_hsv()[0] + hue_change_per_interval
            #         new_saturation = current_color.get_hsv()[1] + saturation_change_per_interval
            #         new_brightness = current_color.get_hsv()[2]
            #         new_color = Neo_Color.from_hsv(new_hue, new_saturation, new_brightness)
            #         print("New Color: {}".format(new_color.get_rgb()))
            #         self.update_neopixel_with_color(new_color)
            #         self.color = new_color

    def hue_changed(self, value):
        print("Hue_change")
        print("Hue Before:")
        self.color_fade_colors.print_colors(False)
        old_color = self.color_fade_colors.get_primary_color()
        new_color = Neo_Color.from_color(old_color)
        print("Old Color")
        print(old_color.get_hsv())
        print("new_color")
        print(new_color.get_hsv())
        new_color.set_hue(value)
        print("new_color_new_hue")
        print(new_color.get_hsv())
        self.color_fade_colors.insert_new_color(new_color)

        if(self.accessory_state == 1):
            print("hue")
            self.update_neopixel_with_color(self.color_fade_colors.get_primary_color())
            self.color_fade_colors.set_current_pixel_color(self.color_fade_colors.get_primary_color())

        print("Hue After: ")
        self.color_fade_colors.print_colors(False)

    def brightness_changed(self, value):
        print("brightness_changed")
        self.wasBrightness = 1  # Hack for Appkit API brightness changing state
        pri = self.color_fade_colors.get_primary_color()
        sec = self.color_fade_colors.get_secondary_color()

        pri.set_brightness(value)
        sec.set_brightness(value)

        if(self.accessory_state == 1):
            print("brightness")
            self.update_neopixel_with_color(pri)
            self.color_fade_colors.set_current_pixel_color(pri)
            print(self.color_fade_colors.print_colors(False))

    def saturation_changed(self, value):
        print("saturation_changed")
        print("Sat Before: ")
        self.color_fade_colors.print_colors(False)
        """ Saturation is never called on its own and always follwed by hue
            Because of this we will update the primary and secondary colors
            saturation value only and let the hue call handel the final
            insertion and application of the new colors"""
        pri = self.color_fade_colors.get_primary_color()

        pri.set_saturation(value)

        print("Sat After: ")
        self.color_fade_colors.print_colors(False)

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


    def flash_pixels(self, number_of_flashes, delay_between_flashes_seconds, flash_color):
        # Note: - Flashing does not work yet because I dont know how to thread
        for x in range(number_of_flashes):
            self.update_neopixel_with_color(Neo_Color.black())
            time.sleep(delay_between_flashes_seconds)
            self.update_neopixel_with_color(flash_color)
            time.sleep(delay_between_flashes_seconds)

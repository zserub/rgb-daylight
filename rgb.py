#!/usr/bin/python3

class RGB(object):

    def __init__(self, config, r=None, g=None, b=None, settype=None):
        self.config = config
        self._white_balance = self.config.get("white_balance", [1, 1, 1])
        self._intensity = self.config.get("intensity", 1)
        self.led_pins = self.config.get(
            "led_pins", {"r": 22, "g": 27, "b": 17})
        self._color = [0, 0, 0]

    def set(self):
        if len(self._color) > 3 and self._color[3] == 1:
            r = self.color[0]
            g = self.color[1]
            b = self.color[2]
        else:
            r=round((self.color[0] * self.white_balance[0] * self.intensity), 3)
            g=round((self.color[1] * self.white_balance[1] * self.intensity), 3)
            b=round((self.color[2] * self.white_balance[2] * self.intensity), 3)

        pwm = open('/dev/pi-blaster', 'w')
        pwm.write(str(self.led_pins["r"])+"="+str(r)+" ")
        pwm.write(str(self.led_pins["g"])+"="+str(g)+" ")
        pwm.write(str(self.led_pins["b"])+"="+str(b)+"\n")
        pwm.close()
        print("r"+"="+str(r))
        print("g"+"="+str(g))
        print("b"+"="+str(b))

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value
        self.set()

    @property
    def intensity(self):
        return self._intensity

    @intensity.setter
    def intensity(self, value):
        self._intensity = value
        self.set()

    @property
    def white_balance(self):
        return self._white_balance

    @white_balance.setter
    def white_balance(self, value):
        self._white_balance = value
        self.set()

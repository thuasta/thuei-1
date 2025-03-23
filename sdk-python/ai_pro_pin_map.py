
"""
Alternative pin mappings for Orange PI Ai Pro
(https://drive.google.com/drive/folders/1jALhyhwjSVsxwSX1MwhjiOyQdx_fwlFg)

Usage:

.. code:: python
   import orangepi.4
   from OPi import GPIO

   GPIO.setmode(orangepi.4.BOARD) or GPIO.setmode(orangepi.4.BCM)
"""

# pin number = (position of letter in alphabet - 1) * 32 + pin number
# So, PD14 will be (4 - 1) * 32 + 14 = 110

# Orange Pi Ai Pro physical board pin to GPIO pin
_BOARD = {
    3: 76,    # SDA7
    5: 75,    # SCL7
    7: 226,   # GPIO7_02
    8: 14,    # UTXD0
    10: 15,   # URXD0
    11: 82,   # GPIO2_18
    12: 227,  # GPIO7_03
    13: 38,   # GPIO1_06
    15: 79,   # GPIO2_15
    16: 80,   # GPIO2_16
    18: 25,   # GPIO0_25
    19: 91,   # SPI0_SD0
    21: 92,   # SPI0_SDI
    22: 2,    # GPIO0_02
    23: 89,   # SPI0_CLK
    24: 90,   # SPI0_CS
    26: 83,   # GPIO2_19
    29: 231,  # URXD7
    31: 84,   # GPIO2_20
    32: 33,   # PWM3
    33: 128,  # GPIO4_00
    35: 228,  # GPIO7_04
    36: 81,   # GPIO2_17
    37: 3,    # GPIO0_03
    38: 230,  # GPIO7_06
    40: 229,  # GPIO7_05
}

# No reason for BCM mapping, keeping it for compatibility
BCM = _BOARD
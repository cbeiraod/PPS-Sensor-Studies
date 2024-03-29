#############################################################################
# zlib License
#
# (C) 2023 Cristóvão Beirão da Cruz e Silva <cbeiraod@cern.ch>
#
# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the authors be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.
#############################################################################

__version__ = '0.0.2'

from .PPSHitmap import PPSHitmap
from .SensorPad import SensorPad
from .Sensor import Sensor
from .Sensor import calcLossProb
from .CustomizedSensors import *

from .functions import *

__all__ = [
    "PPSHitmap",
    "SensorPad",
    "Sensor",
    "calcLossProb",
]

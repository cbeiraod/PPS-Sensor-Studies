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

class IntField:
    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __set__(self, instance, value:int):
        if not isinstance(value, int):
            raise ValueError(f'expecting integer in {self.name}')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name

class PositiveIntField:
    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __set__(self, instance, value:int):
        if not isinstance(value, int):
            raise ValueError(f'expecting integer in {self.name}')
        if value <= 0:
            raise ValueError(f'expecting a positive integer in {self.name}')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name

class NonNegativeIntField:
    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __set__(self, instance, value:int):
        if not isinstance(value, int):
            raise ValueError(f'expecting integer in {self.name}')
        if value < 0:
            raise ValueError(f'expecting a positive integer in {self.name}')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name

class FloatField:
    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __set__(self, instance, value:float):
        if not (isinstance(value, float) or isinstance(value, int)):
            raise ValueError(f'expecting float in {self.name}')
        instance.__dict__[self.name] = float(value)

    def __set_name__(self, owner, name):
        self.name = name

class ListField:
    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __set__(self, instance, value:list):
        if not isinstance(value, list):
            raise ValueError(f'expecting list in {self.name}')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name

class FloatListField:
    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __set__(self, instance, value:list):
        if not isinstance(value, list):
            raise ValueError(f'expecting list in {self.name}')
        if not (all(isinstance(x, float) or isinstance(x, int) for x in value)):
            raise ValueError(f'expecting list of floats in {self.name}')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name

class FloatPairListField:
    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __set__(self, instance, value:list):
        if not isinstance(value, list):
            raise ValueError(f'expecting list in {self.name}')
        if not all(isinstance(x, tuple) for x in value):
            raise ValueError(f'expecting list of tuples in {self.name}')
        if not all(isinstance(x, float) or isinstance(x, int) for x in [item for y in value for item in y]):
            raise ValueError(f'expecting list of tuples of floats in {self.name}')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name

__all__ = ["IntField", "PositiveIntField", "NonNegativeIntField", "FloatField", "ListField", "FloatListField", "FloatPairListField"]
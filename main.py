#!/usr/bin/env python3

"""
Coffee Life Test Fixture Application

Vikram Seshadri
December 4, 2020

"""


# Toggle unit and vessel fan
class AuxFunctions:
    def fan_toggle(unitfantoggle, vesselfantoggle):
        print("Unit fan and vessel fan is off")
        if unitfantoggle is True:
            # Turn unit fan on
            print("Unit fan is on")

        if vesselfantoggle is True:
            # Turn vessel fan on
            print("Vessel fan is on")

#!/usr/bin/python
#-*- coding:utf-8 -*-

#Copyright 2008-2009 pyEmpires Team
#This file is part of pyEmpires.

#pyEmpires is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#pyEmpires is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

import os
import pygame
from logging import basicConfig, DEBUG, ERROR, debug, error

basicConfig(level=DEBUG, filename="debuglogs.txt",
                    format="[%(levelname)s] %(module)s - %(funcName)s, (%(asctime)s) \n\t \n\t   %(message)s\
                    \n -------------------------------------------------------",
                    datefmt="%m-%d-%y, %H:%M")
basicConfig(level=ERROR, filename="errorlogs.txt",
                    format="[%(levelname)s] %(module)s - %(funcName)s, (%(asctime)s) \n\t \n\t   %(message)s \
                    \n -------------------------------------------------------",
                    datefmt="%m-%d-%y, %H:%M")

class Player(object):
    human_player, cpu_player = range(2)
    
    def __init__(self, mainObj, id, group=None, type=1):
        self.mainObj = mainObj
        self.id = id
        self.type = type
        
        # local groups
        self.all = pygame.sprite.RenderUpdates()
        self.units = pygame.sprite.Group()
        self.selectedUnits = pygame.sprite.OrderedUpdates()
        self.movingUnits = pygame.sprite.RenderUpdates()
        self.buildings = pygame.sprite.Group()
        self.ai = pygame.sprite.Group()
        
        # unit types groups
        units_path = "../resources/units"
        subdirs = os.listdir(units_path)
        joined_list = [os.path.join(units_path, path) for path in subdirs]
        units_strings = filter(lambda path: os.path.isdir(os.path.join(units_path, path)) and not path.startswith("."), subdirs)
        
        for str in units_strings:
            self.__setattr__("unit_" + str, pygame.sprite.Group())
        
        # ctrl groups
        self.ctrl = list()
        for i in xrange(10):
            self.ctrl.append(pygame.sprite.Group())
        
    def __eq__(self, player):
        return self.id == player.id
    
    def addTo(self, group, *sprites):
        """ to syncronize with global groups. """
        thegroup = self.__getattribute__(group)
        
        if thegroup == self.selectedUnits:
            thegroup.add(*sprites)
            self.mainObj.selectedUnits.add(*sprites)
            
        elif thegroup == self.movingUnits:
            thegroup.add(*sprites)
            self.mainObj.movingUnits.add(*sprites)
            
    def removeFrom(self, group, *sprites):
        """ to syncronize with global groups. """
        thegroup = self.__getattribute__(group)
        
        if thegroup == self.selectedUnits:
            thegroup.remove(*sprites)
            self.mainObj.selectedUnits.remove(*sprites)
            
        elif thegroup == self.movingUnits:
            thegroup.remove(*sprites)
            self.mainObj.movingUnits.remove(*sprites)
            
    def empty(self, group, i=0):
        """ to syncronize with global groups. """
        thegroup = self.__getattribute__(group)
        
        if thegroup == self.selectedUnits:
            thegroup.empty()
            self.mainObj.selectedUnits.empty()
        
    @staticmethod
    def joinGroups(*groups):
        empty = pygame.sprite.Group()
        for grp in groups:
            empty.add(*grp.sprites())
            
        return empty

    @staticmethod
    def intersectionGroups(*groups):
        # get all the sprites to group
        big_group = joinGroups(*groups)
        for spt in big_group.sprites():
            # check if that sprite is in all groups
            for grp in groups:
                if spt not in grp:
                    big_group.remove(spt)
                    break
            
        return big_group

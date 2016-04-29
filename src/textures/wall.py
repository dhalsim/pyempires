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

import pygame
from logging import basicConfig, debug, DEBUG, ERROR

basicConfig(level=DEBUG, filename="debuglogs.txt",
                    format="[%(levelname)s] %(module)s - %(funcName)s, (%(asctime)s) \n\t \n\t   %(message)s\
                    \n -------------------------------------------------------",
                    datefmt="%m-%d-%y, %H:%M")
basicConfig(level=ERROR, filename="errorlogs.txt",
                    format="[%(levelname)s] %(module)s - %(funcName)s, (%(asctime)s) \n\t \n\t   %(message)s \
                    \n -------------------------------------------------------",
                    datefmt="%m-%d-%y, %H:%M")
                    
class Wall(pygame.sprite.Sprite):
    def __init__(self, mainObj, image, position):
        pygame.sprite.Sprite.__init__(self)
        self.type = 'Wall'
        self.mainObj = mainObj
        self.image = image
        self.rect = image.get_rect()
        self.rect.topleft = position
        
    def __getstate__(self):
        odict = self.__dict__.copy() # copy the dict since we change it
        del odict['image']           # remove surface entry
        del odict['mainObj']         # remove surface entry
        return odict
        
    def update(self, *args):
        if "slide" in args:
            self.rect.move_ip(*args[1])

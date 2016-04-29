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

import math
import time
import pygame
from random import randrange, shuffle
import xml.etree.ElementTree as etree

from textures.text import Text, Terminal
from units.kurt import Kurt
from logging import basicConfig, debug, DEBUG, ERROR

basicConfig(level=DEBUG, filename="debuglogs.txt",
                    format="[%(levelname)s] %(module)s - %(funcName)s, (%(asctime)s) \n\t \n\t   %(message)s\
                    \n -------------------------------------------------------",
                    datefmt="%m-%d-%y, %H:%M")
basicConfig(level=ERROR, filename="errorlogs.txt",
                    format="[%(levelname)s] %(module)s - %(funcName)s, (%(asctime)s) \n\t \n\t   %(message)s \
                    \n -------------------------------------------------------",
                    datefmt="%m-%d-%y, %H:%M")

def shuffleList(liste):
    shuffle(liste)
    
def collide_rect(sprite1, sprite2):
    """ Sprite çarpışmalarında "rect" dışında kullanılacak olan colRect değişkenin
    çarpışıp çarpışmadığı burada test ediliyor. """
    if sprite1 == sprite2:
        return False
    return sprite2.rect.collidepoint(*sprite1.colPoints[0]) or sprite2.colRect.collidepoint(*sprite1.colPoints[1])
        
class ResourceManager(object):
    """ Tüm kaynakların oyunun başında yüklenmesini, ve erişilmesini sağlıyor. """
    image_resources = {'Kurt': 8}
    playerColors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 0, 0)]
    
    def __init__(self, mainObj):
        self.mainObj = mainObj
        
        self.degisik = pygame.image.load("../resources/units/Kurt/0.png")
        array = pygame.PixelArray(self.degisik)
        array.replace((0, 255, 255), (0, 255, 0))
        self.degisik = array.make_surface()
        self.degisik.set_colorkey((255, 0, 255))

        # animasyonlu sprite dosyaları yükleniyor
        for ad, sayi in ResourceManager.image_resources.items():
            self.__setattr__(ad, [])
            li = self.__getattribute__(ad)
            
            # her kullanıcı için farklı renkler
            for i in xrange(len(self.mainObj.players)):
                li.append([])
                
                for j in xrange(sayi):
                    # renk değiştirme
                    image = pygame.image.load('../resources/units/' + ad + '/' + str(j) + '.png')
                    array = pygame.PixelArray(image)
                    array.replace((0, 255, 255), ResourceManager.playerColors[i])
                    image = array.make_surface()
                    image.set_colorkey(image.get_at((0, 0)))
                    li[i].append(image)

                
        # sabit sprite dosyaları
        self.tile = pygame.image.load("../resources/textures/grass.png").convert_alpha()
        self.grass = pygame.image.load("../resources/textures/grass.png").convert_alpha()
        self.sand = pygame.image.load("../resources/textures/sand.png").convert_alpha()
        self.water = pygame.image.load("../resources/textures/water.png").convert_alpha()
        self.wall1 = pygame.image.load("../resources/textures/wall1.png").convert()
        self.wall1.set_colorkey((255, 0 , 255))
        
        #self.healthBarBorder = pygame.Surface(
        #self.healthBarBorder = pygame.Surface((0, 0, 0), copy(Unit.healthRect))
        
        pygame.font.init()
        self.__setattr__('xfont', pygame.font.Font("../resources/freemono.ttf", 12))
        
        # Keyboard
        self.keys = self.readKeyboardMap()

    def spriteClass(self, unitType, *args, **kwargs):
        """ String kullanarak sprite nesneleri yaratmaya yarar. """
        return eval(unitType)(*args, **kwargs)
    
    def readKeyboardMap(self):
        map_file = "../resources/keyboard.xml"
        map_xml = etree.parse(map_file)
        keyboard = map_xml.getroot()
        keys = dict()
        lst = ["a", "s", "d", "f", "esc", "+", "-", "*", "up", "down", "right", "left", "space"]
        
        for i, key in enumerate(keyboard):
            keys[lst[i]] = Key(eval("pygame." + key.text), eval("pygame." + key.attrib["helper"]))
        
        return keys
        
class Key(object):
    def __init__(self, key, mod=pygame.KMOD_NONE):
        self.key = key
        self.mod = mod
        
    def __eq__(self, other_key):
        return (self.key == other_key.key) and (self.mod | pygame.KMOD_NUM | pygame.KMOD_CAPS == other_key.mod | pygame.KMOD_NUM | pygame.KMOD_CAPS)
        
class Timer(object):
    """ A countdown, timer, controls if "duration" seconds passed, duration could be float. Used in attacking. """
    def __init__(self, duration=5, **kwargs):
        self.setTimer(duration)
        
        # additional arguments if needed
        for arg in kwargs:
            self.__setattr__(arg, kwargs[arg])
        
    def setTimer(self, duration):
        self.duration = duration
        self.startTime = time.time()
        
    def finished(self):
        return time.time() - self.startTime >= self.duration

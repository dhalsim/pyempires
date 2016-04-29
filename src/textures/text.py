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
                    
class Terminal(object):
    color = (255, 255, 255)
    bgcolor = (0, 0, 0)
    
    def __init__(self, mainObj, tempKuyrukUzunluk):
        self.tempKuyrukUzunluk = tempKuyrukUzunluk # Temp'in maximum uzunluğu
        self.mainObj = mainObj
        self.kuyruk = {}
        self.tmpKuyruk = {}
        self.tmpKeys = []
        self.bgSurface = pygame.Surface(self.mainObj.resolution)
        self.bgSurface.fill(Terminal.bgcolor)
                
    def tmpEkle(self, key, value):
        if key in self.tmpKuyruk.keys():
            self.tmpKuyruk[key].setImage(str(key) + ": " + str(value))
            return
        elif len(self.tmpKuyruk) >= self.tempKuyrukUzunluk:
            firstKey = self.tmpKeys.pop(0)
            self.tmpKuyruk[firstKey].kill()
            self.tmpKuyruk.pop(firstKey)
            
            for sprite in self.mainObj.tempConsoleFonts:
                sprite.rect.move_ip(0, -10)
        
        font = self.mainObj.resourceManager.xfont
        text = unicode(key) + ': ' + unicode(value)
        
        sprite = Text(font, text, key, (10, (len(self.mainObj.tempConsoleFonts) + len(self.mainObj.consoleFonts) + 1) * 10), Terminal.color, Terminal.bgcolor)
        self.tmpKuyruk[key] = sprite
        self.mainObj.tempConsoleFonts.add(sprite)
        self.tmpKeys.append(key)
    
    def ekle(self, key, value):
        if key in self.kuyruk.keys():
            self.kuyruk[key].setImage(str(key )+ ": " + str(value))
            return
        else:
            font = pygame.font.Font(None, 17)
            text = unicode(key) + ': ' + unicode(value)
            
            for sprite in self.mainObj.tempConsoleFonts:
                sprite.rect.move_ip(0, 10)
            
            sprite = Text(font, text, key, (10, (len(self.mainObj.consoleFonts) + 1) * 10), Terminal.color, Terminal.bgcolor)
            self.kuyruk[key] = sprite
            self.mainObj.consoleFonts.add(sprite)

class Text(pygame.sprite.Sprite):
    def __init__(self, font, text, key, position, color, bgcolor=None):
        pygame.sprite.Sprite.__init__(self)
        self.font = font
        self.text = unicode(text)
        self.key = key
        self.position = position
        self.color = color
        self.bgcolor = bgcolor
        
        if bgcolor:
            self.image = font.render(text, True, color, bgcolor)
        else:
            self.image = font.render(text, True, color)
        
        self.rect = self.image.get_rect()
        self.rect.topleft = self.position
        
    def setColor(self, color):
        if self.bgcolor:
            self.image = self.font.render(unicode(self.text), True, color, self.bgcolor)
        else:
            self.image = self.font.render(unicode(self.text), True, color)
        self.color = color
            
    def setImage(self, text):
        if self.bgcolor:
            self.image = self.font.render(unicode(text), True, self.color, self.bgcolor)
        else:
            self.image = self.font.render(unicode(text), True, self.color)
        
        self.rect = self.image.get_rect()
        self.rect.topleft = self.position

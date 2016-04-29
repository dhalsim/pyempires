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
from math import atan, atan2, degrees
from game_players import Player
from game_ai import KurtFSM
from unit import Unit, Vector2
from copy import copy
from logging import basicConfig, debug, DEBUG, ERROR

basicConfig(level=DEBUG, filename="debuglogs.txt",
                    format="[%(levelname)s] %(module)s - %(funcName)s, (%(asctime)s) \n\t \n\t   %(message)s\
                    \n -------------------------------------------------------",
                    datefmt="%m-%d-%y, %H:%M")
basicConfig(level=ERROR, filename="errorlogs.txt",
                    format="[%(levelname)s] %(module)s - %(funcName)s, (%(asctime)s) \n\t \n\t   %(message)s \
                    \n -------------------------------------------------------",
                    datefmt="%m-%d-%y, %H:%M")


class Kurt(Unit):
    sol, sag, yukari, asagi, yukari_sol, asagi_sol, yukari_sag, asagi_sag = range(8)
    colRect = [pygame.Rect(0, 37, 52, 7), pygame.Rect(0, 37, 52, 7), pygame.Rect(17, 25, 19, 31), pygame.Rect(17, 25, 19, 31),
                        pygame.Rect(12, 32, 28, 16), pygame.Rect(12, 32, 28, 16), pygame.Rect(12, 32, 28, 16), pygame.Rect(12, 32, 28, 16)]
    colCenter = (19, 42)
    color = (255, 0, 0)  
    def __init__(self, mainObj, position, yon=4, layer=0, attrDict={}):
        self.type = 'Kurt'
        Unit.__init__(self, mainObj, position, yon, attrDict)

        self.image = self.changeImage('Kurt', yon) # Oyunun başında ilk yüklenen unit resim dosyasi
        self.rect = self.image.get_rect()
        self.rect.topleft = position
        self.layer = layer # LayeredUpdates grubu için gerekiyor
        
        self.colRect = copy(Kurt.colRect[self.yon])
        self.colRect.topleft = (self.colRect.topleft[0] + self.rect.topleft[0], self.colRect.topleft[1] + self.rect.topleft[1])
        
        # çarpışmalarda kullanılan noktalar
        self.colPoints = None
        
        self.tolerans = 0
        self.speed = 4
        
        if self.player.type == Player.human_player:
            self.ai = KurtFSM(self, human=True)
        else:
            self.ai = KurtFSM(self)
        
        # unit'in gerçek pozisyonunu (reel sayılarla) tutar. rect'e atılırken int'e dönüştürülür.
        self.yer = Vector2(*self.colRect.center)

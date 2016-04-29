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
import game_events
from random import randrange
from logging import basicConfig, DEBUG, ERROR, debug

basicConfig(level=DEBUG, filename="debuglogs.txt",
                    format="[%(levelname)s] %(module)s - %(funcName)s, (%(asctime)s) \n\t \n\t   %(message)s\
                    \n -------------------------------------------------------",
                    datefmt="%m-%d-%y, %H:%M")
basicConfig(level=ERROR, filename="errorlogs.txt",
                    format="[%(levelname)s] %(module)s - %(funcName)s, (%(asctime)s) \n\t \n\t   %(message)s \
                    \n -------------------------------------------------------",
                    datefmt="%m-%d-%y, %H:%M")

class BaseFSM(object):
    # States
    # patrol, basic_chase, evade, attack
    
    # Conditions
    # enemy_near, enemy_reached, enemy_died, enemy_strong, enemy_far
    
    def __init__(self, sprite, human):
        self.sprite = sprite
        self.human = human
        self.enemy = None
        self.mainObj = sprite.mainObj
        self.show = self.mainObj.screenManager.showScreen
        self.condition = None
        self.table = None
        self.reached, self.near, self.far = None, None, None
        self.attackTime = None
        
    def __getstate__(self):
        odict = self.__dict__.copy() # copy the dict since we change it

        del odict['mainObj']
        del odict['show']
        del odict['sprite']
        del odict['enemy']
        del odict['condition']
        del odict['table']
        del odict['attackTime']
        print odict
    
        return odict
        
    def setMoving(self):
        self.condition = self.move
        
    def setAttack(self):
        self.condition = self.attack
        
    def setChase(self):
        self.condition = self.basic_chase
        
    def execute(self):
        # condition'a uyan satırları al
        rows = [row for row in self.table if row[0] == self.condition]
        
        # sırayla koşullara bak, uyan varsa condition'ı değiştir
        for row in rows:
            # o durumun fonksiyonunu çalıştır
            row[0]()
            # istenen koşul sağlandıysa durum değiş
            if row[1]():
                self.condition = row[2]
                break
            
    # FUNCTIONS -------------------------------------------------------------------------------
            
    def patrol(self):
        pass
    
    def move(self):
        """ To understand where unit's base is, relative positioning shouldn't be used, because of sliding. """
        from units.unit import Vector2
        center = self.sprite.colRect.center
        self.base = (Vector2(*self.show.position) + Vector2(*center)).toTuple()

    def getBase(self):
        from units.unit import Vector2
        return (Vector2(*self.base) - Vector2(*self.show.position)).toTuple()
        
    def basic_chase(self):
        """ basit hedefi takip etme. """
        self.sprite.hedef = self.enemy.colRect.center
        self.sprite.moveTo(self.enemy.colRect.center)
        
    def turn_base(self):
        """ basit hedefi takip etme. """
        try:
            base = self.getBase()
        except:
            pass
    
    def evade(self):
        """ basic_chase gibi çalışır fakat ters yöne kaçmayı sağlar. """
        
        direction = self.sprite.setDirection(self.enemy.colRect.center)
        direction = direction * -1 # kaçış yönünü veriyor
        
        konum = self._randomPosition(direction)
        while self.show.whereAmI(konum) == (-1, -1):
            konum = self._randomPosition(direction)
        
        self.sprite.moveTo(konum)
            
    def _randomPosition(self, direction):
        if direction.x >= self.enemy.colRect.center[0]:
            randomx = randrange(self.enemy.colRect.center[0], self.mainObj.resolutionX)
        if direction.x < self.enemy.colRect.center[0]:
            randomx = randrange(0, self.enemy.colRect.center[0])
        
        if direction.y >= self.enemy.colRect.center[1]:
            randomy = randrange(self.enemy.colRect.center[1], self.mainObj.resolutionY)
        if direction.y < self.enemy.colRect.center[1]:
            randomy = randrange(0, self.enemy.colRect.center[1])
            
        return (randomx, randomy)
    
    def attack(self):
        from game_classes import Timer
        
        if self.attackTime and self.attackTime.finished():
            self.mainObj.eventManager.add(game_events.AttackEvent(self.mainObj, self.sprite, self.enemy))
            
            # debug("atmainObjtack time: " + str(self.attackTime.neKadarGecti()))
            self.enemy.health -= randrange(self.attackPower)
            # debug("enemy health %d" % self.enemy.health)
            if self.enemy.health <= 0:
                self.enemy.health = 0
                self.mainObj.eventManager.add(game_events.DestroyEvent(self.mainObj, self.enemy))
                self.enemy.kill()
                self.enemy = None
                
            self.attackTime.setTimer(0.5)
        elif not self.attackTime:
            self.attackTime = Timer(0.5)
    
    # CONDITIONS -------------------------------------------------------------------------------
    
    def enemy_range(self, range, base=False):
        """ yakında enemy olabilecek unit varsa onu enemy yapar. """
        try:
            merkez = self.getBase()
            rect = pygame.Rect((merkez.x, merkez.y), (0, 0))
        except AttributeError:
            merkez = self.sprite.colRect.center
            rect = pygame.Rect(merkez, (0, 0))
        rect.inflate_ip(range, range)
        
        for player in self.mainObj.players:
            if player == self.sprite.player:
                continue
            
            for sprite in player.units:
                if rect.colliderect(sprite.colRect):
                    self.enemy = sprite
                    return True
        
        return False
    
    def stopped(self):
        return not self.mainObj.movingUnits.has(self.sprite)
    
    def enemy_reached(self):
        merkez = self.sprite.colRect.center
        rect = pygame.Rect(merkez, (0, 0))
        rect.inflate_ip(self.reached, self.reached)
        
        return rect.colliderect(self.enemy.colRect)
    
    def enemy_near(self):
        return self.enemy_range(self.near)
    
    def enemy_near_base(self):
        return self.enemy_range(self.near, base=True)
    
    def enemy_far(self):
        return not self.enemy_range(self.far)
    
    def enemy_far_base(self):
        return not self.enemy_range(self.far, base=True)
    
    def enemy_evading(self):
        return not self.enemy_reached()
     
    def enemy_died(self):
        return not self.enemy
    
    def enemy_strong(self):
        """ aradaki oran 2 ise enemy güçlüdür. """
        return self.enemy.health > 10 and self.enemy.health / (self.sprite.health + 0.1) >= 2
    
    def true(self):
        return True
    
    def false(self):
        return False
    
class KurtFSM(BaseFSM):
    humanAggressive, humanDefensive, humanStandGround, humanNoAttack = range(4)
    
    def __init__(self, sprite, human=False):
        BaseFSM.__init__(self, sprite, human)
        self.condition = self.patrol
        
        if self.human:
            self.table = self.humanDefensive()
        else:
            self.mode = "CPUAggressive"
            self.table = [[self.patrol,      self.enemy_near,      self.basic_chase],
                          [self.basic_chase, self.enemy_reached,   self.attack],
                          [self.basic_chase, self.enemy_far,       self.patrol],
                          [self.attack,      self.enemy_died,      self.patrol],
                          [self.attack,      self.enemy_evading,   self.basic_chase],
                          [self.attack,      self.enemy_strong,    self.evade],
                          [self.evade,       self.true,            self.move],
                          [self.move,        self.stopped,         self.patrol]]
            
        # uzaklıklar
        self.reached, self.near, self.far = 30, 500, 900
        
        # nesne özellikleri
        self.attackPower = 10 # randoma sokulacak
        
        self.execute()
        
    def setMode(self, mode):
        modes = {KurtFSM.humanAggressive: self.humanAggressive, KurtFSM.humanDefensive: self.humanDefensive, KurtFSM.humanStandGround: self.humanStandGround, KurtFSM.humanNoAttack: self.humanNoAttack}
        self.table = modes[mode]()
        self.condition = self.patrol
        
    def humanAggressive(self):
        """ Enemy'yi öldürünceye kadar kovalar. Attack bir oyun. """
        
        self.near = 500
        self.mode = "Aggressive"
        
        #        current,          condition,            next
        return [[self.patrol,      self.enemy_near,      self.basic_chase],
                [self.basic_chase, self.enemy_reached,   self.attack],
                [self.attack,      self.enemy_died,      self.patrol],
                [self.attack,      self.enemy_evading,   self.basic_chase],
                [self.move,        self.stopped,         self.patrol]]
        
    def humanDefensive(self):
        """ Eğer range içindeyse saldırır, range dışına çıktıysa ilk konumuna geri döner. """
        
        self.near = 250
        self.far = 250
        self.mode = "Defensive"
        
        #        current,          condition,            next
        return [[self.patrol,      self.enemy_near_base, self.basic_chase],
                [self.basic_chase, self.enemy_far_base,  self.turn_base],
                [self.basic_chase, self.enemy_reached,   self.attack],
                [self.attack,      self.enemy_died,      self.turn_base],
                [self.attack,      self.enemy_evading,   self.basic_chase],
                [self.turn_base,   self.true,            self.move],
                [self.move,        self.stopped,         self.patrol]]
        
    def humanStandGround(self):
        """ Unit hiç kımıldamaz, ama range içindeyse saldırır. """
        #        current,          condition,              next
        self.near = 30
        self.mode = "Stand Ground"
        
        return [[self.patrol,      self.enemy_near_base,   self.attack],
                [self.attack,      self.enemy_died,        self.patrol],
                [self.attack,      self.enemy_evading,     self.patrol],
                [self.move,        self.stopped,           self.patrol]]
        
    def humanNoAttack(self):
        """ Unit hiç kımıldamaz ve saldırmaz. """
        
        self.mode = "No Attack"
        
        #        current,          condition,            next
        return [[self.move,        self.stopped,         self.patrol]]

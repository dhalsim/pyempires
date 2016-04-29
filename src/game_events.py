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

from time import time
from datetime import datetime
from logging import basicConfig, DEBUG, ERROR
from units.unit import findAngle, Vector2
import game_screens
from game_classes import Timer
from game_players import Player
import pygame

""" Local veya Remote Olay Modülüdür. Amacı oyun içi veya oyunlar arası haberleşmeler.
    Kullanımı: Oyunun yapısına göre EventManager single veya network olarak kurulur. 
    Yapılması gereken bir iş olduğunda gerekli olay nesnesi oluşturulur, EventManager'a gönderilir. """


basicConfig(level=DEBUG, filename="debuglogs.txt",
                    format="[%(levelname)s] %(module)s - %(funcName)s, (%(asctime)s) \n\t \n\t   %(message)s\
                    \n -------------------------------------------------------",
                    datefmt="%m-%d-%y, %H:%M")
basicConfig(level=ERROR, filename="errorlogs.txt",
                    format="[%(levelname)s] %(module)s - %(funcName)s, (%(asctime)s) \n\t \n\t   %(message)s \
                    \n -------------------------------------------------------",
                    datefmt="%m-%d-%y, %H:%M")

class EventManager(object):
    """ Tüm event'lerin yaratılması, toplanması ve işletilmesinden sorumlu sınıftır. """
    SinglePlay = 0
    NetworkPlay = 1
    firstTimeList = [-1, -1, -1, -1] # MouseMoveEvent için kullanılan zaman listesi
    doubleTime = Timer(0) # static time attribute for double clicking
    
    def __init__(self, mainObj, type):
        self.mainObj = mainObj
        self.gameType = type
        self.eventList = []
        
    def add(self, event):
        """ EventManager'a event eklenir. """ 
        self.eventList.append(event)
        
    def control(self, list=None):
        """ EventManager'da event var mı? Ayrıca zamanlama işleri de halledilir. """
        # ekran = self.mainObj.screenManager

        # MouseMoveEvent için zamanlama kısmı
        if self.mainObj.screenManager.showScreen == self.mainObj.screenManager.gameScreen:
            wait = 0 # kaydırma işleminin olması için beklenen zaman
            for i, t in enumerate(EventManager.firstTimeList):
                if t != -1 and time() - t >= wait:
                    self.mainObj.screenManager.showScreen.setPosition(i)
                    EventManager.firstTimeList[i] = time()
        
        # Event var mı
        if list != None:
            liste = list
        else:
            liste = self.eventList
        
        if len(liste) > 0:
            return True
        else:
            return False
        
    def handleEvent(self):
        """ EventManager'da ilk Event işlenir/gönderilir. """
        if self.control():
            if self.gameType == EventManager.SinglePlay:
                self.eventList[0].execute()
            else:
                self.send(self.eventList[0])
            del self.eventList[0]
    
    def getEvents(self, eventType=None):
        if eventType:
            return filter(lambda e: type(e) == eventType, self.eventList)
        else:
            return self.eventList
    
    def handleEvents(self, eventType=None):
        """ EventManager'daki tüm Event'ler işlenir/gönderilir. """
        eventList = self.getEvents(eventType)
        
        while self.control(eventList):
            eventList[0].execute()
            del eventList[0]
    
    def clear(self):
        """ Tüm eventler silinir. """
        self.eventList = None
        
    def send(self, event):
        """ Will be implemented for network play """
        pass



class BaseEvent(object):
    """ Tüm Event sınıfları bu sınıftan miras alır. """
    def __init__(self, mainObj):
        self.mainObj = mainObj
        
    def execute(self):
        """ Olay olduğunda yapılması gereken işler. Override edilmeli. """

        
class LocalEvent(BaseEvent):
    """ Oyun içindeki MouseEvent, KeyEvent, MenuEvent gibi yerel olaylar bu sınıftan miras alır. """
    def __init__(self, mainObj):
        BaseEvent.__init__(self, mainObj)
        self.map = self.mainObj.resourceManager.keys
        
class MouseDownEvent(LocalEvent):
    """ Mouse hareketi ve tıklamaları durumunda oluşturulup çalıştırılır. """
    def __init__(self, mainObj, button=None, m_pos=None):
        LocalEvent.__init__(self, mainObj)
        self.button = button
        self.mousePosition = m_pos
        
    def execute(self):
        ekran = self.mainObj.screenManager
        
        if self.button == 1: # sol
            if ekran.showScreen == ekran.gameScreen:
                ekran.showScreen.secimStartPoint = self.mousePosition
                ekran.showScreen.secim = True
                ekran.showScreen.secimCiz(self.mousePosition)
                
class MouseUpEvent(LocalEvent):
    """ Mouse hareketi ve tıklamaları durumunda oluşturulup çalıştırılır. """
    def __init__(self, mainObj, button=None, m_pos=None):
        LocalEvent.__init__(self, mainObj)
        self.button = button
        self.mousePosition = m_pos
        
    def execute(self):
        ekran = self.mainObj.screenManager
        show = ekran.showScreen
        mp = self.mousePosition
        
        if self.button == 1: # sol
            
            # Double Click implementation
            # If a click happens twice in same coordinates and without delayin much
            # a doubleClick event will be triggered
            
            if EventManager.doubleTime.finished():
                # it missed it, or it will be first, anyway it will be reset
                EventManager.doubleTime = Timer(0.25, mc=mp)
            else:
                # it hasn't finished yet, but need to control coordinates
                if mp == EventManager.doubleTime.mc:
                    self.mainObj.eventManager.add(DoubleClickEvent(self.mainObj, mp))
            
            if show == ekran.gameScreen:
                # eğer seçim dörtgeni çizimi olmamışsa, sadece o noktadakiler seçilecek
                if show.secimStartPoint == mp:
                    for sprite in self.mainObj.units:
                        if sprite.rect.collidepoint(mp):
                            nokta = mp[0] - sprite.rect.topleft[0], mp[1] - sprite.rect.topleft[1]
                            if sprite.mask.get_at(nokta) != 0:
                                self.mainObj.players[0].addTo("selectedUnits", sprite)
                        elif self.mainObj.players[0].selectedUnits.has(sprite):
                            self.mainObj.players[0].removeFrom("selectedUnits", sprite)
                
                show.secim = False
            else:
                for sprite in self.mainObj.fonts:
                    if sprite.rect.collidepoint(mp):
                        self.mainObj.eventManager.add(MenuEvent(self.mainObj, sprite.key))
                
        elif self.button == 2: # orta
            if show == ekran.gameScreen:
                show.terminal.tmpEkle('orta tus: ', mp)
        
        elif self.button == 3: # sağ
            if show == ekran.gameScreen and len(self.mainObj.players[0].selectedUnits) > 0:
                
                for sprite in self.mainObj.players[0].selectedUnits:
                    if sprite.player in self.mainObj.enemyPlayers:
                        continue
                    
                    if show.whereAmI(mp) != (-1, -1):
                        if self.mainObj.attackTo:
                            sprite.ai.setAttack()
                            sprite.ai.enemy = self.mainObj.attackTo
                            sprite.ai.base = sprite.ai.enemy.colRect.center
                        else:
                            sprite.moveTo(mp)
                            sprite.ai.setMoving()

class DoubleClickEvent(LocalEvent):
    """ Double click event, based on two MouseUpEvents with a timer. """
    
    def __init__(self, mainObj, m_pos):
        LocalEvent.__init__(self, mainObj)
        self.mousePosition = m_pos
        
    def execute(self):
        ekran = self.mainObj.screenManager
        show = ekran.showScreen
        mp = self.mousePosition
        
        if show == ekran.gameScreen:
            for spt in self.mainObj.players[0].units:
                if spt.rect.collidepoint(self.mousePosition):
                    nokta = mp[0] - spt.rect.topleft[0], mp[1] - spt.rect.topleft[1]
                    if spt.mask.get_at(nokta):
                        # select every unit of that kind
                        spt.player.empty("selectedUnits")
                        spt.player.addTo("selectedUnits", spt.player.__getattribute__("unit_" + spt.type).sprites())
        
class MouseMoveEvent(LocalEvent):
    """ Mouse hareketi ve tıklamaları durumunda oluşturulup çalıştırılır. """
    
    def __init__(self, mainObj, m_pos):
        LocalEvent.__init__(self, mainObj)
        self.mousePosition = m_pos
        
    def execute(self):
        """ Menülerde başlıkların üstüne gelince renk değiştirme,
        oyun içinde seçim dörtgeninin çizimi ve
        haritanın kaydırılması gibi işleri yapar.
        Kaydırma işleminde waitFor sn'lik bekleme süresi vardır. """
        
        ekran = self.mainObj.screenManager
        eMan = self.mainObj.eventManager
        
        if ekran.showScreen == ekran.startScreen or ekran.showScreen == ekran.gameMenuScreen:
            for sprite in self.mainObj.fonts:
                if sprite.rect.collidepoint(self.mousePosition):
                    sprite.setColor(game_screens.BaseScreen.onColor)
                else:
                    sprite.setColor(game_screens.BaseScreen.color)
        
        elif ekran.showScreen == ekran.gameScreen and ekran.showScreen.secim:
            ekran.showScreen.secimCiz(self.mousePosition)
        
        elif ekran.showScreen == ekran.gameScreen:
            mp = self.mousePosition
            show = ekran.showScreen
            
            
            # SCROLLING-------------------------------------------------------------------
            s = 0
            # aşağı
            if mp[1] == self.mainObj.resolutionY - 1:
                # ilk giriş
                if eMan.firstTimeList[s] == -1:
                    eMan.firstTimeList[s] = time()
            else:
                # zamanı resetle
                eMan.firstTimeList[s] = -1
                
            s += 1
            # yukarı
            if mp[1] == 0: 
                if eMan.firstTimeList[s] == -1:
                    eMan.firstTimeList[s] = time()
            else:
                eMan.firstTimeList[s] = -1
                
            s += 1
            
            # sola
            if mp[0] == 0: 
                if eMan.firstTimeList[s] == -1:
                    eMan.firstTimeList[s] = time()
            else:
                eMan.firstTimeList[s] = -1
            
            s += 1
            
            # sağa
            if mp[0] == self.mainObj.resolutionX - 1:
                if eMan.firstTimeList[s] == -1:
                    eMan.firstTimeList[s] = time()
            else:
                eMan.firstTimeList[s] = -1
                
            # ATTACK CURSOR--------------------------------------------------------------
            for plyr in self.mainObj.enemyPlayers:
                for spr in plyr.units:
                    if spr.rect.collidepoint(mp):
                        nokta = mp[0] - spr.rect.topleft[0], mp[1] - spr.rect.topleft[1]
                        if spr.mask.get_at(nokta):
                            pygame.mouse.set_cursor(*pygame.cursors.broken_x)
                            self.mainObj.attackTo = spr # MouseUpEvent'te kullanılacak 
                            return
            
            pygame.mouse.set_cursor(*pygame.cursors.arrow)
            self.mainObj.attackTo = None
             
class KeyboardUpEvent(LocalEvent):
    """ Keyboardda bir tuşun basılıp kaldırılması durumunda oluşturulur. """
    def __init__(self, mainObj, key, mod=pygame.KMOD_NONE):
        LocalEvent.__init__(self, mainObj)
        self.key = key
        self.mod = mod
        
    def execute(self):
        from game_ai import KurtFSM
        from game_classes import Key
        
        ekran = self.mainObj.screenManager
        show = ekran.showScreen
        
        key = Key(self.key, self.mod)
                
        # Escape Key
        if key == self.map["esc"]:
            if show == ekran.startScreen:
                self.mainObj.eventManager.add(DisconnectEvent(self.mainObj, self.mainObj.humanPlayer))
                self.mainObj.stop()
                
            else:
                show.saveMusic()
                ekran.setScreen(show.previousScreen)
                show.playMusic()

        # Set Attack Modes
        if key == self.map["a"] or key == self.map["s"] or key == self.map["d"] or key == self.map["f"]:
            for sprite in self.mainObj.players[0].selectedUnits:
                if sprite.player.id != self.mainObj.humanPlayer.id:
                    continue
                
                if key == self.map["a"]:
                    sprite.ai.setMode(KurtFSM.humanAggressive)
                elif key == self.map["s"]:
                    sprite.ai.setMode(KurtFSM.humanDefensive)
                elif key == self.map["d"]:
                    sprite.ai.setMode(KurtFSM.humanStandGround)
                elif key == self.map["f"]:
                    sprite.ai.setMode(KurtFSM.humanNoAttack)
        
        # Select or create groups 
        for i in xrange(1,10):
            # Selecting groups
            if key == Key(eval("pygame.K_" + str(i))):
                self.mainObj.players[0].empty("selectedUnits")
                self.mainObj.players[0].addTo("selectedUnits", self.mainObj.players[0].ctrl.__getitem__(i))
            # Creating groups
            if key == Key(eval("pygame.K_" + str(i)), pygame.KMOD_LCTRL):
                group = self.mainObj.players[0].__getattribute__("ctrl").__getitem__(i)
                group.empty()
                group.add(self.mainObj.players[0].selectedUnits)
        
        # add units during gameplay
        keyss = ["+", "-", "*"]
        for i, k in enumerate(keyss):
            if key == self.map[k]:
                attributes = {"health": 100, "player": self.mainObj.players[i]}
                self.mainObj.addObject('Kurt', None, iteration=1, attrDic=attributes)
                
        # select only one sprite
        if key == self.map["space"]:
            selected = self.mainObj.players[0].selectedUnits.sprites()[0]
            self.mainObj.players[0].empty("selectedUnits")
            self.mainObj.players[0].addTo("selectedUnits", selected)              
             
class KeyboardDownEvent(LocalEvent):
    """ Keyboardda bir tuşun basılıp kaldırılması durumunda oluşturulur. """
    def __init__(self, mainObj, key, mod=pygame.KMOD_NONE):
        LocalEvent.__init__(self, mainObj)
        self.key = key
        self.mod = mod
        
    def execute(self):
        from game_classes import Key
        
        ekran = self.mainObj.screenManager
        show = ekran.showScreen
        
        key = Key(self.key, self.mod)
        # scrolling
        if show == self.mainObj.screenManager.gameScreen:
            if key == self.map["up"]:
                show.setPosition(game_screens.GameScreen.up)
            elif key == self.map["down"]:
                show.setPosition(game_screens.GameScreen.down)
            elif key == self.map["right"]:
                show.setPosition(game_screens.GameScreen.right)
            elif key == self.map["left"]:
                show.setPosition(game_screens.GameScreen.left)

                       
class MenuEvent(LocalEvent):
    """ Menülerde tıklama olayları. """
    def __init__(self, mainObj, menuItem):
        LocalEvent.__init__(self, mainObj)
        self.menuItem = menuItem

    def execute(self):
        ekran = self.mainObj.screenManager
        oldScreen = ekran.showScreen
        ekran.setScreen(ekran.showScreen.nextScreen[self.menuItem])
        
        if self.menuItem == 'newGame':
            if oldScreen == ekran.gameMenuScreen:
                for name, group in self.mainObj.groups.items(): #@UnusedVariable
                    group.empty()
            
            attributes = {"health": 100, "player": self.mainObj.players[0]}
            self.mainObj.addObject('Kurt', None, iteration=2, attrDic=attributes)
            attributes = {"health": 100, "player": self.mainObj.players[2]}
            self.mainObj.addObject('Kurt', None, iteration=1, attrDic=attributes)
            
            sprts = self.mainObj.walls.sprites()
            lyrs = self.mainObj.walls.layers()
            
            for spr, lyr in zip(sprts, lyrs):
                self.mainObj.all.add(spr, layer=lyr)
            
            #ekran.showScreen.konum = [0, 0]
            
        elif self.menuItem == 'saveGame':
            oldScreen.saveGameScreen()
            ekran.gameScreen.terminal.tmpEkle('save', 'oyun kaydedildi')
        
        elif self.menuItem == 'loadGame':
            ekran.gameMenuScreen.loadGameScreen()
            ekran.showScreen.terminal.tmpEkle('load', 'oyun yuklendi')
            
        elif self.menuItem == 'quitGame':
            self.mainObj.eventManager.add(DisconnectEvent(self.mainObj, self.mainObj.humanPlayer))
            self.mainObj.stop()

class RemoteEvent(BaseEvent):
    """ 
    Paylaşılması gereken single-play veya network-play olaylarının üst sınıfıdır. 
    MoveEvent, DeleteEvent, CreateEvent, DestroyEvent, LoseEvent, WinEvent, DisconnectEvent, AttackEvent, FinishAttackEvent """
    def __init__(self, mainObj, player):
        BaseEvent.__init__(self, mainObj)
        self.player = player
        
class MoveEvent(RemoteEvent):
    """ Nesne'nin hareket etmesi olayı. """
    def __init__(self, mainObj, sprite, oldRect, newRect, newColRect):
        RemoteEvent.__init__(self, mainObj, sprite.player)
        self.sprite = sprite
        self.oldRect = oldRect
        self.newRect = newRect
        self.colRect = newColRect
        
    def execute(self):
        if self.mainObj.units.has(self.sprite):
            show = self.mainObj.screenManager.showScreen
            ne = show.whereAmI(self.colRect.bottomright)
            self.sprite.layer = ne[0] * show.mapW + ne[1]

class DeleteEvent(RemoteEvent):
    """ Nesne'nin silinmesi olayı. """
    def __init__(self, mainObj, deletedObj):
        RemoteEvent.__init__(self, mainObj, deletedObj.player)
        self.deletedObj = deletedObj
        
    def execute(self):
        pass

class CreateEvent(RemoteEvent):
    """ Nesne'nin yaratılması olayı. """
    def __init__(self, mainObj, createdObj):
        RemoteEvent.__init__(self, mainObj, createdObj.player)
        self.createdObj = createdObj
        
    def execute(self):
        pass

class DestroyEvent(RemoteEvent):
    """ Nesne'nin yok edilmesi olayı. """
    def __init__(self, mainObj, destroyedObj):
        RemoteEvent.__init__(self, mainObj, destroyedObj.player)
        self.destroyedObj = destroyedObj
        
    def execute(self):
        # player group'ta başka unit kalmamışsa o player oyunu kaybetmiştir
        
        if len(self.player.all) == 0:
            self.mainObj.eventManager.add(LoseEvent(self.mainObj, self.player))
    
class LoseEvent(RemoteEvent):
    """ 
    Oyunu kaybeyme olayı. Tüm unit ve building'ler DestroyEvent, DeleteEvent durumunda 
    veya kullanıcının DisconnectEvent durumunda. """
    def __init__(self, mainObj, player):
        RemoteEvent.__init__(self, mainObj, player)
        
    def execute(self):
        print "%d oyuncusu yenildi. %s" % (self.player.id, datetime.today().strftime("%d/%m/%y %H:%M"))
        
        """
        # oyun kaybedildi
        if self.player.id == self.mainObj.humanPlayer.id:
            self.mainObj.pause()
            lose = self.mainObj.resourceManager.lose
            show = self.mainObj.screenManager.showScreen
            rect = lose.get_rect()
            rect.
            show.Surface.blit(lose, )
        """
        
class WinEvent(RemoteEvent):
    """ Kendi dışındaki tüm kullanıcıların LoseEvent durumuna gelmesi durumunda. """
    def __init__(self, mainObj, player):
        RemoteEvent.__init__(self, mainObj, player)
        
    def execute(self):
        pass
    
class DisconnectEvent(RemoteEvent):
    """ Oyuncunun oyundan çıkması olayı. """
    def __init__(self, mainObj, player):
        RemoteEvent.__init__(self, mainObj, player)
        
    def execute(self):
#        debug("topmost sprite is: " + str(self.mainObj.all.get_top_sprite()))
#        debug("top layer: %d" % self.mainObj.all.get_top_layer())
#        debug("bottom layer: %d" % self.mainObj.all.get_bottom_layer())
#        debug("layers: %s" % str(self.mainObj.all.layers))
        print self.player.id, "oyuncusu oyundan ayrıldı."
        
class AttackEvent(RemoteEvent):
    """ Oyuncunun bir düşmana saldırması olayı. """
    def __init__(self, mainObj, attackerObj, attackToObj):
        RemoteEvent.__init__(self, mainObj, attackToObj.player)
        self.attackerObj = attackerObj
        self.attackToObj = attackToObj
        yon = Vector2(*attackToObj.colRect.center).from_point(attackerObj.colRect.center)
        attackerObj.setImageDirection(findAngle(yon.x, yon.y))
        
    def execute(self):
        pass
    
class FinishAttackEvent(RemoteEvent):
    """ Oyuncunun bir nesneye saldırıyı kesmesi olayı. """
    def __init__(self, mainObj, attackToObj):
        RemoteEvent.__init__(self, mainObj, attackToObj.player)
        self.attackToObj = attackToObj
        
    def execute(self):
        pass


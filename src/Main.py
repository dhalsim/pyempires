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


from pygame.sprite import Group
import game_events
import game_screens
import game_classes
import pygame
from random import randrange
from pygame.locals import QUIT, MOUSEMOTION, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from game_players import Player
from game_constants import SONG_FINISHED_EVENT, ADD_OBJECTS, SHOW_CONSOLE, TILE_NUMBER_X, TILE_NUMBER_Y, TILE_SIZE
from logging import basicConfig, debug, DEBUG, ERROR
from copy import copy

basicConfig(level=DEBUG, filename="debuglogs.txt",
                    format="[%(levelname)s] %(module)s - %(funcName)s, (%(asctime)s) \n\t \n\t   %(message)s\
                    \n -------------------------------------------------------",
                    datefmt="%m-%d-%y, %H:%M")
basicConfig(level=ERROR, filename="errorlogs.txt",
                    format="[%(levelname)s] %(module)s - %(funcName)s, (%(asctime)s) \n\t \n\t   %(message)s\
                    \n -------------------------------------------------------",
                    datefmt="%m-%d-%y, %H:%M")

class Main(object):
    all, units, selectedUnits, movingUnits, buildings, ai, tempConsoleFonts, consoleFonts = range(8)
    
    def __init__(self):
        # 0: çalış, 1: dur, 2: pause
        self.stopthread = 0
        # used for KEYPRESS events in handleEvents
        self.keyup = True
                
        # Oyuncular
        self.players = [Player(self, 0, type=Player.human_player), Player(self, 1), Player(self, 2)]
        self.humanPlayer = filter(lambda player: player.type == Player.human_player, self.players)[0]
        self.enemyPlayers = filter(lambda player: player.type == Player.cpu_player, self.players)
        # Müzik ayarları
        pygame.mixer.pre_init(44100, -16, 2, 1024*4)
        pygame.mixer.init()  
        
        # Kaynakların yüklenmesi
        self.resourceManager = None
        
        # Groups ------
        #    GameScreen    
        self.all = pygame.sprite.LayeredUpdates() # tüm şekiller (update için)
        self.units = pygame.sprite.RenderUpdates()
        self.selectedUnits = pygame.sprite.OrderedUpdates()
        self.movingUnits = pygame.sprite.RenderUpdates()
        self.buildings = pygame.sprite.RenderUpdates()
        self.ai = pygame.sprite.Group()
        #    Conditionları yazdırmak için
        self.conditions = pygame.sprite.RenderUpdates()
        self.walls = pygame.sprite.LayeredUpdates()
        #    StartScreen, GameMenuScreen menüleri için
        self.fonts = pygame.sprite.RenderUpdates()
        #    Terminal yazıları için
        self.tempConsoleFonts = pygame.sprite.OrderedUpdates()
        self.consoleFonts = pygame.sprite.OrderedUpdates()
        #     groups dict for GameScreen
        
        # Ekran bilgileri
        self.maxfps = 0
        self.minfps = 100
        pygame.init()
        self.displayInfo = pygame.display.Info()
        self.resolutionX = pygame.display.list_modes(32, pygame.FULLSCREEN)[0][0]
        self.resolutionY = pygame.display.list_modes(32, pygame.FULLSCREEN)[0][1]
        self.resolution = (self.resolutionX, self.resolutionY)                           
        
        # Ekranlar
        self.screenManager = game_screens.ScreenManager(self)
        self.screenManager.createAllScreens()
        self.screenManager.setScreen(self.screenManager.startScreen)
        
        # Olaylar
        self.eventManager = game_events.EventManager(self, game_events.EventManager.SinglePlay)
        self.update = False
        self.attackTo = None # sağ click olayında kullanılacak unit'i tutar
        self.saat = pygame.time.Clock()
        
    def _randomPosition(self, spriteType, yon):
        show = self.screenManager.showScreen
        position = (randrange(self.resolutionX), randrange(self.resolutionY))
        # debug("randomdan gelen: " + str(position))
        spriteClass = eval("game_classes." + spriteType)
        colRect = copy(spriteClass.colRect[yon])
        # debug("colRect orijinal: " + str(colRect))
        colRect.topleft = (colRect.topleft[0] + position[0], colRect.topleft[1] + position[1])
        # debug("colRect değişmiş: " + str(colRect))
        
        li = [colRect.topleft, colRect.bottomleft, colRect.topright, colRect.bottomright]
        for l in li:
            nerede = show.whereAmI(l)
            # debug("whereAmI %s: %s" % (str(l), str(nerede)))
            if nerede == (-1, -1) or show.map[nerede[0]][nerede[1]] != "grass":
                # debug("hatali")
                return False
        
        # debug("uygundur: " + str(position))
        return position

    def addObject(self, spriteType, positionTuple, yon=None, iteration=5, attrDic={}):
        """
        Verilen parametrelere uygun iteration kadar aynı sprite'ı yaratır.
        Yeni nesne yaratmada kullanılmalıdır. Load işlemi için addObjests methodunu kullanın.
        
        spriteType -- Sprite hangi class ise o gruba aittir. ör: kurt.
        positionList -- Her sprite'ın orijin noktasını içerir. iteration kadar elemanı olmalıdır. 
            Eğer None ise yaratılan sprite'ların position'ları random ayarlanır. 
        player -- Sprite hangi oyuncuya eklencekse onun grubu.
        group -- Yeni sprite yaratımında units veya building gruplarından biri yazılmalıdır.
        yon -- Sprite class içindeki yön bilgisi. ör: asagi.
        iteration -- aynı sprite kaç kere yaratılacak. """
        
        if ADD_OBJECTS:
            for i in xrange(iteration): 
                if not yon:
                    # make a random direction
                    yon2 = randrange(8)
                if positionTuple:
                    position = positionTuple[i]
                # random positioning
                else:
                    position = self._randomPosition(spriteType, yon2)
                    # debug("ilk pozisyon: " + str(position))
                    while not position:
                        position = self._randomPosition(spriteType, yon2)
                        # debug("dönen sonuç: " + str(position))
                
                # debug("kabul edilen position: " + str(position))
                sprite = self.resourceManager.spriteClass(spriteType, self, position, yon2, attrDict=attrDic)
                self.all.add(sprite, layer=self.getLayer(sprite.colRect))
        #
        # debug("hello")
    def addObjects(self, spriteTypeTuple, positionTuple, groupsTuple, yonTuple):
        """ 
        Verilen listelerdeki sprite'ları bir daha oluşturur. Load işlemleri için kullanılır.
        Tüm listeler aynı boyutta olmalıdır. groupsList sprite'ın içinde olduğu tüm grupları vermektedir. """
        
        if ADD_OBJECTS:
            for i in xrange(len(spriteTypeTuple)):
                sprite = self.resourceManager.spriteClass(spriteTypeTuple[i], self, positionTuple[i], yonTuple[i])
                for g in groupsTuple:
                    g.add(sprite)
                          
    def getLayer(self, rect):
        """ rect'in hangi layer'a denk geldiğini döndürür. """
        show = self.screenManager.showScreen
        tupl = show.whereAmI(rect.bottomright)
        return tupl[0] * show.mapW + tupl[1]
    
    def run(self):
        while True:
            if not self.stopthread:
                self.saat.tick(30)
                self.handleEvents()
                self.redrawAll()
            elif self.stopthread == 2:
                pass
            else:
                pygame.quit()
                return

    def stop(self):
        self.stopthread = 1
        
    def pause(self):
        self.stopthread = 2
        
    def play(self):
        self.stopthread = 0

    def redrawAll(self):
        show = self.screenManager.showScreen
        show.execute()
        self.changes = []
        
        if show == self.screenManager.startScreen or show == self.screenManager.gameMenuScreen:
            self.fonts.clear(show.Surface, show.backgroundSurface)
            self.changes.extend(self.fonts.draw(show.Surface))
        else:
            # çizimden önceki temizlik işleri
            ortak = [sprite for sprite in self.movingUnits.sprites() if self.selectedUnits.has(sprite)]
            for sprite in ortak:
                sprite.update("clear")
            
            # eski seçim bölgesi, arkaplan basılarak temizleniyor
            if show.secim and show.secimRectOld:
                show.Surface.blit(show.backgroundSurface.subsurface(show.secimRectOld), show.secimRectOld)
                self.changes.append(show.secimRectOld)
            
            # oyun nesneleri yenileniyor, çeşitli görevler
            self.all.clear(show.Surface, show.backgroundSurface)
            self.changes.extend(self.all.draw(show.Surface))
            self.movingUnits.update("move")
            self.conditions.empty()
            self.ai.update("ai")
            
            # yeni seçim için çizim yapılıyor
            if show.secim and show.secimRect:
                pygame.draw.rect(show.Surface, show.color, show.secimRect, 1)
                self.changes.append(show.secimRect)
                show.secimRectOld = copy(show.secimRect)
            
            # seçim nesneleri
            if show.secim:
                for unit in self.units:
                    if show.secimRect.colliderect(unit.rect):
                        if not self.selectedUnits.has(unit):
                            unit.player.addTo("selectedUnits", unit)
                    else:
                        if self.selectedUnits.has(unit):
                            unit.player.removeFrom("selectedUnits", unit)
                            unit.update("clear")

            # son temizlik (mouseButtonUp)
            elif show.secimRect:
                show.Surface.blit(show.backgroundSurface.subsurface(show.secimRect), show.secimRect)
                self.changes.append(show.secimRect)
                
                # oyun nesneleri çiziliyor
                self.movingUnits.update("draw")
                self.all.clear(show.Surface, show.backgroundSurface)
                self.changes.extend(self.all.draw(show.Surface))
                            
            # oyun console çıktıları çiziliyor
            if SHOW_CONSOLE:
                self.consoleFonts.clear(show.Surface, show.backgroundSurface)
                self.changes.extend(self.consoleFonts.draw(show.Surface))    
                self.tempConsoleFonts.clear(show.Surface, show.backgroundSurface)
                self.changes.extend(self.tempConsoleFonts.draw(show.Surface))
                # conditions 
                self.conditions.clear(show.Surface, show.backgroundSurface)
                self.changes.extend(self.conditions.draw(show.Surface))  
        
            self.selectedUnits.update("draw")
            
        if self.update:
            pygame.display.flip()
            self.update = False
        else:
            pygame.display.update(self.changes)
        
    def handleEvents(self):
        m_pos = pygame.mouse.get_pos()
        m_pos_x = int(m_pos[0])
        m_pos_y = int(m_pos[1])
        m_pos = (m_pos_x, m_pos_y)
        
        pygame.event.pump()
        for event in pygame.event.get():
            # QUIT----------------------------------------------------------------------------
            if event.type == QUIT:
                self.eventManager.add(game_events.DisconnectEvent(self, self.humanPlayer))
                self.stop()
            
            # MOUSEMOTION---------------------------------------------------------------------
            elif event.type == MOUSEMOTION:
                self.eventManager.add(game_events.MouseMoveEvent(self, event.pos))
                 
            # KEYUP---------------------------------------------------------------------------
            elif event.type == KEYUP:
                self.keyup = True
                self.eventManager.add(game_events.KeyboardUpEvent(self, event.key, event.mod))

            # MOUSEBUTTONDOWN-----------------------------------------------------------------
            elif event.type == MOUSEBUTTONDOWN:
                self.eventManager.add(game_events.MouseDownEvent(self, event.button, m_pos))

            # MOUSEBUTTONUP-------------------------------------------------------------------
            elif event.type == MOUSEBUTTONUP:
                self.eventManager.add(game_events.MouseUpEvent(self, event.button, m_pos))

            # SONG_FINISHED_EVENT-------------------------------------------------------------
            elif event.type == SONG_FINISHED_EVENT:
                self.screenManager.showScreen.playMusic()
                
        # KEYPRESS---------------------------------------------------------------------------
        # with this events we can use for making groups (CTRL + NUM)
        # if not pressed with CTRL, then that number will select the appropriate group
        # map is the keyboard configuration map dictionary read from keyboard.xml
        map = self.resourceManager.readKeyboardMap()
        
        for i in xrange(10):
            k = eval("pygame.K_" + str(i))
            if pygame.key.get_pressed()[k] and self.keyup:
                self.keyup = False
                mods = pygame.key.get_mods()
                self.eventManager.add(game_events.KeyboardUpEvent(self, k, mods))
                # to check mods: mods & pygame.KMOD_LCTRL:
        
        # for scrolling map, use the arrow keys...
        arrow_keys = ["up", "down", "right", "left"]
        for arrow in arrow_keys:
            k = map[arrow]
            if pygame.key.get_pressed()[k.key]:
                self.eventManager.add(game_events.KeyboardDownEvent(self, k.key, k.mod))
        self.eventManager.handleEvents()
        
if __name__ == "__main__":
    gui = Main()
    gui.run()

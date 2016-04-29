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
import pygame

from game_players import Player
from game_screens import BaseScreen
from textures.text import Text, Terminal

from copy import copy
from math import atan2, degrees
from logging import basicConfig, debug, DEBUG, ERROR

basicConfig(level=DEBUG, filename="debuglogs.txt",
                    format="[%(levelname)s] %(module)s - %(funcName)s, (%(asctime)s) \n\t \n\t   %(message)s\
                    \n -------------------------------------------------------",
                    datefmt="%m-%d-%y, %H:%M")
basicConfig(level=ERROR, filename="errorlogs.txt",
                    format="[%(levelname)s] %(module)s - %(funcName)s, (%(asctime)s) \n\t \n\t   %(message)s \
                    \n -------------------------------------------------------",
                    datefmt="%m-%d-%y, %H:%M")
                    
def findAngle(x, y):
    """ Finds Y/X's angle. """
    # convert sdl coordinate system to cartesian
    y_ = y * -1
    angle = degrees(atan2(y_, x))
    if angle < 0:
        angle += 360
        
    return angle

class Unit(pygame.sprite.Sprite, object):
    healthColor = (0, 255, 0)
    healthRect = pygame.Rect(0, 0, 50, 5)
    
    def __init__(self, mainObj, position, yon, attrDict):
        pygame.sprite.Sprite.__init__(self)
        
        self.mainObj = mainObj
        self.position = position
        
        # unit attributes
        self.health = None
        self.healthRect = pygame.Rect(0, 0, 50, 5)
        self.setAttributes(attrDict)
        self.setGroups()
        
        # gidilmesi gereken birim vektör
        self.direction = None
        
        # resimin yönünü tutar
        self.yon = yon
        
        # Vector2d list from A* -near to far-
        self.path = []
        self.hedef = None # path için gidilecek yer
        
        self.colRect = None # miras edinilen sınıfta eklenecek
        self.oldRect = None # selection box silinmesi için gerekli
        
        # condition yazdırmak için
        self.condition = None
        
    def __getstate__(self):
        odict = self.__dict__.copy()    # copy the dict since we change it
        del odict['image']              # remove surface entry
        del odict['mainObj']            # remove mainObj
        del odict['condition']          # remove Text surface
        del odict['mask']               # remove mask
        del odict['ai']                 # remove ai
        return odict

    def __setstate__(self, dict):
        self.__dict__.update(dict)   # update attributes
        # bkz: loadGameScreen
        
    def _randomPosition(self, direction, unit, uzaklik=50):
        if direction.x >= unit.colRect.center[0]:
            randomx = randrange(unit.colRect.center[0], unit.colRect.center[0] + uzaklik)
        if direction.x < unit.colRect.center[0]:
            randomx = randrange(unit.colRect.center[0] - uzaklik, unit.colRect.center[0])
        
        if direction.y >= unit.colRect.center[1]:
            randomy = randrange(unit.colRect.center[1], unit.colRect.center[1] + uzaklik)
        if direction.y < unit.colRect.center[1]:
            randomy = randrange(unit.colRect.center[1] - uzaklik, unit.colRect.center[1])
            
        return (randomx, randomy)
        
        
    def setAttributes(self, dic):
        for k, v in dic.items():
            self.__setattr__(k, v)
            
    def setGroups(self):
        # local groups
        self.add(self.player.all, self.player.units, self.player.ai, eval("self.player.unit_" + self.type))
        # global groups, except self.mainObj.all because it needs layer property
        self.add(self.mainObj.units, self.mainObj.ai)
        
    def changeImage(self, unit, yon):
        """ Returns image of unit. """
        images = getattr(self.mainObj.resourceManager, unit)
        self.yon = yon
        image = images[self.player.id][yon]
        self.mask = pygame.mask.from_surface(image)
        return image
        
    def moveTo(self, hedef):
        """ Nesne hareketinin ilk başladığı fonksiyon budur. kaynak ve hedef koordinatlar belirlenir,
            destination ve source tile'lar belirlenir, path oluşturulur. Nesne movingUnits'e eklenir. """
        
        """ A* algoritmasını kullanarak path'ı ayarlar """
        show = self.mainObj.screenManager.showScreen
        
        self.path = []
        self.hedef = list(hedef) # koordinat
        
        self.destination = show.whereAmI(hedef) # tile
        self.source = show.whereAmI(self.colRect.center)  # tile
        
        self.player.addTo("movingUnits", self)
        self.findPath()
        
        #debug("bulunan path: " + str(self.path))
        
    def getPath(self, source, destination):
        """ A-star algoritmasının çalıştığı method. """
        map = self.mainObj.screenManager.showScreen.map
        
        self.opened, self.closed = [], []
        self.opened.append(Node(None, source, destination, 0))
        while len(self.opened) > 0:
            best = min(self.opened, key=lambda node: node.f_score)
            self.opened.remove(best)
            self.closed.append(best)
            if best.koords == destination:
                return best
            else:
                adjacents = self.getAdjacents(*best.koords)
                for adj in adjacents:
                    if map[adj[0]][adj[1]] == "sand":
                        cost = 2
                    else:
                        cost = 1
                    node = Node(best, adj, destination, best.g_score + 1 * cost)
                    if (node in self.opened or node in self.closed):
                        continue
                    self.opened.append(node)
        return False
        
    def findPath(self):
        """ self.path listesi atanıyor. Eğer path bulunuyorsa ilk direction oluşturulur. """
        target = self.getPath(self.source, self.destination)
        self.updateControl()
        
        if not target:
            # temizlik
            self.path = []
            self.player.removeFrom("movingUnits", self)
            return False
        else:
            self.path = self.constructPath(target)
            show = self.mainObj.screenManager.showScreen
            # ekrana path'ı göstermek için kullanılabilir.
            # show.path = self.path
            # show.updateBackground()
            
        if self.path:
            show = self.mainObj.screenManager.showScreen
            eg = show.getMapRect(self.path[0]).center
            self.direction = self.setDirection(eg)
        else:
            self.direction = self.setDirection(self.hedef)

    def setDirection(self, hedefKoor):
        """ self.direction vektör'ünü !in_place! oluşturur. """
        
        direction = Vector2(*hedefKoor).from_point(self.colRect.center)
        direction.normalize()
        #debug("yeni direction: " + str(self.direction))
        return direction
         
    def constructPath(self, target):
        """ path'ın tersi alınması işlemi. """
        
        path = []
        while target.koords != self.source: # bu şekilde source tile eklenmiyor, gerek yok
            path.append(target.koords)
            target = target.parent
        path.reverse()
        # son tile'ın path'a eklenmesine gerek yok, self.hedef zaten onu karşılıyor
        path and path.pop()
        return path
    
    def getAdjacents(self, x, y):
        show = self.mainObj.screenManager.showScreen
        adj = [(x-1, y), (x, y-1), (x+1, y), (x, y+1), (x-1, y-1), (x+1, y+1), (x+1, y-1), (x-1, y+1)]
        
        # filtering only suitable tiles which are kept within borders, and passable ways
        
                     # position is within the borders
        adj = filter(lambda koor: koor[0] >= 0 and koor[1] >= 0 and koor[0] < show.mapH and koor[1] < show.mapW 
                     # that tile is not a wall
                     and not (show.map[koor[0]][koor[1]].startswith("wall") or show.map[koor[0]][koor[1]].startswith("water"))
                     # travers tiles are not between wall or water tile
                     and not (show.map[koor[0]][y].startswith("wall") or show.map[koor[0]][y].startswith("water")) 
                     and not (show.map[x][koor[1]].startswith("wall") or show.map[x][koor[1]].startswith("water")), adj)

        return adj
    
    def updateControl(self):
        """ update - move işlemi için gerekli değerleri hesaplar. """
        show = self.mainObj.screenManager.showScreen
        self.vRect = Vector2(*self.colRect.center)
        hedef = Vector2(*self.hedef)
        
        if self.path:
            mevki = show.getMapRect(self.path[0]).center
            self.vMevki = Vector2(*mevki)
            self.vHedef = self.vMevki
            #debug("path var, hedef: " + str(self.vHedef))
        else:
            self.vHedef = hedef
            #debug("path yok hedef: " + str(self.vHedef))
            
        #debug("rect center: %s \nyer: %s" % (str(self.vRect), str(self.yer)))
        
    def update(self, *args):
        """ draw: objeyi seçmek için, rect bölgesine 1 kalınlığında color renginde rect çizer.
            move: objenin hareketinden sorumlu. """
        
        show = self.mainObj.screenManager.showScreen
        
        # seçili nesnelerin etrafına rect çizer
        if "draw" in args:
            if self.mainObj.selectedUnits in self.groups():
                # dış çerçeve için
                copyHealthRect = copy(Unit.healthRect)
                copyHealthRect.center = self.rect.center
                copyHealthRect.move_ip(0, -1 * self.rect.height // 2)
                
                self.healthRect.width = round(Unit.healthRect.width * (self.health / 100.))
                self.healthRect.topleft = copyHealthRect.topleft
                
                pygame.draw.rect(show.Surface, BaseScreen.onColor, copyHealthRect)
                pygame.draw.rect(show.Surface, Unit.healthColor, self.healthRect)
                pygame.draw.rect(show.Surface, BaseScreen.color, copyHealthRect, 1)
                
                self.mainObj.changes.append(copyHealthRect)
                self.oldRect = copy(copyHealthRect)
        
        # seçili nesnenin arkaplanının temizlenmesi
        elif "clear" in args:
            screen_rect = pygame.Rect((0, 0), self.mainObj.resolution)
            clipping_rect = self.oldRect.clip(screen_rect)
            sub_surface = show.backgroundSurface.subsurface(clipping_rect)
            show.Surface.blit(sub_surface, clipping_rect)
                
        elif "move" in args:
            # hareket et
            # debug("direction is: " + str(self.direction))
            
            # collision var mı? varsa evade
            for unit in self.mainObj.units:
                if unit == self:
                    continue
                if self.colRect.colliderect(unit.colRect):
                    # self.update("evade", unit)
                    # hedef'e uzaklık colRect'in hipotenüsünden azsa dur
                    """
                    width = self.colRect.width
                    height = self.colRect.height
                    hipo = round(math.sqrt(width * width + height * height))
                    if (Vector2(*self.hedef) - self.vRect).get_magnitude() < hipo :
                        self.player.removeFrom("movingUnits", self)
                    return
                    """
            
            show = self.mainObj.screenManager.showScreen
            tile_xy = show.whereAmI((self.vRect.x, self.vRect.y))
            
            # cost = (speed on grass - speed on X)
            if show.map[tile_xy[0]][tile_xy[1]] == "sand":
                cost = 1. # 2 - 1
            else:
                cost = 0;
            
            # moving and jobs to be done after that    
            self.move(self.direction.x, self.direction.y, self.speed - cost)
            
            
            # gerekli değişkenlerin oluşturulması
            self.updateControl()

            if self.vRect.yaklasik(self.vHedef, self.tolerans):
                #debug("hedeflerden birine vardık")
                if self.path:
                    self.path.pop(0)
                    #debug("path vardı sildim")
                
                if self.vHedef == Vector2(*self.hedef):
                    #debug("path yoktu, demek hedefe varmışız, çık")
                    self.player.removeFrom("movingUnits", self)
                    
                self.updateControl()
                self.direction = self.setDirection(self.vHedef.toTuple())
                
        elif "evade" in args:
            direction = self.setDirection(args[1].colRect.center)
            direction = direction * -1 # kaçış yönünü veriyor
            
            konum = self._randomPosition(direction, args[1], uzaklik=50)
            while show.whereAmI(konum) == (-1, -1):
                konum = self._randomPosition(direction, args[1], uzaklik=50)
            
            self.path.insert(0, konum)
        
        # scroll map olayında nesnelerin ve path.hedef'in kaydırılması
        elif "slide" in args:
            # map scroll işlemlerinden dolayı
            self.rect.move_ip(*args[1])
            self.colRect.center = self.rect.center
            self.yer += Vector2(*args[1])
            if self.hedef:
                self.hedef[0] += args[1][0];self.hedef[1] += args[1][1]
        
        # cpu tipi oyuncuların sprite'ları için yapay zeka
        elif "ai" in args:   
            self.ai.execute()
            font = self.mainObj.resourceManager.xfont
            rect = copy(self.rect)
            rect.move_ip(0, -10)
            s = self.ai.mode + ":" + str(self.ai.condition).split("KurtFSM.")[1].split()[0]
            
            self.condition = Text(font, s, "", rect.topleft, Terminal.color, Terminal.bgcolor)
            self.mainObj.conditions.add(self.condition)
            
    def setImageDirection(self, angle):
        """ Sets the unit's image to a right directioned one. """
        
        # must import all units
        from kurt import Kurt
        
        if  22.5 <= angle < 67.5: #northeast
            self.image = self.changeImage(self.type, eval(self.type).yukari_sag)
            self.colPoints = [self.colRect.topright, self.colRect.topleft]
        if  67.5 <= angle < 112.5: #north
            self.image = self.changeImage(self.type, eval(self.type).yukari)
            self.colPoints = [self.colRect.topright, self.colRect.topleft]
        if  112.5 <= angle < 157.5: #northwest
            self.image = self.changeImage(self.type, eval(self.type).yukari_sol)
            self.colPoints = [self.colRect.topright, self.colRect.topleft]
        if  157.5 <= angle < 202.5: #west
            self.image = self.changeImage(self.type, eval(self.type).sol)
            self.colPoints = [self.colRect.bottomleft, self.colRect.topleft]
        if  202.5 <= angle < 247.5: #southwest
            self.image = self.changeImage(self.type, eval(self.type).asagi_sol)
            self.colPoints = [self.colRect.bottomright, self.colRect.bottomleft]
        if  247.5 <= angle < 292.5: #south
            self.image = self.changeImage(self.type, eval(self.type).asagi)
            self.colPoints = [self.colRect.bottomright, self.colRect.bottomleft]
        if  292.5 <= angle < 337.5: #southeast
            self.image = self.changeImage(self.type, eval(self.type).asagi_sag)
            self.colPoints = [self.colRect.bottomright, self.colRect.bottomleft]
        if  337.5 <= angle <= 360 or 0 <= angle < 22.5: #east
            self.image = self.changeImage(self.type, eval(self.type).sag)
            self.colPoints = [self.colRect.bottomright, self.colRect.topright]
    
    def move(self, x, y, speed=1):
        """ Birim vektör hareketi, sprite'ın değişmesi ve collision'dan sorumludur. """
        #debug("moving %d, %d with speed %d" % (x,y,speed))
        
        # must import all units
        from kurt import Kurt
        from game_events import MoveEvent
        
        for sp in xrange(int(round(speed))):
            #yedekColRect = copy(self.colRect)
            #self.colRect.move_ip(x, y)
            
            # çarpışma olursa geri almak veya image değişimlerinden kaynaklanan colRect sapmaları için yedek
            yedekRect = copy(self.colRect)

            angle = findAngle(x, y)
            self.setImageDirection(angle)
            self.colRect.center = yedekRect.center
            
            mycolrect = eval(self.type).colRect[self.yon] 
            self.rect.topleft = self.colRect.topleft[0] - mycolrect.topleft[0], self.colRect.topleft[1] - mycolrect.topleft[1]
  
            # units arasında colRect çarpışması var mı? kendisinden dolayı len - 1 bakıyoruz.
            # if len(pygame.sprite.spritecollide(self, self.mainObj.units, False, collide_rect)) > 0:
            #     return
            # else:
                # self.yer de değişiklik yapıp bunu rect'e atıyoruz
                
            self.yer += Vector2(x, y)
            self.colRect.center = (round(self.yer.x), round(self.yer.y))
            
            self.updateControl()
            self.direction = self.setDirection(self.vHedef.toTuple())
            
            if self.vRect.yaklasik(self.vHedef, self.tolerans):
                return
        
        self.mainObj.eventManager.add(MoveEvent(self.mainObj, self, yedekRect, self.rect, self.colRect))
        if self.mainObj.all.has(self):
            # debug("moving, new layer is: " + str(self.mainObj.getLayer(self.colRect)))
            self.mainObj.all.change_layer(self, self.mainObj.getLayer(self.colRect))
            
class Vector2(object):
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y
    
    def from_point(self, n1):
        return Vector2(self.x - n1[0], self.y - n1[1])
    
    @classmethod
    def vector2_from_points(self, n1, n2):
        return cls(n1[0] - n2[0], n1[1] - n2[1])

    def __str__(self):
        return "(%s, %s)" % (self.x, self.y)
    
    def get_magnitude(self):
        return math.sqrt( self.x**2 + self.y**2 )
    
    def normalize(self):
        """ birim hız. """
        magnitude = self.get_magnitude()
        try:
            self.x /= magnitude
            self.y /= magnitude
        except:
            self.x = self.y = 0
        
    def toTuple(self):
        return (self.x, self.y)

    def __add__(self, rhs):
        return Vector2(self.x + rhs.x, self.y + rhs.y)
    
    def __sub__(self, rhs):
        return Vector2(self.x - rhs.x, self.y - rhs.y)
    
    def __neg__(self):
        return Vector2(- self.x, - self.y)
    
    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)
      
    def __div__(self, scalar):
        return Vector2(self.x / scalar, self.y / scalar)
    
    def __abs__(self):
        return Vector2(abs(self.x), abs(self.y))
    
    def __eq__(self, v):
        return self.x == v.x and self.y == v.y
    
    def __gt__(self, v):
        return self.get_magnitude() > v.get_magnitude()
    
    def __ge__(self, v):
        return self > v or self == v
    
    def __lt__(self, v):
        return self.get_magnitude() < v.get_magnitude()
    
    def __le__(self, v):
        return self < v or self == v
    
    def yaklasik(self, v, deger):
        """ koordinatları karşılaştırırken, iki koordinat arası farkın, 
        deger kadar yanılma payına kadar doğru döndürür. """
        fark = abs(self - v)
        return fark <= Vector2(deger + 1, deger + 1) 
    
class Node(object):
    """ A-star'da kullanılan, düğümün g_score, h_score gibi bilgilerini tutan class. """
    
    # heuristic methods
    EUGLIAN, MANHATTAN = 0, 1
    
    # costs of the node
    GRASS, SAND = (1, 1.5)
    
    def __init__(self, parent, koords, destination, g_score):
        self.parent = parent
        self.koords = koords
        self.h_score = self.getHeuristic(koords, destination, method=Node.MANHATTAN)
        self.g_score = g_score
        self.f_score = self.h_score + self.g_score
        
    def __eq__(self, n):
        if n.koords == self.koords:
            return 1
        else:
            return 0
        
    @staticmethod
    def getHeuristic(koords, destination, method, type=1):
        x_ = abs(koords[0] - destination[0])
        y_ = abs(koords[1] - destination[1])    
        if method == Node.EUGLIAN:
            return math.sqrt(x_ ** y_)
        elif method == Node.MANHATTAN:
            return x_ + y_
        else:
            return False
     

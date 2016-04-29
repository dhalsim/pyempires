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


import shelve
import os
import pygame
import random
from copy import copy
from textures.wall import Wall
from textures.text import Text
from textures.text import Terminal
from game_players import Player
from game_ai import KurtFSM
from game_constants import PLAY_MUSIC, SONG_FINISHED_EVENT, DISPLAY_FLAGS
from logging import basicConfig, debug, DEBUG, ERROR

basicConfig(level=DEBUG, filename="debuglogs.txt",
					format="[%(levelname)s] %(module)s - %(funcName)s, (%(asctime)s) \n\t \n\t   %(message)s\
					\n -------------------------------------------------------",
					datefmt="%m-%d-%y, %H:%M")
basicConfig(level=ERROR, filename="errorlogs.txt",
					format="[%(levelname)s] %(module)s - %(funcName)s, (%(asctime)s) \n\t \n\t   %(message)s \
					\n -------------------------------------------------------",
					datefmt="%m-%d-%y, %H:%M")

class ScreenManager(object):
	""" creates screens, and makes transitions between screens. """
	
	StartScreen, GameScreen, GameMenuScreen = range(3)
	def __init__(self, mainObj):
		self.mainObj = mainObj
		self.startScreen = None
		self.gameScreen = None
		self.gameMenuScreen = None
		self.showScreen = self.startScreen
	
	def createScreen(self, screen):
		""" Create a certain screen. """
		if screen == ScreenManager.StartScreen:
			self.startScreen = StartScreen(self.mainObj, name="Game", musicPath="../resources/music")
			self.startScreen.initLinks()
		elif screen == ScreenManager.GameScreen:
			self.gameScreen = GameScreen(self.mainObj, name="Game", musicPath="../resources/music/game")
			self.gameScreen.initLinks()
		elif screen == ScreenManager.GameMenuScreen:
			self.gameMenuScreen = GameMenuScreen(self.mainObj, name="Game", musicPath="../resources/music")
			self.gameMenuScreen.initLinks()
			
	def createAllScreens(self):
		""" Create all screens. """
		self.startScreen = StartScreen(self.mainObj, name="Game", musicPath="../resources/music")
		self.gameScreen = GameScreen(self.mainObj, name="Game", musicPath="../resources/music/game")
		self.gameMenuScreen = GameMenuScreen(self.mainObj, name="Game", musicPath="../resources/music")
		
		self.startScreen.initLinks()
		self.gameMenuScreen.initLinks()
		self.gameScreen.initLinks()
		
	def delScreen(self, screen):
		if screen == ScreenManager.startScreen:
			del self.startScreen
		elif screen == ScreenManager.gameScreen:
			del self.gameScreen
		elif screen == ScreenManager.gameMenuScreen:
			del self.gameMenuScreen
	
	def delAllScreens(self):
		del self.startScreen
		del self.gameScreen
		del self.gameMenuScreen
		
	def setScreen(self, screen):
		""" Changes the screen to be displayed, if there is no screen application will end. """
		if not screen:
			self.mainObj.stop()
		else:
			self.mainObj.fonts.empty()
			self.showScreen = screen
			self.showScreen.clear()
			self.showScreen.paint()
			pygame.display.update() 

class BaseScreen(object):
	""" All other screen classes inherits from this. It's most methods will be overriden. """
	background = (255, 255, 255)
	color = (0, 0, 0)
	onColor = (255, 0, 0)
	
	def __init__(self, mainObj, name="Game", musicPath="../resources/music"):
		self.mainObj = mainObj
		self.screen = mainObj.screenManager
		self.name = name
		self.musicPath = musicPath
		pygame.font.init()
		self.font = pygame.font.Font('../resources/menu.ttf', 25)
		
		# music
		pygame.mixer.music.set_endevent(SONG_FINISHED_EVENT)
		self.musicList = filter(lambda a: os.path.splitext(a)[1] == ".mp3" or os.path.splitext(a)[1] == ".ogg" or os.path.splitext(a)[1] == ".wav", os.listdir(self.musicPath))
		self.musicTime = 0.0
		self.musicNo = 0
		random.shuffle(self.musicList)
		self.playMusic()
		
		# screen

		self.Surface = pygame.display.set_mode(self.mainObj.resolution, DISPLAY_FLAGS)
		self.Surface.fill(BaseScreen.background)
		pygame.display.set_caption(name)
		
	def clear(self):
		self.Surface.blit(self.backgroundSurface, (0, 0))
		
	def playMusic(self):
		""" is used for music playing. After the song finished, it will go on from the playlist.
		If song is cut, it will resume from that point. """
		if PLAY_MUSIC:
			if not self.musicTime == 0.0:
				if len(self.musicList) - 1 == self.musicNo:
					self.musicNo = 0
				else:
					self.musicNo += 1
					
				if self.musicList: 
					pygame.mixer.music.load(os.path.join(self.musicPath, self.musicList[self.musicNo]))
					pygame.mixer.music.play(1)
			else:
				if self.musicList: 
					pygame.mixer.music.load(os.path.join(self.musicPath, self.musicList[self.musicNo]))
					pygame.mixer.music.play(1, round(self.musicTime / 1000))
			
	def saveMusic(self):
		if PLAY_MUSIC:
			self.musicTime = pygame.mixer.music.get_pos()
			
	def paint(self):
		""" Must be implemented. """
		pass
	
	def execute(self):
		""" Must be implemented. """
		pass
	

class StartScreen(BaseScreen):
	""" This is a Start Screen which have New Game, Save Game, Load Game, Exit items. """
	def __init__(self, mainObj, name="Game", musicPath="../resources/music"):
		BaseScreen.__init__(self, mainObj, name, musicPath)
		self.backgroundSurface = pygame.Surface(self.mainObj.resolution)
		self.backgroundSurface.fill(self.background)
		self.Surface.blit(self.backgroundSurface, (0, 0))

	def initLinks(self):
		# Links
		self.previousScreen = None
		self.nextScreen = {}
		self.nextScreen['newGame'] = self.screen.gameScreen
		self.nextScreen['loadGame'] = self.screen.gameScreen
		self.nextScreen['quitGame'] = None
		
	def paint(self):
		self.mainObj.fonts.add(Text(self.font, u'NEW GAME', 'newGame', (10, 10), BaseScreen.color))
		self.mainObj.fonts.add(Text(self.font, u'LOAD GAME', 'loadGame', (10, 40), BaseScreen.color))
		self.mainObj.fonts.add(Text(self.font, u'EXIT GAME', 'quitGame', (10, 70), BaseScreen.color))

class GameMenuScreen(BaseScreen):
	""" Game Menu Screen. """
	def __init__(self, mainObj, name="Game", musicPath="../resources/music"):
		BaseScreen.__init__(self, mainObj, name, musicPath)
		self.backgroundSurface = pygame.Surface(self.mainObj.resolution)
		self.backgroundSurface.fill(self.background)
		self.Surface.blit(self.backgroundSurface, (0, 0))
	
	def initLinks(self):
		# Links
		self.previousScreen = self.screen.gameScreen
		self.nextScreen = {}
		self.nextScreen['newGame'] = self.screen.gameScreen
		self.nextScreen['saveGame'] = self.screen.gameScreen
		self.nextScreen['loadGame'] = self.screen.gameScreen
		self.nextScreen['quitGame'] = None
		
	def paint(self):
		self.mainObj.fonts.add(Text(self.font, u'NEW GAME', 'newGame', (10, 10), BaseScreen.color))
		self.mainObj.fonts.add(Text(self.font, u'SAVE GAME', 'saveGame', (10, 40), BaseScreen.color))
		self.mainObj.fonts.add(Text(self.font, u'LOAD GAME', 'loadGame', (10, 70), BaseScreen.color))
		self.mainObj.fonts.add(Text(self.font, u'EXIT GAME', 'quitGame', (10, 100), BaseScreen.color))
		
	def saveGameScreen(self):
		file = shelve.open('save.dat')
		file['all'] = self.mainObj.all.sprites()
		
		"""
		file['ai'] = self.mainObj.ai.sprites()
		file['selectedUnits'] = self.mainObj.selectedUnits.sprites()
		file['movingUnits'] = self.mainObj.movingUnits.sprites()
		"""
		
		file['players'] = self.mainObj.players
		print self.mainObj.players
		file['playerGroups'] = self.mainObj.playerGroups
		file.close()
	
	def loadGameScreen(self):
		for sprite in self.mainObj.all:
			sprite.kill()
			
		for value in self.mainObj.groups.values():
			value.empty()
		
		file = shelve.open('save.dat')
		self.mainObj.all.add(file['all'])
		
		"""
		self.mainObj.ai.add(file['ai'])
		self.mainObj.selectedUnits.add(file['selectedUnits'])
		self.mainObj.movingUnits.add(file['movingUnits'])
		"""
		
		"""
		self.mainObj.players = file['players']
		print "players", self.mainObj.players
		self.mainObj.playerGroups = file['playerGroups']
		print "playerGroups", self.mainObj.playerGroups
		self.mainObj.humanPlayer = self.mainObj.players[0]
		print "humanPlayer", self.mainObj.humanPlayer
		"""
		
		# add removed features
		for sprite in self.mainObj.all:
			sprite.mainObj = self.mainObj
			if sprite.type == 'Kurt': # or is it another Unit?
				sprite.image = sprite.changeImage(sprite.type, sprite.yon)
			
				if sprite.player.type == Player.human_player:
					sprite.ai = KurtFSM(sprite, human=True)
				else:
					sprite.ai = KurtFSM(sprite)
			elif sprite.type == 'Wall':
				sprite.image = self.mainObj.resourceManager.wall
			
			"""
			for gr in sprite.groups():
				print gr
				gr.add(sprite)
			"""
			
		file.close()


class GameScreen(BaseScreen):
	""" Game Screen. """
	color = (0, 0, 255)
	background = (255, 255, 255)

	# map directions
	down, up, left, right = range(4)
	
	def __init__(self, mainObj, name="Game", musicPath="../resources/music"):
		BaseScreen.__init__(self, mainObj, name, musicPath)
		self.map = self.readMap("../resources/map1.map");
		
		# Load Resources
		from game_classes import ResourceManager
		self.mainObj.resourceManager = ResourceManager(self.mainObj)
		
		# Map Height, Map Width
		self.mapH = len(self.map)
		self.mapW = len(self.map[0])
		
		for m in self.map:
			m.reverse()
		
		# Tile Height, Tile Width
		self.tileH = self.mainObj.resourceManager.tile.get_height()
		self.tileW = self.mainObj.resourceManager.tile.get_width()
		
		self.tileMap = [] # tagging tiles with dimensions/positions (i,j)
		
		# Font and game music directory
		self.font = pygame.font.Font("../resources/freemono.ttf", 9)
		self.path = "../resources/music/game"
		
		# Position right now
		self.position = [0, 0]
		
		self.wholeBackgroundSurface = pygame.Surface(self.getMapSize())
		self.wholeBackgroundSurface.fill((255, 255, 255))
		self.blitWhole()
		
		self.backgroundSurface = None # will be blitted with subsurface from self.wholeBackgroundSurface
		self.updateBackground(self.position)
		
		# Terminal
		self.terminal = Terminal(self.mainObj, 4)
				
		# Selection stuff
		self.secimRectOld = None
		self.secimRect = None
		self.secimStartPoint = (0, 0)
		self.secim = False
	
	def initLinks(self): 
		""" Makes link to other screen. """
		self.previousScreen = self.screen.gameMenuScreen
		self.nextScreen = None
			
	def paint(self):
		pass
		
	def execute(self):
		fps = self.mainObj.saat.get_fps()
		if fps > self.mainObj.maxfps:
			self.mainObj.maxfps = fps
		if fps < self.mainObj.minfps and fps > 5:
			self.mainObj.minfps = fps
		
		self.terminal.ekle('fps', fps)
		self.terminal.ekle('maxfps', self.mainObj.maxfps)
		self.terminal.ekle('minfps', self.mainObj.minfps)
		
	def setPosition(self, position):
		""" adjusting self.position with informations comes from MouseMoveEvent. """
		
		slide = 4
		size = self.wholeBackgroundSurface.get_size()
		difference = (size[0] - self.mainObj.resolutionX, size[1] - self.mainObj.resolutionY)
		# debug("difference: " + str(difference))
		old = copy(self.position)
		if position == GameScreen.down:
			debug("old position: " + str(old))
			self.position[1] += slide
			# debug("new position: " + str(self.position))
			# debug("size[1]: " + str(size[1]))
			if self.position[1] > size[1]:
				self.position[1] = size[1]
			if difference[1] <= 0:
				self.position[1] = old[1]
			elif self.position[1] > difference[1]:
				self.position[1] = difference[1]

				
		elif position == GameScreen.up:
			self.position[1] -= slide
			if self.position[1] < 0:
				self.position[1] = 0
			if difference[1] <= 0:
				self.position[1] = old[1]
				
		elif position == GameScreen.left:
			self.position[0] -= slide
			if self.position[0] < 0:
				self.position[0] = 0
			if difference[0] <= 0:
				self.position[0] = old[0]
				
		elif position == GameScreen.right:
			self.position[0] += slide

			if self.position[0] > size[0]:
				self.position[0] = size[0]
			if difference[0] <= 0:
				self.position[0] = old[0]
			elif self.position[0] > difference[0]:
				self.position[0] = difference[0]
			# debug(str(self.position))
		
		if old != self.position:
			# debug("position is changed " + str(self.position))        
			self.updateBackground()
			self.mainObj.all.update("slide", (old[0] - self.position[0], old[1] - self.position[1]))
			self.mainObj.update = True
		
	def updateBackground(self, position=None):
		""" Alternative solution 1:
			Background will be created as a whole, then only the part of which will be seen in screen will be painted.
			position: starting point. """
		if position:
			self.position = position
			
		rect = pygame.Rect((self.position), (self.mainObj.resolution))
		
		try:
			self.backgroundSurface = self.wholeBackgroundSurface.subsurface(rect)
		except ValueError:
			new_rect = rect.clip(self.wholeBackgroundSurface.get_rect())
			self.backgroundSurface = self.wholeBackgroundSurface.subsurface(new_rect)
		self.Surface.blit(self.backgroundSurface, (0, 0))
		
	def blitWhole(self):
		""" creating wholeBackgroundSurface and tileMap. """
		self.tileMap = []
		for i in xrange(self.mapH):
			for j in xrange(self.mapW):
				self._blitMap(i, j)
		
	def _blitMap(self, i, j):
		""" it is used in blitWhole method. """
		tile = self.mainObj.resourceManager.__getattribute__(self.map[i][j])
		x = (i - j) * (self.tileW / 2) + ((self.mapW - 1) * (self.tileW / 2))
		# if object height is more than tileH, it will be slided up to the difference.
		y = (i + j) * (self.tileH / 2) + self.tileH - tile.get_height()
		
		if self.map[i][j].startswith("wall"):
			wall = Wall(self.mainObj, tile, (x, y))
			# debug("wall " + str(wall) + " has level of " + str(i*self.mapW+j))
			self.mainObj.all.add(wall,layer=i*self.mapW+j)
			self.mainObj.walls.add(wall,layer=i*self.mapW+j)
		else:
			self.wholeBackgroundSurface.blit(tile, (x, y))
			# self.wholeBackgroundSurface.blit(random.choice(self.mainObj.resourceManager.tiles), (x, y))

		tile_default = self.mainObj.resourceManager.grass
		x_default = x
		y_default = y = (i + j) * (self.tileH / 2) + self.tileH - tile_default.get_height()
		self.tileMap.append({'rect': pygame.Rect((x_default, y_default), tile_default.get_size()), 'row': i, 'column': j})
	
	def getMapSize(self):
		xsize = self.tileW / 2 * (self.mapW + self.mapH)
		ysize = self.tileH / 2 * (self.mapW + self.mapH)
		return xsize, ysize
	
	def getMapRect(self, tile):
		""" returns a rect of tile. it is translated reverse by self.position. """
		return self.tileMap[tile[0] * self.mapW + tile[1]]['rect'].move(*[aa * -1 for aa in self.position])
	
	def whereAmI(self, position):
		""" it's a method which converts osimetric projection to normal projection.
		it gives the pixel positions of given (x, y) tile position in a map. 
		it makes a comparision check using point's incline, then finds and returns which tile position it is belongs.
		"""	
		
		found = False
		reversePosition = [aa * -1 for aa in self.position]
		
		for t in self.tileMap:
			if t['rect'].move(*reversePosition).collidepoint(position):
				tile_x = t['row']
				tile_y = t['column']
				
				x, y, width, height = t['rect'].move(*reversePosition)
				a = (x, y + height / 2)
				b = (x + width, y + height / 2)
				
				little = 0.1
				if a[0] - position[0] == 0:
					if a[1] > position[1]:
						little = 0.1
					else:
						little = -0.1
				
				mAC = round((a[1] - position[1]) / (a[0] - position[0] + little), 2)
				mCB = round((b[1] - position[1]) / (b[0] - position[0] + little), 2) 
				
				if mAC < -0.5:
					tile_x -= 1
				elif mAC > 0.5:
					tile_y += 1
				elif mCB < -0.5:
					tile_x += 1
				elif mCB > 0.5:
					tile_y -= 1
				
				if tile_x == -1 or tile_y == -1:
					continue
				
				# tile_x is a variable which determines the row, its maximum value is mapH.
				# tile_y is a variable which determines the column, its maximum value is mapW.
				if tile_x >= self.mapH or tile_y >= self.mapW:
					continue
				
				found = True
				return tile_x, tile_y

		if not found:
			return -1, -1

		
	def secimCiz(self, endPoint):
		width, height = endPoint[0] - self.secimStartPoint[0], endPoint[1] - self.secimStartPoint[1]
		myRect = pygame.Rect(self.secimStartPoint, (width, height))
		myRect.normalize()
		self.secimRect = myRect
		
	def readMap(self, mapPath):
		""" Reads a .map file for tiles. """
		f = open(mapPath)
		array = f.readlines()
		lines = list()
		for a in array:
			splitted = a.rstrip().split()
			lines.append(splitted)
			
		return lines
		
		


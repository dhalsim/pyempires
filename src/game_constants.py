
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
from logging import disable, ERROR, DEBUG

DISPLAY_FLAGS = pygame.HWSURFACE #| pygame.FULLSCREEN

SHOW_CONSOLE = True
PLAY_MUSIC = True
ADD_OBJECTS = True
 
TILE_SIZE = 100, 50
TILE_NUMBER_X = 18
TILE_NUMBER_Y = 15
SONG_FINISHED_EVENT = 100

# disables logging less than X level
disable(ERROR)

class MSGS(object):
    CONN_RQEST, CONN_ACCEPTED = range(2)

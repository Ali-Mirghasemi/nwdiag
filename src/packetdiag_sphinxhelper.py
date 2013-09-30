# -*- coding: utf-8 -*-
#  Copyright 2011 Takeshi KOMIYA
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import packetdiag.parser
import packetdiag.builder
import packetdiag.drawer
core = packetdiag

import blockdiag.utils.bootstrap
import blockdiag.utils.collections
import blockdiag.utils.fontmap
utils = blockdiag.utils

from packetdiag.utils.rst import nodes
from packetdiag.utils.rst import directives

# FIXME: obsoleted interface (keep for compatibility)
from blockdiag.utils import collections
from blockdiag.utils.fontmap import FontMap
from packetdiag import command, parser, builder, drawer
from packetdiag.utils.rst.directives import packetdiag, PacketdiagDirective

(collections, FontMap, command, parser, builder, drawer,
 nodes, directives, packetdiag, PacketdiagDirective)

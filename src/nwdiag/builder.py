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

from elements import *
import diagparser
from blockdiag.utils.XY import XY
from blockdiag.utils.namedtuple import namedtuple


class DiagramTreeBuilder:
    def build(self, tree):
        self.diagram = Diagram()
        self.instantiate(None, None, tree)
        for network in self.diagram.networks:
            nodes = [n for n in self.diagram.nodes if network in n.networks]
            if len(nodes) == 0:
                self.diagram.networks.remove(network)

        for i, network in enumerate(self.diagram.networks):
            network.xy = XY(0, i)

        for subgroup in self.diagram.groups:
            if len(subgroup.nodes) == 0:
                self.diagram.groups.remove(subgroup)

        for node in self.diagram.nodes:
            if len(node.networks) == 0:
                msg = "DiagramNode %s does not belong to any networks"
                raise RuntimeError(msg % msg.id)

        return self.diagram

    def instantiate(self, network, group, tree):
        for stmt in tree.stmts:
            if isinstance(stmt, diagparser.Node):
                node = DiagramNode.get(stmt.id)
                node.set_attributes(network, stmt.attrs)

                if group:
                    if node.group and node.group != self.diagram and \
                       group != node.group:
                        msg = "DiagramNode could not belong to two groups"
                        raise RuntimeError(msg)
                    node.group = group
                    group.nodes.append(node)
                elif node.group is None:
                    node.group = self.diagram

                if network not in node.networks:
                    if network is not None:
                        node.networks.append(network)
                if node not in self.diagram.nodes:
                    self.diagram.nodes.append(node)

            elif isinstance(stmt, diagparser.Network):
                subnetwork = Network.get(stmt.id)
                subnetwork.label = stmt.id

                if subnetwork not in self.diagram.networks:
                    self.diagram.networks.append(subnetwork)

                substmt = namedtuple('Statements', 'stmts')([])
                for s in stmt.stmts:
                    if isinstance(s, diagparser.DefAttrs):
                        subnetwork.set_attributes(s.attrs)
                    else:
                        substmt.stmts.append(s)

                self.instantiate(subnetwork, group, substmt)

            elif isinstance(stmt, diagparser.SubGraph):
                subgroup = NodeGroup.get(stmt.id)

                if subgroup not in self.diagram.groups:
                    self.diagram.groups.append(subgroup)

                substmt = namedtuple('Statements', 'stmts')([])
                for s in stmt.stmts:
                    if isinstance(s, diagparser.DefAttrs):
                        subgroup.set_attributes(s.attrs)
                    else:
                        substmt.stmts.append(s)

                self.instantiate(network, subgroup, substmt)

            elif isinstance(stmt, diagparser.Edge):
                nodes = [DiagramNode.get(n) for n in stmt.nodes]
                for node in nodes:
                    if node.group is None:
                        node.group = self.diagram
                    if node not in self.diagram.nodes:
                        self.diagram.nodes.append(node)

                if len(nodes[0].networks) == 0:
                    nw = Network.create_anonymous([nodes[0]])
                    if nw:
                        self.diagram.networks.append(nw)

                for i in range(len(nodes) - 1):
                    nw = Network.create_anonymous(nodes[i:i + 2], stmt.attrs)
                    if nw:
                        self.diagram.networks.append(nw)

            elif isinstance(stmt, diagparser.DefAttrs):
                self.diagram.set_attributes(stmt.attrs)

            else:
                raise AttributeError("Unknown sentense: " + str(type(stmt)))

        return network


class DiagramLayoutManager:
    def __init__(self, diagram):
        self.diagram = diagram

        self.coordinates = []

    def run(self):
        self.do_layout()
        self.diagram.fixiate()

    def do_layout(self):
        self.sort_nodes()
        self.layout_nodes()
        self.set_network_size()

    def sort_nodes(self):
        for i in range(len(self.diagram.nodes)):
            if self.diagram.nodes[i].group:
                n = 1
                basenode = self.diagram.nodes[i]
                group = basenode.group

                for j in range(i + 1, len(self.diagram.nodes)):
                    if basenode.group == self.diagram.nodes[j].group:
                        node = self.diagram.nodes[j]

                        self.diagram.nodes.remove(node)
                        self.diagram.nodes.insert(i + n, node)
                        n += 1

    def layout_nodes(self):
        networks = self.diagram.networks
        last_group = None
        for node in self.diagram.nodes:
            if last_group != node.group:
                if last_group:
                    self.set_coordinates(last_group)
                last_group = node.group

            joined = [g for g in node.networks if g.hidden == False]
            y1 = min(networks.index(g) for g in node.networks)
            if joined:
                y2 = max(networks.index(g) for g in joined)
            else:
                y2 = y1

            if node.group and node.group != self.diagram:
                starts = min(n.xy.x for n in node.group.nodes)
            else:
                nw = [n for n in node.networks if n.xy.y == y1][0]
                nodes = [n for n in self.diagram.nodes if nw in n.networks]
                layouted = [n for n in nodes  if n.xy.x > 0]

                starts = 0
                if layouted:
                    layouted.sort(lambda a, b: cmp(a.xy.x, b.xy.x))
                    basenode = min(layouted)
                    commonnw = set(basenode.networks) & set(node.networks)

                    if basenode.xy.y == y1:
                        starts = basenode.xy.x + 1
                    elif commonnw and \
                         list(commonnw)[0].hidden == True:
                        starts = basenode.xy.x
                    else:
                        starts = basenode.xy.x + 1 - len(nodes)

                if starts < 0:
                    starts = 0

            for x in range(starts, len(self.diagram.nodes)):
                points = [XY(x, y) for y in range(y1, y2 + 1)]
                if not set(points) & set(self.coordinates):
                    node.xy = XY(x, y1)
                    self.coordinates += points
                    break

        if last_group:
            self.set_coordinates(last_group)

    def set_coordinates(self, group):
        self.set_group_size(group)

        xy = group.xy
        for i in range(xy.x, xy.x + group.width):
            for j in range(xy.y, xy.y + group.height):
                self.coordinates.append(XY(i, j))

    def set_network_size(self):
        for network in self.diagram.networks:
            nodes = [n for n in self.diagram.nodes  if network in n.networks]
            nodes.sort(lambda a, b: cmp(a.xy.x, b.xy.x))

            x0 = min(n.xy.x for n in nodes)
            network.xy = XY(x0, network.xy.y)

            x1 = max(n.xy.x for n in nodes)
            network.width = x1 - x0 + 1

    def set_group_size(self, group):
        nodes = list(group.nodes)
        nodes.sort(lambda a, b: cmp(a.xy.x, b.xy.x))

        x0 = min(n.xy.x for n in nodes)
        y0 = min(n.xy.y for n in nodes)
        group.xy = XY(x0, y0)

        x1 = max(n.xy.x for n in nodes)
        y1 = max(n.xy.y for n in nodes)
        group.width = x1 - x0 + 1
        group.height = y1 - y0 + 1


class ScreenNodeBuilder:
    @classmethod
    def build(klass, tree):
        DiagramNode.clear()
        DiagramEdge.clear()
        NodeGroup.clear()
        Network.clear()

        diagram = DiagramTreeBuilder().build(tree)
        DiagramLayoutManager(diagram).run()
        diagram = klass.update_network_status(diagram)

        return diagram

    @classmethod
    def update_network_status(klass, diagram):
        for node in diagram.nodes:
            above = [nw for nw in node.networks  if nw.xy.y <= node.xy.y]
            if len(above) > 1 and [nw for nw in above  if nw.hidden]:
                for nw in above:
                    nw.hidden = False

            below = [nw for nw in node.networks  if nw.xy.y > node.xy.y]
            if len(below) > 1 and [nw for nw in below  if nw.hidden]:
                for nw in below:
                    nw.hidden = False

        return diagram

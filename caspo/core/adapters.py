# Copyright (c) 2014, Santiago Videla
#
# This file is part of caspo.
#
# caspo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# caspo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with caspo.  If not, see <http://www.gnu.org/licenses/>.import random
# -*- coding: utf-8 -*-

from collections import defaultdict

from zope import component

from pyzcasp import asp, potassco

from interfaces import *
from impl import *

class GraphAdapter(object):
    interface.implements(IGraph)
    
    def __init__(self):
        self.graph = Graph()
        
    @property
    def nodes(self):
        return self.graph.nodes
        
    @property
    def edges(self):
        return self.graph.edges

    def predecessors(self, node):
        return self.graph.predecessors(node)


class Sif2Graph(GraphAdapter):
    component.adapts(ISifReader)
    
    def __init__(self, sif):
        super(Sif2Graph, self).__init__()
                
        for source, sign, target in sif:
            sign = int(sign)
            
            self.graph.nodes.add(source)
            self.graph.nodes.add(target)
            self.graph.edges.add((source,target,sign))

class LogicalHeaderMapping2Graph(GraphAdapter):
    component.adapts(ILogicalHeaderMapping)
    
    def __init__(self, header):
        super(LogicalHeaderMapping2Graph, self).__init__()
        
        for m in header:
            clause, target = m.split('=')
            
            self.graph.nodes.add(target)
            for (source, signature) in Clause.from_str(clause):
                self.graph.nodes.add(source)
                self.graph.edges.add((source, target, signature))

class Graph2TermSet(asp.TermSetAdapter):
    component.adapts(IGraph)
    
    def __init__(self, graph):
        super(Graph2TermSet, self).__init__()
        
        for node in graph.nodes:
            self.termset.add(asp.Term('node', [node]))
            
        for source, target, sign in graph.edges:
            self.termset.add(asp.Term('edge', [source, target, sign]))

class Setup2TermSet(asp.TermSetAdapter):
    component.adapts(ISetup)
    
    def __init__(self, setup):
        super(Setup2TermSet, self).__init__()
        
        for s in setup.stimuli:
            self._termset.add(asp.Term('stimulus', [s]))
            
        for i in setup.inhibitors:
            self._termset.add(asp.Term('inhibitor', [i]))
            
        for r in setup.readouts:
            self._termset.add(asp.Term('readout', [r]))


class LogicalNames2TermSet(asp.TermSetAdapter):
    component.adapts(ILogicalNames)
    
    def __init__(self, names):
        super(LogicalNames2TermSet, self).__init__()
        
        for var_name, var in enumerate(names.variables):
            self._termset.add(asp.Term('node', [var, var_name]))
            for clause_name, clause in names.iterclauses(var):
                self._termset.add(asp.Term('hyper', [var_name, clause_name, len(clause)]))
                for lit in clause:
                    self._termset.add(asp.Term('edge', [clause_name, lit.variable, lit.signature]))

class LogicalNetwork2TermSet(asp.TermSetAdapter):
    component.adapts(ILogicalNetwork)
    
    def __init__(self, network):
        super(LogicalNetwork2TermSet, self).__init__()
        
        names = component.getUtility(ILogicalNames)
        
        for var in network.variables:
            self._termset.add(asp.Term('variable', [var]))
        
        for var, formula in network.mapping.iteritems():
            var_name = names.get_variable_name(var)
            self._termset.add(asp.Term('formula', [var, var_name]))
            for clause in formula:
                clause_name = names.get_clause_name(clause)
                self._termset.add(asp.Term('dnf', [var_name, clause_name]))
                for lit in clause:
                    self._termset.add(asp.Term('clause', [clause_name, lit.variable, lit.signature]))
        
class TermSet2LogicalNetwork(object):
    component.adapts(asp.ITermSet)
    interface.implements(ILogicalNetwork)
    
    def __init__(self, termset):
        super(TermSet2LogicalNetwork, self).__init__()
        
        names = component.getUtility(ILogicalNames)
        self._mapping = defaultdict(set)
        for term in termset:
            if term.pred == 'dnf':
                self._mapping[names.variables[term.arg(0)]].add(names.clauses[term.arg(1)])
        
    @property
    def variables(self):
        return self._network.variables
        
    @property
    def mapping(self):
        return self._network.mapping

class TermSet2BooleLogicNetwork(TermSet2LogicalNetwork):
    component.adapts(asp.ITermSet)
    interface.implements(IBooleLogicNetwork)
    
    def __init__(self, termset):
        super(TermSet2BooleLogicNetwork, self).__init__(termset)
        names = component.getUtility(ILogicalNames)        
        self._network = BooleLogicNetwork(names.variables, self._mapping)
        
    def prediction(self, var, clamping):
        return self._network.prediction(var, clamping)


class LogicalNetworksReader2LogicalNetworkSet(object):
    component.adapts(ILogicalNetworksReader)
    interface.implements(ILogicalNetworkSet)
    
    def __init__(self, reader):
        super(LogicalNetworksReader2LogicalNetworkSet, self).__init__()
        names = component.getUtility(ILogicalNames)
        names.load(reader.graph)
        
        self.networks = set()
        for mapping in reader:
            self.networks.add(LogicalNetwork(list(names.variables), mapping))
            names.add(map(frozenset, mapping.itervalues()))
        
    def __iter__(self):
        return iter(self.networks)

class LogicalNetworkSet2TermSet(asp.TermSetAdapter):
    component.adapts(ILogicalNetworkSet)
    
    def __init__(self, networks):
        super(LogicalNetworkSet2TermSet, self).__init__()
        
        names = component.getUtility(ILogicalNames)
        for var in names.variables:
            self._termset.add(asp.Term('variable', [var]))
        
        for i, network in enumerate(networks):
            for var,formula in network.mapping.iteritems():
                formula_name = names.get_formula_name(formula)
                self._termset.add(asp.Term('formula', [i, var, names.get_formula_name(formula)]))
                for clause in formula:
                    clause_name = names.get_clause_name(clause)
                    self._termset.add(asp.Term('dnf', [formula_name, clause_name]))
                    for lit in clause:
                        self._termset.add(asp.Term('clause', [clause_name, lit.variable, lit.signature]))
                    
class ClampingTerm2TermSet(asp.TermSetAdapter):
    component.adapts(IClamping, asp.ITerm)
    
    def __init__(self, clamping, term):
        super(ClampingTerm2TermSet, self).__init__()
        
        for var, val in clamping:
            self._termset.add(asp.Term(term.pred, [var, val]))

class ClampingTermInClampingList2TermSet(asp.TermSetAdapter):
    component.adapts(IClamping, IClampingList, asp.ITerm)
    
    def __init__(self, clamping, clist, term):
        super(ClampingTermInClampingList2TermSet, self).__init__()
        
        name = clist.clampings.index(clamping)
        for var, val in clamping:
            self._termset.add(asp.Term(term.pred, [name, var, val]))
            
class Clamping2TermSet(ClampingTerm2TermSet):
    component.adapts(IClamping)
    
    def __init__(self, clamping):
        super(Clamping2TermSet, self).__init__(clamping, asp.Term('clamped'))

class ClampingInClampingList2TermSet(ClampingTermInClampingList2TermSet):
    component.adapts(IClamping, IClampingList)
    
    def __init__(self, clamping, clist):
        super(ClampingInClampingList2TermSet, self).__init__(clamping, clist, asp.Term('clamped'))

class TermSet2Clamping(object):
    component.adapts(asp.ITermSet)
    interface.implements(IClamping)
    
    def __init__(self, termset):
        literals = []
        for term in termset:
            if term.pred == 'clamped':
                literals.append(Literal(term.arg(0), term.arg(1)))
                
        self.clamping = Clamping(literals)
        
    def __iter__(self):
        return iter(self.clamping)
        
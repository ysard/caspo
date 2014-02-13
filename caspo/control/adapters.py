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
# along with caspo.  If not, see <http://www.gnu.org/licenses/>.
# -*- coding: utf-8 -*-
from zope import component
from pyzcasp import asp, potassco
from caspo import core

from interfaces import *
from impl import *

class CsvReader2MultiScenario(object):
    component.adapts(core.ICsvReader)
    interface.implements(IMultiScenario)
    
    def __init__(self, reader):
        super(CsvReader2MultiScenario, self).__init__()
        
        species = reader.fieldnames
    
        constraints = map(lambda name: name[3:], filter(lambda name: name.startswith('SC:'), species))
        goals = map(lambda name: name[3:], filter(lambda name: name.startswith('SG:'), species))
            
        self.exclude = set(constraints + goals)
        
        self.constraints = ConstraintsList()
        self.goals = GoalsList()
        
        for row in reader:
            literals = []
            for c in constraints:
                if row['SC:' + c] != '0':
                    literals.append(core.Literal(c, int(row['SC:' + c])))
                 
            cclamping = core.Clamping(literals)
            
            literals = []
            for g in goals:
                if row['SG:' + g] != '0':
                    literals.append(core.Literal(g, int(row['SG:' + g])))

            gclamping = core.Clamping(literals)        
                
            self.constraints.append(cclamping)
            self.goals.append(gclamping)
            
    def __iter__(self):
        for i, (constraints, goals) in enumerate(zip(self.constraints, self.goals)):
            yield i, constraints, goals

class MultiScenario2TermSet(asp.TermSetAdapter):
    component.adapts(IMultiScenario)
    
    def __init__(self, ms):
        super(MultiScenario2TermSet, self).__init__()
        
        for i, c, g in ms:
            self._termset.add(asp.Term('scenario', [i]))
            
            self._termset = self._termset.union(component.getMultiAdapter((c, ms.constraints, asp.Term('constrained')), asp.ITermSet))
            self._termset = self._termset.union(component.getMultiAdapter((g, ms.goals, asp.Term('goal')), asp.ITermSet))

class NetworksMultiScenario2TermSet(asp.TermSetAdapter):
    component.adapts(core.ILogicalNetworkSet, IMultiScenario)
    
    def __init__(self, networks, multiscenario):
        super(NetworksMultiScenario2TermSet, self).__init__()
        
        names = component.getUtility(core.ILogicalNames)
        for var in names.variables:
            if var not in multiscenario.exclude:
                self._termset.add(asp.Term('candidate', [var]))
            
        self._termset = self._termset.union(asp.ITermSet(networks))
        self._termset = self._termset.union(asp.ITermSet(multiscenario))    

class PotasscoDisjunctiveController(object):
    component.adapts(asp.ITermSet, potassco.IGringoGrounder, potassco.IClaspDSolver)
    interface.implements(IController, IStrategySet)
    
    def __init__(self, termset, gringo, clasp):
        super(PotasscoDisjunctiveController, self).__init__()
        self.termset = termset
        self.grover = component.getMultiAdapter((gringo, clasp), potassco.IMetaGrounderSolver)
            
    @asp.cleanrun        
    def control(self, size=0):
        encodings = component.getUtility(asp.IEncodingRegistry).encodings(self.grover.grounder)
        
        programs = [self.termset.to_file(), encodings('caspo.control.full')]
        
        self.grover.optimize = asp.TermSet([asp.Term('optimize',[1,1,asp.NativeAtom('incl')])])
        stdin="""
        #hide.
        #show hold(atom(intervention(_,_))).
        """
        self.grover.run(stdin, grounder_args=programs + ['-c maxsize=%s' % size], solver_args=["0"])
        
    def __iter__(self):
        for termset in self.grover:
            yield IStrategy(termset)

class PotasscoHeuristicController(object):
    component.adapts(asp.ITermSet, potassco.IGringoGrounder, potassco.IClaspHSolver)
    interface.implements(IController, IStrategySet)
        
    def __init__(self, termset, gringo, clasp):
        super(PotasscoHeuristicController, self).__init__()
        self.termset = termset
        self.grover = component.getMultiAdapter((gringo, clasp), asp.IGrounderSolver)

    @asp.cleanrun            
    def control(self, size=0):
        encodings = component.getUtility(asp.IEncodingRegistry).encodings(self.grover.grounder)
        
        programs = [self.termset.to_file(), encodings('caspo.control.full'), encodings('caspo.control.heuristic')]
        stdin = """
        #hide.
        #show intervention/2.
        """     
        self.grover.run(stdin, 
            grounder_args=programs + ['-c maxsize=%s' % size], 
            solver_args=['0', '-e record', '--opt-ignore'])

    def __iter__(self):
        for ts in self.grover:
            yield IStrategy(asp.TermSet(filter(lambda t: len(t.args) == 2, ts)))

class TermSet2Strategy(object):
    component.adapts(asp.ITermSet)
    interface.implements(IStrategy)
    
    def __init__(self, termset):
        self.strategy = Strategy(map(lambda term: core.Literal(term.arg(0),term.arg(1)), termset))
        
    def __iter__(self):
        return iter(self.strategy)
        
    def __str__(self):
        return str(self.strategy)

class Strategies2CsvWriter(object):
    component.adapts(IStrategySet)
    interface.implements(core.ICsvWriter)
    
    def __init__(self, strategies):
        self.strategies = strategies
        names = component.getUtility(core.ILogicalNames)
        self.header = names.variables
        
        
    def __iter__(self):
        for strategy in self.strategies:
            row = dict.fromkeys(self.header, 0)
            row.update(strategy)
            yield row
        
    def write(self, filename, path='./'):
        writer = component.getUtility(core.ICsvWriter)
        writer.load(self, self.header)
        writer.write(filename, path)
        
    
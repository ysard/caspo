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

import os, sys, argparse, pkg_resources
import handlers

VERSION = pkg_resources.get_distribution("caspo").version
LICENSE = """
Copyright (C) Santiago Videla
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
caspo is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.\n
"""

def run():
    clingo_parser = argparse.ArgumentParser(add_help=False)
    clingo_parser.add_argument("--clingo", dest="clingo", default="clingo", help="clingo solver binary (Default to 'clingo')", metavar="C")
    
    parser = argparse.ArgumentParser("caspo", formatter_class=argparse.RawTextHelpFormatter,
                                     description="Reasoning on the response of logical signaling networks with Answer Set Programming")
                                         
    subparsers = parser.add_subparsers(title='caspo subcommands', dest='cmd',
                                       description='for specific help on each subcommand use: caspo {cmd} --help')
    
    learn = subparsers.add_parser("learn", parents=[clingo_parser])
    learn.add_argument("pkn", help="prior knowledge network in SIF format")
    learn.add_argument("midas", help="experimental dataset in MIDAS file")
    learn.add_argument("time", type=int, help="time-point to be used in MIDAS")    
    learn.add_argument("--fit", dest="fit", type=float, default=0., help="tolerance over fitness (Default to 0)", metavar="F")
    learn.add_argument("--size", dest="size", type=int, default=0, help="tolerance over size (Default to 0)", metavar="S")
    learn.add_argument("--factor", dest="factor", type=int, default=100, choices=[1, 10, 100, 1000], help="discretization over [0,D] (Default to 100)", metavar="D")                        
    learn.add_argument("--discretization", dest="discretization", default='round', choices=['round', 'floor', 'ceil'], help="discretization function: round, floor, ceil (Default to round)", metavar="T")                        
    learn.set_defaults(handler=handlers.learn)
    
    design = subparsers.add_parser("design", parents=[clingo_parser])
    design.add_argument("networks", help="logical networks in CSV format")
    design.add_argument("midas", help="experimental dataset in MIDAS file")                    
    design.add_argument("--stimuli", dest="stimuli", type=int, default=-1,help="maximum number of stimuli per experiment", metavar="S")
    design.add_argument("--inhibitors", dest="inhibitors", type=int, default=-1, help="maximum number of inhibitors per experiment", metavar="I")
    design.add_argument("--experiments", dest="experiments", type=int, default=20, help="maximum number of experiments (Default to 20)", metavar="E")
    design.set_defaults(handler=handlers.design)
    
    control = subparsers.add_parser("control")
    control.add_argument("networks", help="Logical networks in CSV format")
    control.add_argument("scenarios", help="intervention scenarios in csv format")                        
    control.add_argument("--size", dest="size", type=int, default=0, help="maximum size for interventions strategies (Default to 0 (no limit))", metavar="M")
    control.add_argument("--allow-constraints", dest="iconstraints", action='store_true', help="allow intervention over side constraints (Default to False)")    
    control.add_argument("--allow-goals", dest="igoals", action='store_true', help="allow intervention over goals (Default to False)")
    control.add_argument("--gringo", dest="gringo", default="gringo", help="gringo grounder binary (Default to 'gringo')", metavar="G")
    control.add_argument("--hclasp", dest="hclasp", default="hclasp", help="hclasp solver binary (Default to 'hclasp')", metavar="H")                    
    control.set_defaults(handler=handlers.control)
    
    analyze = subparsers.add_parser("analyze", parents=[clingo_parser])
    analyze.add_argument("--networks", dest="networks", help="logical networks in CSV format", metavar="N")
    analyze.add_argument("--midas", dest="midas", nargs=2, metavar=("M","T"), help="experimental dataset in MIDAS file and time-point to be used")
    analyze.add_argument("--strategies", help="intervention stratgies in CSV format", metavar="S")
    analyze.set_defaults(handler=handlers.analyze)
    
    visualize = subparsers.add_parser("visualize")
    visualize.add_argument("--pkn", dest="pkn", help="prior knowledge network in SIF format", metavar="P")
    visualize.add_argument("--midas", dest="midas", help="experimental dataset in MIDAS file", metavar="M")
    visualize.add_argument("--networks", dest="networks", help="logical networks in CSV format", metavar="N")
    visualize.add_argument("--sample", dest="sample", type=int, default=0, help="visualize a sample of N logical networks (Default to all)", metavar="R")
    visualize.add_argument("--union", dest="union", action='store_true', help="visualize the union of logical networks (Default to False)")
    visualize.add_argument("--strategies", help="intervention stratgies in CSV format", metavar="S")
    visualize.set_defaults(handler=handlers.visualize)
    
    test = subparsers.add_parser("test", parents=[clingo_parser])
    test.add_argument("--gringo", dest="gringo", default="gringo", help="gringo grounder binary (Default to 'gringo')", metavar="G")
    test.add_argument("--hclasp", dest="hclasp", default="hclasp", help="hclasp solver binary (Default to 'hclasp')", metavar="H")
    test.add_argument("--testcase", help="testcase name", choices=["Toy", "LiverToy", "LiverDREAM", "ExtLiver"], default="Toy")

    parser.add_argument("--quiet", dest="quiet", action="store_true", help="do not print anything to standard output")
    parser.add_argument("--out", dest="outdir", default='.', help="output directory path (Default to current directory)", metavar="O")
    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION + '\n' + LICENSE)
    
    args = parser.parse_args()
    
    from zope import component
    from caspo.core import Printer, IPrinter
    
    printer = Printer(args.quiet)
    gsm = component.getGlobalSiteManager()
    gsm.registerUtility(printer, IPrinter)
    
    if args.cmd != "test":
        printer.pprint("Running caspo %s...\n" % args.cmd)
        return args.handler(args)
    else:
        testcase = args.testcase
        clingo = args.clingo
        gringo = args.gringo
        hclasp = args.hclasp
        
        printer.pprint("Testing caspo subcommands using test case %s.\n" % testcase)
        import caspo
        from subprocess import check_call
        
        if os.path.exists('test'):
            check_call(['rm', '-fr', 'test'])

        os.mkdir('test')
        path = os.path.dirname(caspo.__file__)
        printer.pprint("Copying files for running tests:")
        printer.pprint("\tPrior knowledge network: test/pkn.sif")
        printer.pprint("\tPhospho-proteomics dataset: test/dataset.csv")
        printer.pprint("\tIntervention scenarios: test/scenarios.csv")
        printer.pprint("")
        
        check_call(['cp', os.path.join(path, 'data', args.testcase, 'pkn.sif'), 'test/'])
        check_call(['cp', os.path.join(path, 'data', args.testcase, 'dataset.csv'), 'test/'])
        check_call(['cp', os.path.join(path, 'data', args.testcase, 'scenarios.csv'), 'test/'])
        
        testcases = {
            "Toy":        ('10', '0.1' , '5'),
            "LiverToy":   ('10', '0.1' , '5'),
            "LiverDREAM": ('30', '0.1' , '2'),
            "ExtLiver":   ('30', '0.02', '0'),
        }
        
        params = testcases[testcase]
        args = parser.parse_args(['--out', 'test', 'learn', '--clingo', clingo,
                                  os.path.join('test', 'pkn.sif'), 
                                  os.path.join('test', 'dataset.csv'), 
                                  params[0], '--fit', params[1], '--size', params[2]])

        printer.pprint("Running caspo %s...\n" % args.cmd)
        try:
            args.handler(args)
        except Exception as e:
            printer.pprint(e)
            printer.pprint("Testing on caspo %s has failed." % args.cmd)
            
        printer.pprint("")
        
        args = parser.parse_args(['--out', 'test', 'control', '--gringo', gringo, '--hclasp', hclasp,
                                  os.path.join('test', 'networks.csv'), 
                                  os.path.join('test', 'scenarios.csv')])

        printer.pprint("Running caspo %s...\n" % args.cmd)
        try:
            args.handler(args)
        except Exception as e:
            printer.pprint(e)
            printer.pprint("Testing on caspo %s has failed." % args.cmd)
            
        printer.pprint("")
                
        args = parser.parse_args(['--out', 'test', 'analyze', '--clingo', clingo,
                                  '--networks', os.path.join('test', 'networks.csv'), 
                                  '--midas', os.path.join('test', 'dataset.csv'), 
                                  params[0], '--strategies', os.path.join('test', 'strategies.csv')])
                                  
        printer.pprint("Running caspo %s...\n" % args.cmd)
        try:
            args.handler(args)
        except Exception as e:
            printer.pprint(e)
            printer.pprint("Testing on caspo %s has failed." % args.cmd)
            
        printer.pprint("")
                
        args = parser.parse_args(['--out', 'test', 'design', '--clingo', clingo,
                                  os.path.join('test', 'behaviors.csv'), 
                                  os.path.join('test', 'dataset.csv')])

        printer.pprint("Running caspo %s...\n" % args.cmd)
        try:
            args.handler(args)
        except Exception as e:
            printer.pprint(e)
            printer.pprint("Testing on caspo %s has failed." % args.cmd)
            
        printer.pprint("")
                
        args = parser.parse_args(['--out', 'test', 'visualize', 
                                  '--pkn', os.path.join('test', 'pkn.sif'),
                                  '--networks', os.path.join('test', 'networks.csv'), 
                                  '--midas', os.path.join('test', 'dataset.csv'),
                                  '--strategies', os.path.join('test', 'strategies.csv'),
                                  '--union'])

        printer.pprint("Running caspo %s...\n" % args.cmd)
        try:
            args.handler(args)
        except Exception as e:
            printer.pprint(e)
            printer.pprint("Testing on caspo %s has failed." % args.cmd)
    
        printer.pprint("")

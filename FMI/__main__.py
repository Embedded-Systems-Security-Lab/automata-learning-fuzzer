import argparse
from numpy import random
import random as stdrandom
import os

from FMI.targets.target import Target
from FMI.fuzzers.ifuzzer import IFuzzer
from FMI.restarters.irestarter import IRestarter
from FMI.session import Session

from FMI.utils import config_constants, afl_constants, constants
from FMI.utils.decorators import FMILogger
# from FMI.fuzzer import FMIFuzzer
from FMI.projects.project import Project

from FMI.network.tcp_socket_connection import TCPSocketConnection
from FMI.SML.RPE.rpe import RPE
from FMI.format_learner.abstraction import AbstractionLayer
from FMI.network.network_process_wrapper import NetworkProcessWrapper, NetworkProcessWrapperMaker
from FMI.active_grammar_inferer import ActiveGrammarInferer
from FMI.mutation.afl_mutation_strategy import AFL_MUTATION
from FMI.mutation.radamsa.radamsa_mutation import RamdamsaMutation
from FMI.mutation.afl_mutation_strategy import MutationEingine
from FMI.mutation.base_mutation import Mutation

from collections import defaultdict


logo = """
`````````````````````````````````````````````````````````````````````
``````=======````````````````````````````````````````````````````````
`````|````````````||\``````/||```````````````````````````````````````
`````|````````````||`\````/`||```````````````````````````````````````
`````|=======`````||``\``/``||```````````````````````````````````````
`````|````````````||```\/```||```````````````````````````````````````
`````|````````````||````````||```````````````````````````````````````
`````|````````````||````````||```````````````````````````````````````
 ````````````````````````````````````````````````````````````````````
 Industrial Control Fuzzing Approach by Uchenna Ezeobi
"""

@FMILogger
class FMI(object):

    def __init__(self):
        self.session = None
        self._init_argparser()
        self.args = self._parse_args()
        sym_per_msg = self.args.fuzz_protocol.get_all_msg_by_symbols()

        abslayer = AbstractionLayer(sym_per_msg)
        # TODO: Fix this latter
        connection = TCPSocketConnection(
                        host=self.args.host,
                        port=self.args.port,
                        send_timeout=self.args.send_timeout,
                        recv_timeout=self.args.recv_timeout
                        )
        #TODO: Add more options for parameter passing

        # TODO add an option to instantiate a Frida target or normal target
        self.target = Target(
                        connection=connection
                        )
        self.project = Project(self.args.project)
        self.mutator = defaultdict(lambda: defaultdict(Mutation))

        self.learner = ActiveGrammarInferer(
                        self.args.fuzz_protocol.get_symbols_name(),
                        self.restart_module,
                        connection,
                        abslayer,
                        self.project
                        )

        self.session = Session(
                        restart_sleep_time=self.args.restart_sleep_time,
                        target=self.target,
                        restarter=self.restart_module,
                        fuzz_protocol=self.args.fuzz_protocol,
                        learner=self.learner,
                        mutator=self.mutator,
                        project=self.project,
                        seed=self.args.seed,
                        time_budget=self.args.time_budget,
                        debug=self.args.debug,
                        output=self.args.output,
                        dump_shm=self.args.dump_shm,
                        deterministic=False
                        ) #pass
        # To be continued

    def _init_argparser(self):
        """
        Initializes the argparser inside self.parser
        """
        self.parser = argparse.ArgumentParser(
            description=logo,
            formatter_class=argparse.RawTextHelpFormatter
        )
        self.parser.add_argument("-pj", "--project", type=str, help="project to create")
        self.parser.add_argument("-hs", "--host", type=str, help="target host")
        self.parser.add_argument("-p", "--port", type=int, help="target port")
        conn_grp = self.parser.add_argument_group('Connection options')
        conn_grp.add_argument("-pt", "--protocol", dest="protocol", help="transport protocol", default='tcp',
                              choices=['tcp', 'udp', 'tcp+tls'])
        conn_grp.add_argument("-st", "--send_timeout", dest="send_timeout", type=float, default=0.5,
                              help="send() timeout")
        conn_grp.add_argument("-rt", "--recv_timeout", dest="recv_timeout", type=float, default=0.5,
                              help="recv() timeout")

        fuzzers = [fuzzer_class.name for fuzzer_class in IFuzzer.__subclasses__()]

        fuzz_grp = self.parser.add_argument_group('Fuzzer options')
        fuzz_grp.add_argument("--fuzzer", dest="fuzz_protocol", help='application layer fuzzer', required=True,
                              choices=fuzzers)
        fuzz_grp.add_argument('--name', dest='name', type=str, help='Name of the protocol you are fuzzing')
        fuzz_grp.add_argument('--debug', action='store_true', help='enable debug.csv')
        # fuzz_grp.add_argument('--batch', action='store_true', help='non-interactive, very quiet mode')
        # fuzz_grp.add_argument('--dtrace', action='store_true', help='extremely verbose debug tracing')
        fuzz_grp.add_argument('--pcap', dest='pcap', type=str, required=True, help='example communicaion between client and server')
        fuzz_grp.add_argument('--seed', dest='seed', type=int, default=0, help='prng seed')
        fuzz_grp.add_argument('--budget', dest='time_budget', type=float, default=0.0, help='time budget')
        fuzz_grp.add_argument('--output', dest='output', type=str, default="", help='output dir')
        fuzz_grp.add_argument('--shm_id', dest='shm_id', type=str, default="", help='custom shared memory id overwrite')
        fuzz_grp.add_argument('--dump_shm', dest='dump_shm', action='store_true', default=False, help='dump shm after run')

        # learner_grp = self.parser.add_argument_group('Automata learning options')

        # learner_grp.add_argument('--lm', dest='lm', type=str, required=True, help='automata ')
        # learner_grp.add_argument('--nstep', dest='nstep', type=int, default=0, help='Random Walk Eq Oracle')
        # learner_grp.add_argument('--budget', dest='time_budget', type=float, default=0.0, help='time budget')
        # learner_grp.add_argument('--output', dest='output', type=str, default="", help='output dir')
        # learner_grp.add_argument('--shm_id', dest='shm_id', type=str, default="", help='custom shared memory id overwrite')
        # learner_grp.add_argument('--dump_shm', dest='dump_shm', action='store_true', default=False, help='dump shm after run')


        restarters_grp = self.parser.add_argument_group('Restart options')
        restarters_help = 'Restarter Modules:\n'
        for restarter in IRestarter.__subclasses__():
            restarters_help += '  {}: {}\n'.format(restarter.name(), restarter.help())
        restarters_grp.add_argument('--restart', nargs='+', default=[], metavar=('module_name', 'args'),
                                    help=restarters_help)
        restarters_grp.add_argument("--restart-sleep", dest="restart_sleep_time", type=int, default=5,
                                    help='Set sleep seconds after a crash before continue (Default 5)')



    def _parse_args(self) -> argparse.Namespace:
        """
        Parse arguments with argparse

        Returns:
            (argparse.Namespace) Argparse arguments
        """
        args = self.parser.parse_args()
        if args.shm_id != "":
            afl_constants.SHM_OVERWRITE = args.shm_id

        random.seed(args.seed)
        stdrandom.seed(args.seed)
        args.fuzz_protocol = [icl for icl in IFuzzer.__subclasses__() if icl.name == args.fuzz_protocol][0]
        args.fuzz_protocol.initialize(**args.__dict__)

        self.restart_module = None
        if len(args.restart) > 0:
            try:
                restart_module = [mod for mod in IRestarter.__subclasses__() if mod.name() == args.restart[0]][0]
                restart_args = args.restart[1:]
                self.restart_module = restart_module(*restart_args)
            except IndexError:
                print(f"The restarter module {args.restart[0]} does not exist!")
                exit(1)
        return args

    def run(self):
        self.session.start()

def main():
    fmi = FMI()
    print(logo)
    try:
        fmi.run()
    except:
        try:
            self.session.restarter.kill()
        except:
            pass

if __name__ == "__main__":
    main()

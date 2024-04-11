# MCFICS: Model-based Coverage-guided Fuzzing for Industrial Control System Protocol Implementations
In this paper, we present MCFICS, a coverage-guided greybox
fuzzing framework that uses (1) active model learning for stochastic reactive systems to infer the state machine of the underlying stateful ICS protocol implementations, and (2) guided fuzzing to explore the state space using this learned state machine. During fuzzing, new input sequences that increase code coverage are used to refine the state machine model of the ICS protocol implementations. Refinement helps to further explore deeper states or paths to increase coverage of the overall state space of the ICS protocol implementation under test. We implemented and tested MCFICS with two example server implementations of IEC 60870-5-104 (IEC104) SCADA protocol
[Link To Paper]()
### Preresiquite
**System:**
```bash
sudo apt-get update && sudo apt get install python3 python3-pip python3-venv
```
*Additionally: * MCFICS requires afl-gcc or afl-clang to build target for instrumentation and collecting code coverage. To install the program yourself you need to following the depencies and afl instrumentation guide provided by [AFL++](https://github.com/AFLplusplus/AFLplusplus)
## Installation (Tested on Ubuntu 22.04 & 20.04 & 18.04 & 16.04)
1. Install [AFL++](https://github.com/AFLplusplus/AFLplusplus)
2. Install MCFICS
```bash
git clone --recursive <the-current-repo> # clone
cd automata-learning-fuzzer             # workdir
python3 -m venv env                     # Creat virtual environment
source env/bin/activate                 # Activate virtual environment
unzip netzob                            # unzip version of netzob that works for our experiment, pip install netzob does not work
cd netzob/netzob                         # Install Netzob manually
pip install pylstar numpy               # Install dependencies for Netzob
python setup.py install
cd ../..                                # Move to the top tree folder       
pip install -r requirements.txt         # Install other libraries
```
You should have a working version of both afl++ and MCFICS
We need to compile the [lib60870](https://github.com/mz-automation/lib60870) which is located in the IEC104 folder
```bash
cd IEC104/lib60870/lib60870-C/
```
**Prepare Instrumentation**
We will replace the C compiler with AFL++ toolchain compiler, you can use afl-clang, afl-clang-fast, afl-gcc or afl-gcc-fast to compile the code
```bash
echo "CC=<path-to-afl>/afl-clang-fast" >> make/target_system.mk                     # Use afl-clang-fast to compile the code
echo "CFLAGS += -fsanitize=address,undefined" >> make/target_system.mk                        # Add address sanitizer
make -j<N CPU>
```
You now have a working instrumentation, next step is to compile the test harness.

**Test Harness**
```bash
cd examples/cs104_server_no_threads
make -j<N CPU>
```
This gives a compiled server example
## Usage

```bash
python -m FMI --help

usage: __main__.py [-h] [-pj PROJECT] [-hs HOST] [-p PORT] [-pt {tcp,udp,tcp+tls}]
                   [-st SEND_TIMEOUT] [-rt RECV_TIMEOUT] --fuzzer {MIFuzzer}
                   [--name NAME] [--debug] --pcap PCAP [--seed SEED]
                   [--budget TIME_BUDGET] [--output OUTPUT] [--shm_id SHM_ID]
                   [--dump_shm] [--restart module_name [args ...]]
                   [--restart-sleep RESTART_SLEEP_TIME]
 Industrial Control Fuzzing Approach by Uchenna Ezeobi

optional arguments:
  -h, --help            show this help message and exit
  -pj PROJECT, --project PROJECT
                        project to create
  -hs HOST, --host HOST
                        target host
  -p PORT, --port PORT  target port

Connection options:
  -pt {tcp,udp,tcp+tls}, --protocol {tcp,udp,tcp+tls}
                        transport protocol
  -st SEND_TIMEOUT, --send_timeout SEND_TIMEOUT
                        send() timeout
  -rt RECV_TIMEOUT, --recv_timeout RECV_TIMEOUT
                        recv() timeout

Fuzzer options:
  --fuzzer {MIFuzzer}   application layer fuzzer
  --name NAME           Name of the protocol you are fuzzing
  --debug               enable debug.csv
  --pcap PCAP           example communicaion between client and server
  --seed SEED           prng seed
  --budget TIME_BUDGET  time budget
  --output OUTPUT       output dir
  --shm_id SHM_ID       custom shared memory id overwrite
  --dump_shm            dump shm after run

Restart options:
  --restart module_name [args ...]
                        Restarter Modules:
                          afl_fork: '<executable> [<argument> ...]' (Pass command and arguments within quotes, as only one argument)
  --restart-sleep RESTART_SLEEP_TIME
                        Set sleep seconds after a crash before continue (Default 5)

```
**Run the example server for IEC104**
```bash
cd <path-mcfics>
python -m FMI -pj new_project -hs 127.0.0.1 -p 2404 -pt tcp --fuzzer MIFuzzer --name iec104 --pcap FMI/data/iec104/combined.pcap --seed 123456 --restart afl_fork "./FMI/c_SUT/cs104_server_no_threads"  --budget 10000000
```
## Acknowledgement 
We would like to the following code repository, this project will not be possible with this code base.

* An Active Automata Learning Library: [AALPY](https://github.com/DES-Lab/AALpy)
* Evolutionary Protocol Fuzzer: [EPF](https://github.com/fkie-cad/epf)
* Network Protocol Fuzzing for Humans [BooFuzz](https://github.com/jtpereyda/boofuzz)
* Coverage-guided parallel fuzzer [Manul](https://github.com/mxmssh/manul)
* Protocol Reverse Engineering, Modeling and Fuzzing [Netzob](https://github.com/netzob/netzob/tree/master)
## Owner of Repo 

* **Uchenna Ezeobi** (uezeobi@uccs.edu, uchenna.ezeobi3@gmail.com)
* **Dr. Gedare Bloom** (gbloom@uccs.edu)
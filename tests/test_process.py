import time
#from FMI.network.process_wrapper import ProcessWrapper
from FMI.network.network_process_wrapper import NetworkProcessWrapper, NetworkProcessWrapperMaker
from subprocess import Popen, PIPE
import shlex
import queue
import os
path = "./3rd_party_protocol/epics_project/support/pvAccessCPP/testApp/O.linux-x86_64/testServer"
if os.path.exists(path):
    print("File exist")
n = NetworkProcessWrapperMaker(path, listen_ip="0.0.0.0", listen_port=5075, name="Start a server", restart_process=True)
n.start()
time.sleep(2)
# n.restart()

print(n.is_ready())
print(n)

# print("Waiting")
time.sleep(100)
# print(n)

print("About to stop")
time.sleep(2)
n.stop()


# # print(n)
#!/usr/bin/env python


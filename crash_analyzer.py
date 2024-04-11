import os
import glob
import time
import hashlib
import signal

from triage.utils.executor import Executor
from triage.utils.replay import Replay
from FMI.network.tcp_socket_connection import TCPSocketConnection
from FMI.targets.target import Target
from FMI.utils.ip_constants import DEFAULT_MAX_RECV

def main():
    # You're running on a 64 bits computer 
    gdb_script = """ printf "[+] Disabling verbose and complaints"\n
        set verbose off
        set complaints 0
        set logging file %s
        set logging on
        r
        printf "[+] Backtrace:"\n
        bt
        printf "[+] info reg:"\n
        info reg
        printf "[+] exploitable:"\n
        source 3rd_party_protocol/exploitable/exploitable/exploitable.py
        exploitable
        printf "[+] disassemble $rip, $rip+16:"\n
        disassemble $rip, $rip+16
        printf "[+] list"\n
        list
    """

    # Assumption that you installed and the target is already instrumented

    server_with_gdb =  Executor()
    #replay_client = "To implement this"
    #server_path = "/home/embedded/Project/fuzzers/micfics_case_study_experiment/targets/libiec_iccp_mod/examples/server_example_control/server_example_control"
    # server_path = "/home/embedded/Project/fuzzers/micfics_case_study_experiment/targets/pvxs/example/O.linux-x86_64/mailbox mypv"
    server_path ="/home/embedded/Project/fuzzers/micfics_case_study_experiment/targets/iec104/lib60870_2/lib60870-C/examples/cs104_server_no_threads/cs104_server_no_threads 2404"
    #server_path = "/home/embedded/Project/fuzzers/micfics_case_study_experiment/targets/libiec61850/examples/server_example_substitution/server_example_substitution"
    cmd = 'gdb -x gdb.script --batch --args {}  '.format(server_path)
    cmd = 'gdb {} -x gdb.script -batch'.format(server_path)
    N = 1
    for num in range(1, 16):

        #data_path = "/home/embedded/Project/fuzzers/micfics_case_study_experiment/datasets/aflnwe_pvacess_mailbox/aflnet_{}/replayable-crashes".format(num)
        #data_path = "/home/embedded/Project/fuzzers/micfics_case_study_experiment/datasets/stateafl_server_example_control/stateafl_{}/replayable-crashes".format(num)
        #data_path = "/home/embedded/Project/fuzzers/micfics_case_study_experiment/datasets/micfics_pvxs_mailbox_2/micfics_{}/crashes/20231017_184041_crash/suspects".format(num)
        data_path = "/home/embedded/Project/fuzzers/micfics_case_study_experiment/datasets/aflnet_cs104_server_no_threads_no_d/aflnet_{}/replayable-crashes".format(num)
        data = []
        for root, dirs, files in os.walk(data_path):
            for file in files:
                if not file.endswith(".txt"):
                    data.append(os.path.join(root,file))
        print(len(data))

        client = TCPSocketConnection(host='0.0.0.0',
                                     port=2404,
                                     send_timeout=3.0,
                                     recv_timeout=3.0)
        
        """
        python -m FMI -pj iec_cs104_smm_3 -hs 127.0.0.1 -p 2404 -pt tcp --fuzzer MIFuzzer --name iec104 --pcap FMI/data/other/combined.pcap --seed 123456 --restart afl_fork "./3rd_party_protocol/other/cs104_server_no_threads"  --budget 10000000
        TCPSocketConnection(
                            host=self.args.host,
                            port=self.args.port,
                            send_timeout=self.args.send_timeout,
                            recv_timeout=self.args.recv_timeout
                            )
        """
        N = 1
        count = -1
        # res_path = "micfics_pvacess_mailbox/micfics_{}".format(num)
        res_path = "aflnet_cs104_server_no_thread/aflnet_{}".format(num)
        os.makedirs(res_path, exist_ok=True)

        for d in data:
            #print(d)
            count += 1
            #seq = Replay.read_data(d)
            seq = Replay.replay_data_afl(d)
            print("The count is {} - {}".format(count, d ))
            file_name = os.path.basename(d)
            print(file_name)
            for i in range(N):
                output_gdb_script = gdb_script % ("{}/res_{}.txt".format(res_path,count))
                # print(output_gdb_script)
                #logname = hashlib.sha256(output_gdb_script.encode('utf-8')).hexdigest()
                open('gdb.script', 'w').write(output_gdb_script)
                abort_test = False
                try:
                    res = server_with_gdb.start_process(cmd)
                    #Connect ot the server through the client and send sequence of messages
                    time.sleep(2)
                    try:
                        client.open()
                    except Exception as e:
                        for _ in range(3):
                            server_with_gdb.start_process(cmd)
                            print("Trying to restart")
                            time.sleep(2)
                            try:
                                client.open()
                                break
                            except Exception as e:
                                abort_test = True
                    if abort_test:
                        print("Could not connect, aborting")
                        continue
                    print("The length of the seq is ", len(seq))
                    for s in seq:
                        try:
                            print("Sending {}".format(s))
                            client.send(s)
                            recv = client.recv(DEFAULT_MAX_RECV)
                            print("Receiving {}".format(recv))
                            #time.sleep(0.001)
                        except:
                            print("Unable to send message {} - {}".format(d, count))
                except Exception as e:
                    print("Something went wrong!")
                finally:
                    try:
                        
                        time.sleep(1.0)
                        if (server_with_gdb.p_process.poll() is None):
                            server_with_gdb.kill()
                        print(server_with_gdb.p_process.__dict__)
                        #time.sleep(0.1)
                        #print("killing the process: {}".format(server_with_gdb))
                        # try:
                        #server_with_gdb.kill()
                        # except OSError as e:
                        #     print("Could not kill it {}".format(e))
                        time.sleep(0.05)
                    except:
                        pass   
                    #server_with_gdb.kill()
                    # time.sleep(1)
                # print(server_with_gdb.p_process.__dict__)
                # print(server_with_gdb.p_process.poll())
                # print(server_with_gdb.p_process.__dict__)
                # print(server_with_gdb.p_process.returncode)
                #exit()
            # if count >= 2:
            #     break
        exit()
        
            
if __name__ == "__main__":
    main()

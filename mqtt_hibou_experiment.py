
import sys
import threading
import time
import random
import os
import shutil
import subprocess

global id_already_taken
id_already_taken = set()

def writing_proc(vector_message, trace_as_list,trace_with_data_as_list):
    unique_id = 1
    while unique_id in id_already_taken:
        unique_id = random.randint(1, 1000)
    id_already_taken.add(unique_id)
    #
    for message in vector_message:
        trace_as_list.append(message)
        trace_with_data_as_list.append(message + '({})'.format(unique_id))
        time.sleep(random.uniform(0.01, 0.02))

def write_a_trace(min_loop_rep,max_loop_rep):
    client_name = "client"
    broker_name = "broker"

    mesvec_pub_qos0 = ( client_name + "!pub_qos0", broker_name + "?pub_qos0")
    mesvec_pub_qos1 = (client_name + "!pub_qos1", broker_name + "?pub_qos1", broker_name + "!puback", client_name + "?puback")
    mesvec_pub_qos2 = (client_name + "!pub_qos2", broker_name + "?pub_qos2", broker_name + "!pubrec", client_name + "?pubrec", client_name + "!pubrel", broker_name + "?pubrel", broker_name + "!pubcomp", client_name + "?pubcomp")
    mesvec_subscribe = (client_name + "!subscribe", broker_name + "?subscribe", broker_name + "!suback", client_name + "?suback")
    mesvec_unsubscribe = (client_name + "!unsubscribe", broker_name + "?unsubscribe", broker_name + "!unsuback", client_name + "?unsuback")

    all_mes_vecs = {mesvec_pub_qos0}#, mesvec_pub_qos1, mesvec_pub_qos2, mesvec_subscribe, mesvec_unsubscribe}

    global trace_as_list
    global trace_with_data_as_list
    trace_as_list           = [client_name + "!connect", broker_name + "?connect", broker_name + "!connack", client_name + "?connack"]
    trace_with_data_as_list = [client_name + "!connect", broker_name + "?connect", broker_name + "!connack", client_name + "?connack"]

    remaining_loops = random.randint(min_loop_rep,max_loop_rep)

    threads = []

    while remaining_loops > 0:
        op = random.sample(all_mes_vecs, 1)[0]
        f1 = threading.Thread(target=writing_proc, args=[op, trace_as_list, trace_with_data_as_list])
        f1.start()
        threads.append(f1)
        time.sleep(random.uniform(0.0025, 0.0125))
        remaining_loops = remaining_loops - 1

    for thread in threads:
        thread.join()

    trace_as_list           = trace_as_list + [ client_name + "!disconnect",  broker_name + "?disconnect" ]
    trace_with_data_as_list = trace_with_data_as_list + [ client_name + "!disconnect",  broker_name + "?disconnect" ]

    return (trace_as_list,trace_with_data_as_list)

def empty_directory(dir_path):
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def write_trace_on_file(file_path, trace_as_list):
    sys.stdout = open(file_path, 'w')
    sys.stdout.write("[#all] ")
    sys.stdout.write(".".join(trace_as_list))

def generate_mqtt_traces(number_of_traces,min_loop_rep,max_loop_rep):
    for i in range(number_of_traces):
        (trace,trace_with_data) = write_a_trace(min_loop_rep,max_loop_rep)
        total_len = len(trace)
        for j in range(total_len):
            ok_trace_file_path = './traces/mqtt_glotrace_{}_{}_{}.htf'.format(i+1,total_len,(j+1))
            write_trace_on_file( ok_trace_file_path, trace[:j+1] )
            #
            ok_trace_with_data_file_path = './traces/mqtt_glotrace_{}_{}_{}.hxtf'.format(i + 1, total_len, (j + 1))
            write_trace_on_file(ok_trace_with_data_file_path, trace_with_data[:j + 1])
            #
            ko_trace_file_path = './traces/mqtt_glotrace_{}f_{}_{}.htf'.format(i + 1, total_len, (j + 1))
            write_trace_on_file(ko_trace_file_path, trace[:j + 1] + ["broker!connect"] )
            #
            ko_trace_with_data_file_path = './traces/mqtt_glotrace_{}f_{}_{}.hxtf'.format(i + 1, total_len, (j + 1))
            write_trace_on_file(ko_trace_with_data_file_path, trace_with_data[:j + 1] + ["broker!connect"] )

def run_hib_mqtt(is_data,mean_on,trace_file):
    sum_time = 0
    for i in range(mean_on):
        if is_data:
            start = time.time()
            rtc = subprocess.run(["./hibou_efm.exe", "analyze", "mqtt_model_value_passing.hxsf", trace_file ], capture_output=True)
            end = time.time()
        else:
            start = time.time()
            rtc = subprocess.run(["./hibou_label.exe", "analyze", "mqtt_model_abstract.hsf", trace_file], capture_output=True)
            end = time.time()
        stdout_as_str = str(rtc.stdout)
        if "WeakPass" in stdout_as_str:
            verdict = "WeakPass"
        elif "Pass" in stdout_as_str:
            verdict = "Pass"
        elif "Fail" in stdout_as_str:
            verdict = "Fail"
        else:
            verdict = "Unknown"
        sum_time += (end - start)
    return ( verdict, (sum_time/mean_on) )

def make_perf_report(is_data,mean_on):
    if is_data:
        sys.stdout = open('mqtt_perf_report_with_data.txt', 'w')
        file_type = "hxtf"
    else:
        sys.stdout = open('mqtt_perf_report.txt', 'w')
        file_type = "htf"

    print( "orig_trace_id,trace_len,analysis_time,verdict" )
    for trace_file in os.listdir("./traces/"):
        if trace_file.endswith(file_type):
            subs = (trace_file[:-(1+len(file_type))].split("_"))[2:]
            trace_id   = subs[0]
            prefix_len = int( subs[2] )
            (verdict,ana_time) = run_hib_mqtt(is_data,mean_on,"./traces/" + trace_file)
            print( ",".join([str(trace_id), str(prefix_len), str(ana_time), verdict]) )

if __name__ == '__main__':
    empty_directory("./traces/")
    generate_mqtt_traces( 1,25,25 )
    make_perf_report(True, 2)
    make_perf_report(False, 2)



import os
import linecache
import argparse
from dep_bugClass import depBugInfo
import jpype
import multiprocessing
from multiprocessing import pool
import zipfile
import sys
sys.path.append("..")
from dir_extra import *
import time
# import timeout_decorator
# import eventlet
import signal


# def call_slice(bugInstance, JDClass, re1, re2, src_path, single_bug):
#     slicing_result = bugInstance.do_slice(bugInstance.jar_loc, JDClass)
#     if slicing_result:
#         src_code = [linecache.getline(src_path, int(line_number)).strip() for
#                     line_number in slicing_result]
#         # slice_bug_num += 1
#         re1.writelines(src_code)  # 源码数据
#         re1.write("\n__________________________\n")
#         # re2.write("original num:"+str(ori_bug_num)+'\n')
#         re2.writelines(single_bug[:-1])
#         re2.write("lines:")
#         re2.write(','.join(slicing_result))
#         re2.write("\n\n__________________________\n")
# def handler(signum, frame):
#     print("time out...")
#     raise Exception

def main(pattern_name, jar_name):
    base = "/data/bugDetection/bugdata"
    # ori = os.path.join(base,"dep_bug_ori3",pattern_name+".txt")   # 处理后的各种pattern的文件
    ori = os.path.join(base,"dep_bug_res_new",pattern_name+".txt")   # 处理后的各种pattern的文件
    res_src = os.path.join(base, "user_dep_res/pattern_src", pattern_name)  # 源码
    res_line = os.path.join(base, "user_dep_res/pattern_line", pattern_name)  # 行数

    wala_slicer_jar = "/data/bugDetection/bugDetect/resource/"+jar_name  #切片jar路径
    # jvm_path = "/data/bugDetection/" + jdk + "/jre/lib/amd64/server/libjvm.so"
    # err_log = "/data/bugDetection/bugDetect/data_collection/errlog/test2/" + log_name
    # with open(err_log, "r") as log:
    #     line = log.readline()
    #     processed_num = 0
    #     while line:
    #         if line.split(' ') == "processing":
    #             processed_num += 1
    jvm_path = jpype.getDefaultJVMPath()
    # jvm_path = "/data/bugDetection/"+jdk+"/jre/lib/amd64/server/libjvm.so"
    if not jpype.isJVMStarted():
        jpype.startJVM(jvm_path,
                       "-ea",
                       '-Xms5120m',
                       '-Xmx5120m',
                       '-Djava.class.path=%s' % wala_slicer_jar,
                       interrupt = True)
        # jpype.attachThreadToJVM()
    JDClass = jpype.JClass("org.example.WALASlicer")
    with open(ori, "r") as f:
        with open(res_src, "a") as re1:
            with open(res_line, "a") as re2:
                cont = True
                single_bug = []
                start = 0
                ori_bug_num = 0
                slice_bug_num = 0
                dir_bug_num = 0
                while cont:
                    cont = f.readline()
                    single_bug.append(cont)
                    if cont == "\n":
                        start1 = time.time()
                        # ori_bug_num += 1
                        # if ori_bug_num < int(processed_num):
                        #     single_bug = []
                        #     continue

                        print("processing no."+str(ori_bug_num)+" bug...")
                        try:
                            mthdName = single_bug[start+3].split(': ')[1].strip(" \n")
                            mthdSig = single_bug[start+4].split(': ')[1].strip(" \n")
                            mthdStart = single_bug[start+5].split(': ')[1][:-1].strip()
                            mthdEnd = single_bug[start+6].split(': ')[1][:-1].strip()
                            bugLine = single_bug[start+7].split(': ')[1][:-1].strip()
                            if pattern_name == "RCN_REDUNDANT_NULLCHECK_OF_NONNULL_VALUE":
                                mthd2Name = single_bug[start+7].split(': ')[1].strip(" \n")
                                mthd2Sig = single_bug[start+8].split(': ')[1].strip(" \n")
                                mthd2Start = single_bug[start+9].split(': ')[1][:-1].strip()
                                mthd2End = single_bug[start+10].split(': ')[1][:-1].strip()
                                bugLine = single_bug[start+11].split(': ')[1][:-1].strip()
                                temp1 = mthd2Start
                                temp2 = mthd2End
                                if temp2 >= bugLine >=temp1:
                                    mthdName, mthdSig, mthdStart, mthdEnd = mthd2Name, mthd2Sig, mthd2Start, mthd2End

                            if mthdStart and mthdEnd and bugLine:
                                bugInstance = depBugInfo(single_bug[start].split(': ')[1].strip(" \n"), \
                                                         single_bug[start+1].split(': ')[1][:-1].strip(),\
                                                      single_bug[start+2].split(': ')[1][:-1].strip(), \
                                                    mthdName, mthdSig, int(mthdStart)-1, int(mthdEnd)+1, int(bugLine))


                                src_loc = os.path.splitext(bugInstance.jar_loc)[0]+"-sources"

                                if not os.path.isdir(src_loc):
                                    zip_file = zipfile.ZipFile(os.path.splitext(bugInstance.jar_loc)[0]+"-sources.jar")
                                    zip_file.extractall(src_loc)

                                src_path = bugInstance.find_src(src_loc)
                                if "/home/user/zgj" in src_path:
                                    start2 = time.time()
                                    print("begin slicing...")
                                    slicing_result = bugInstance.do_slice(bugInstance.jar_loc, JDClass)
                                    end2 = time.time()
                                    if slicing_result:
                                        print("slicing time:", end2 - start2)
                                        src_code = '\n'.join([linecache.getline(src_path, int(line_number)).strip() \
                                                              for line_number in slicing_result])
                                        slice_bug_num += 1
                                        re1.write("class:")
                                        re1.write(bugInstance.classPath)
                                        re1.write(" lines:")
                                        re1.write(','.join(slicing_result))
                                        re1.write("\n")
                                        # re1.write("source code:\n")
                                        re1.writelines(src_code)  # 源码数据
                                        re1.write("\n__________________________\n")
                                        # re2.write("original num:"+str(ori_bug_num)+'\n')
                                        re2.writelines(single_bug[:-1])
                                        re2.write("lines:")
                                        re2.write(','.join(slicing_result))
                                        re2.write("\n")
                                        re2.write("path:")
                                        re2.write(src_path)
                                        re2.write("\n")
                                        re2.write("\n\n__________________________\n")


                                    # result = find_code(proj, filePath, st_line, ed_line, bug_line)
                                    # start2 = time.time()
                                    # slicing_result = bugInstance.do_slice(bugInstance.jar_loc, JDClass)
                                    # signal.signal(signal.SIGALRM, handler)
                                    # signal.alarm(20)
                                    # try:
                                    #     call_slice(bugInstance, JDClass, re1, re2, src_path, single_bug)
                                    # except Exception as e:
                                    #     print("slice return null,direct extracting...")
                                    #     dir_extra_result = extra(src_path, bugInstance.mthdStart, bugInstance.mthdEnd, bugInstance.bugLine)
                                    #     dir_bug_num += 1
                                    #     re1.writelines(dir_extra_result[0])  # 源码数据
                                    #     re1.write("\n__________________________\n")
                                    #     # re2.write("original num:" + str(ori_bug_num) + '\n')
                                    #     re2.writelines(single_bug[:-3])
                                    #     re2.write("lines:")
                                    #     re2.write(str(dir_extra_result[1]).strip('[]'))
                                    #     re2.write("\n\n__________________________\n")
                                    # try:

                                    # start2 = time.time()
                                    # slicing_result = bugInstance.do_slice(bugInstance.jar_loc, JDClass)
                                    # end2 = time.time()

                                    # except Exception:
                                    #     slicing_result = None
                                    # start2 = time.time()
                                    # q = multiprocessing.Queue()
                                    # 父进程需要和子进程通信，通信数据放在队列里，以pickle读取，应该是python数据类型
                                    # p = multiprocessing.Process(target=bugInstance.do_slice, args=[q, bugInstance.jar_loc, jvm_path, wala_slicer_jar])
                                    # p = multiprocessing.Process(target=bugInstance.do_slice, args=[q, bugInstance.jar_loc, JDClass])
                                    # p.daemon = True
                                    # p.start()
                                    # p = multiprocessing.Pool()
                                    # p.daemon = True
                                    # p.apply_async(bugInstance.do_slice, args=[q, bugInstance.jar_loc, JDClass])
                                    # p.close()
                                    # p.join()
                                    # slicing_result = q.get(True)
                                    # p.terminate()
                                    # end2 = time.time()

                                    # eventlet.monkey_patch()
                                    # with eventlet.Timeout(20, False):
                                    #     slicing_result = bugInstance.do_slice(bugInstance.jar_loc, JDClass)
                                    #     end2 = time.time()
                                    #     print("slicing time:",end2 - start2)
                                    #     if slicing_result:
                                    #         print("start writing slice...")
                                    #         src_code = [linecache.getline(src_path, int(line_number)).strip() for
                                    #                     line_number in slicing_result]
                                    #         slice_bug_num += 1
                                    #         re1.writelines(src_code)  # 源码数据
                                    #         re1.write("\n__________________________\n")
                                    #         # re2.write("original num:"+str(ori_bug_num)+'\n')
                                    #         re2.writelines(single_bug[:-1])
                                    #         re2.write("lines:")
                                    #         re2.write(','.join(slicing_result))
                                    #         re2.write("\n\n__________________________\n")
                                    #     flag = 1
                                    # if flag == 0:
                                    #     print("slice return null,direct extracting...")
                                    #     dir_extra_result = extra(src_path, bugInstance.mthdStart, bugInstance.mthdEnd, bugInstance.bugLine)
                                    #     dir_bug_num += 1
                                    #     re1.writelines(dir_extra_result[0])  # 源码数据
                                    #     re1.write("\n__________________________\n")
                                    #     # re2.write("original num:" + str(ori_bug_num) + '\n')
                                    #     re2.writelines(single_bug[:-3])
                                    #     re2.write("lines:")
                                    #     re2.write(str(dir_extra_result[1]).strip('[]'))
                                    #     re2.write("\n\n__________________________\n")



                                    # else:
                                    # print("direct extracting...")
                                    # dir_extra_result = extra(src_path, bugInstance.mthdStart, bugInstance.mthdEnd, bugInstance.bugLine)
                                    # dir_bug_num += 1
                                    # re1.write("class:")
                                    # re1.write(bugInstance.classPath)
                                    # re1.write("\nlines:")
                                    # re1.write(str(dir_extra_result[1]).strip('[]'))
                                    # re1.write("\n")
                                    # # re1.write("source code:\n")
                                    # re1.writelines(dir_extra_result[0])  # 源码数据
                                    # re1.write("\n__________________________\n")
                                    # # re2.write("original num:" + str(ori_bug_num) + '\n')
                                    # re2.writelines(single_bug[:-1])
                                    # re2.write("lines:")
                                    # re2.write(str(dir_extra_result[1]).strip('[]'))
                                    # re2.write("\n\n__________________________\n")

                                    # end4 = time.time()
                                    # print("io writing time:", end4 - start4)
                                else:
                                    print("source code not found")
                            single_bug = []
                            start = 0
                            end1 = time.time()

                            print("total time:",end1 - start1)
                        except (ValueError, IndexError):
                        # except IndexError as e:
                            print("original file got problem")
                            single_bug = []
                            start = 0
                            continue
                print("num of "+pattern_name+" is "+str(ori_bug_num))
                print("slicing num of " + pattern_name + " is " + str(slice_bug_num))
                # print("directly extracting num of " + pattern_name + " is " + str(dir_bug_num))

    print("all done!")
    jpype.shutdownJVM()
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', '-n', help='name of every pattern')
    parser.add_argument('--jar', '-j', help='name of slicing jar')
    # parser.add_argument('--log','-l',help='log name')
    # parser.add_argument('--jdk', '-e',help='jdk name')
    args = parser.parse_args()
    main(args.name, args.jar)

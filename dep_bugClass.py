import os
import zipfile
import tempfile
import re
import jpype
import linecache



class depBugInfo:
    def __init__(self,jar_loc,classPath,filePath,methodName,methodSig,mthdStart,mthdEnd,bugLine):
        # self.proj = proj
        self.jar_loc = jar_loc
        self.classPath = classPath
        self.filePath = filePath
        self.mthdName = methodName
        self.mthdSig = methodSig
        self.mthdStart = mthdStart
        self.mthdEnd = mthdEnd
        self.bugLine = bugLine
        # self.lines = lines
        self.proj_src_path = ""
        self.proj_bin_path = ""

    def find_src(self,src_loc):
        '''
        find whether the class has the corresponding source code
        :return:
        '''
        if self.filePath.split(".")[-1] != "java":
            return None
        if not self.filePath:
            self.filePath = self.classPath.split("$")[0].replace('.', '/')+".java"
        return os.path.splitext(self.jar_loc)[0]+"-sources/"+self.filePath
        # for root, ds, fs in os.walk(src_loc):
        #     for f in fs:  # f是目录下的所有文件名 str
        #         path = os.path.join(root, f)
        #         if self.filePath in path:
        #             return path
        #
        # return None

    def find_class(self):
        '''
        find a class' self location
        :return:jar's location
        '''
        # 忽略dep??
        for root, ds, fs in os.walk(self.proj_bin_path):
            for f in fs:  # f是目录下的所有文件名 str
                if os.path.splitext(f)[-1]=='.jar':
                    jarPath = os.path.join(root, f)
                    jarFile = zipfile.ZipFile(jarPath)
                    if(self.classPath.replace('.','/')+".class" in jarFile.namelist()):
                        # print(jarFile.filename)
                        return jarPath
        return None

    def add_dependency(self, zipname, jar_location):
        '''
        add the method's dependencies to config file
        :return:
        '''

        # !!!! change focus
        # zipname = "E:\\com.ibm.wala.core-1.5.4.jar"
        tmpfd, tmpname = tempfile.mkstemp(dir=os.path.dirname(zipname))
        os.close(tmpfd)
        dep_lst = ["Primordial,Java,stdlib,none", "Primordial,Java,jarFile,primordial.jar.model"]

        temp = re.split('L|\(|\)|\;|\[|\]', self.mthdSig)
        # 内置类型的签名表示都是一个字符
        # dep_paths = [temp[i]+".class" for i in range(len(temp)) if temp[i]!='' and len(temp[i])>1]
        # methods' dependency class path
        dep_paths = [temp[i]+".class" for i in range(len(temp)) if temp[i]!='' and '/' in temp[i]]

        for root, ds, fs in os.walk(self.proj_bin_path):
            for f in fs:  # f是目录下的所有文件名 str
                if len(dep_paths)==0:
                    break
                if os.path.splitext(f)[-1]=='.jar':
                    jarPath = os.path.join(root, f)
                    jarFile = zipfile.ZipFile(jarPath)
                    for i in range(len(dep_paths)):
                        if dep_paths[i] in jarFile.namelist() and jarPath != jar_location:
                            # print("dep", jarPath)
                            jarPath = "Extension,Java,jarFile,"+jarPath
                            dep_lst.append(jarPath)
        if dep_lst == ["Primordial,Java,stdlib,none", "Primordial,Java,jarFile,primordial.jar.model"]:
            return

        else:
            data = bytes('\n'.join(dep_lst), encoding="utf8")

            with zipfile.ZipFile(zipname, 'r') as zin:
                with zipfile.ZipFile(tmpname, 'w') as zout:
                    zout.comment = zin.comment
                    for item in zin.infolist():
                        if item.filename != "primordial.txt":
                            zout.writestr(item, zin.read(item.filename))

            os.remove(zipname)
            os.rename(tmpname, zipname)
            # os.remove(tmpname)
            with zipfile.ZipFile(zipname, mode='a', compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("primordial.txt", data)

            return

    def rmv_exclusion(self, zipname):   #zipname-->walaslicerjar
        '''
        remove the class in Java60RegressionExclusions.txt
        :param zipname:
        :return:
        '''
        tmpfd, tmpname = tempfile.mkstemp(dir=os.path.dirname(zipname))
        os.close(tmpfd)
        dep_lst = ["java\/awt\/.*","javax\/swing\/.*","sun\/awt\/.*","sun\/swing\/.*",\
                   "com\/sun\/.*","sun\/.*","org\/netbeans\/.*","org\/openide\/.*",\
                   "com\/ibm\/crypto\/.*","com\/ibm\/security\/.*","dalvik\/.*",\
                   "apple\/.*","com\/apple\/.*","jdk\/.*","org\/omg\/.*","org\/w3c\/.*"]


        temp = re.split('L|\(|\)|\;|\[|\]', self.mthdSig)
        dep_paths = [temp[i] for i in range(len(temp)) if temp[i]!='' and '/' in temp[i]]
        for dep in dep_paths:
            for i in reversed(range(len(dep_lst))):
                if '/'.join(dep_lst[i].split("\/")[:-1]) in dep:
                    dep_lst.pop(i)

        data = bytes('\n'.join(dep_lst), encoding="utf8")

        with zipfile.ZipFile(zipname, 'r') as zin:
            with zipfile.ZipFile(tmpname, 'w') as zout:
                zout.comment = zin.comment
                for item in zin.infolist():
                    if item.filename != "Java60RegressionExclusions.txt":
                        zout.writestr(item, zin.read(item.filename))

        os.remove(zipname)
        os.rename(tmpname, zipname)
        # os.remove(tmpname)
        with zipfile.ZipFile(zipname, mode='a', compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("Java60RegressionExclusions.txt", data)
        azip = zipfile.ZipFile(zipname)
        exclu = azip.read("Java60RegressionExclusions.txt").decode('utf-8')
        azip.close()

        return

    # @timeout_decorator.timeout(20, use_signals=False)
    # def do_slice(self, q, jar_location, jvm_path, jar_path):
    def do_slice(self, jar_location, JDClass):
        '''
        invoke JVM to do java program slicing
        :param jar_location:
        :param jar_path:
        :return:
        '''

        # !!!change focus!!!
        # jvm_path = jpype.getDefaultJVMPath()
        # # print(jvm_path)
        # if not jpype.isJVMStarted():
        #     jpype.startJVM(jvm_path, "-ea", '-Djava.class.path=%s' % jar_path,interrupt = True)
        # JDClass = jpype.JClass("org.example.WALASlicer")
        jd = JDClass(jar_location, None)
        class_input = 'L' + self.classPath.replace('.', '/')
        result = jd.sliceJuliet(class_input, self.mthdName, self.mthdSig, self.bugLine)
        # print(result)
        if result:
            result = str(result).strip('[]').split(', ')
            for i in reversed(range(len(result))):
                if int(result[i]) > self.mthdEnd or int(result[i]) < self.mthdStart:
                    result.pop(i)

        # q.put(result)
        return result
        # jpype.shutdownJVM()
    #
    #
    # def pro_result(self, q, jar_location, jar_path):
    #     result = self.do_slice(jar_location, jar_path)
    #     if result == None:
    #         return None
    #     result = str(result).strip('[]').split(', ')
    #     for i in reversed(range(len(result))):
    #         if int(result[i]) > self.mthdEnd or int(result[i]) < self.mthdStart:
    #             result.pop(i)
    #     return result
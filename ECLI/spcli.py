import argparse
import textwrap
import os
import socket
from subprocess import PIPE, Popen
import sys
from os import path
import platform
import errno


class Utilities:

    def __init__(self):
        pass

    def create_empty_file(self,fname):
        with open(fname, "w") as f:
            f.write()
            f.close()
        return fname

    @staticmethod
    def create_directory(directory):
        try:
            os.makedirs(directory)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        return directory

    @staticmethod
    def write_to_file(fname,string):
        print(string)
        with open(fname,"w") as f:
            f.write(string)
            f.close()

    @staticmethod
    def read_from_file(fname):
        with open(fname,"r") as f:
            string=f.readline()
            f.close()
        return string

    def get_file_content(self, fname):
        """
        Read file content and return a list

        :param fname:
        :return:
        """
        content = list()
        with open(fname) as f:
            content = f.readlines()
        return content

    def get_command_statements(self, command, arraylist):

        content = list()

        if not arraylist:
            content.append(command)
        else:
            for line in arraylist:
               content.append(command + '"{}"'.format(line.strip('\n')))

        return (content)

    def set_command_file(self, connection, command, fileName, arraylist):

        """
        Read input file conents in a list, create full command set and write to file
        Return the file created
        :param connection:
        :param command:
        :param fileName:
        :return:
        """

        outfile = fileName
        with open(outfile, "w") as f:
            f.write(connection + '\n')
            for e in self.get_command_statements(command, arraylist):
                f.write(e + '\n')
            f.write("close")
            f.close()
        return outfile

    def add_job_extention(self, arraylist, postfix):

        tlist = list()
        for e in arraylist:
            tlist.append(str(e.strip('\n')) + ".{}".format(postfix))
        return tlist

    def add_path(self, arraylist, directorypath):

        tlist = list()
        for e in arraylist:
            tlist.append(os.path.join(directorypath,e))
        return tlist

class System:

    def execute_cli(self, cmdfile):
        p = list()
        if platform.system().__eq__("Windows"):
            p = Popen((os.path.join(os.getcwd(), "cli.cmd") + " --cmdfile {}".format(cmdfile)), stdout=PIPE,
                      stderr=PIPE)
        else:
            p = Popen([os.path.join(os.getcwd(), "cli.sh"), " --cmdfile {}".format(cmdfile)], stdout=PIPE, stderr=PIPE)

        out, err = p.communicate()
        e_code = p.returncode
        output = list()
        error =list()

        # print("-----------------------------------------")
        try:

            for i in out.split(b'\n'):
                string = i.decode("utf-8")

                output.append(string)
        except:
            print("")
        try:
            for i in err.split(b'\n'):
                string = i.decode("utf-8")
                error.append(string)
        except:
            print("Error : creating err list")

        return {'output':output,'error':error,'exitcode':e_code}


class Connection:

    def __init__(self, hostname=socket.gethostname(), port="8080", username="admin", password="admin"):
        self.hostname = str(hostname)
        self.port = str(port)
        self.username = str(username)
        self.password = str(password)

    def get_connection_string(self,env="default"):
        if (env.__eq__("default")):
            return str("connect --h {}:{} --u {} --p {}".format(self.hostname, self.port, self.username, self.password))
        else:
            return  self.get_environment(env)

    def set_hostname(self, hostname):
        self.hostname = hostname

    def set_port(self, port):
        self.port = port

    def set_username(self, username):
        self.username = username

    def set_password(self, password):
        self.password = password

    @staticmethod
    def close_connection(self):
        return "close"


    def set_environment(self,env):
        """
        Set Environment connection details dev,uat,sit,prod
        :param self:
        :return:
        """
        print("Inside set environement method")
        print(self.get_connection_string())
        Utilities.write_to_file(os.path.join(Utilities.create_directory("config"),env),str(self.get_connection_string()))

    def get_environment(self,env):
        env=os.path.join("config",env)
        return Utilities.read_from_file(env)


class CommandHandler:

    def __init__(self):

        self.utility = Utilities()
        self.run = System()

    def get_command_results(self,connection,command,outfile,dataflow_list):
        """

        :param connection: Environment connection string dev,uat,sit,prod....
        :param command: Command to run like "dataflow list"
        :param outfile: File keeps connection and  commandlets
        :param dataflow_list: array of data flow/process flow file list
        :return: dictonary of output,error and command exitcode
        """
        tfile = self.utility.set_command_file(connection, command, outfile, dataflow_list)
        result_dict = self.run.execute_cli(tfile)
        return result_dict

    def remove_empty_rows(self,t_list):
        for e in t_list:
            string = str(e)
            if len(string.strip()).__eq__(0):
                t_list.remove(e)
        return list(t_list)

    def remove_format_rows(self,t_list):
        for e in t_list:
            string = str(e)

            if len(string.strip()).__eq__(0):
                t_list.remove(e)
        return list(t_list)

    def remove_empty_elements(self,t_list):

        tmp_list=[x.strip() for x in t_list]
        for i in tmp_list:
            if len(i) == 0:
                tmp_list.remove(i)

        return list(tmp_list)

    def get_dataflow_list(self,connection):
        command = "dataflow list"
        result = self.get_command_results(connection,command,"tmp.out",list())

        l = list()
        if result.get('exitcode') != 0:
            print("ERROR : exitCode = ", result.get('exitcode'))
            for i in result.get('error'):
                print(i)
                exit(1)
        else:

            dflist=result.get('output')
            for e in dflist:
                string = str(e)
                if len(string.strip()).__eq__(0):
                    dflist.remove(e)
            dflist = dflist[4:len(dflist) - 2]
            for j in dflist:
                t = j.split('|')
                dict_object = {'NAME': t[1].strip(), 'TYPE': t[2].strip(), 'EXPOSED': t[3].strip()}
                l.append(dict_object)

        return l

    def dataflow_list(self, connection):
        result=self.get_dataflow_list(connection)

        for i in result:
            print(i.get('NAME'),i.get('TYPE'),i.get('EXPOSED'))

    def get_flow_version(self,connection):
        df_dictonary=self.get_dataflow_list(connection)
        df_list =list()
        for d in df_dictonary:
            df_list.append(d.get('NAME'))
        print(df_list)

        command="dataflow version list --n "
        # element=list()
        # element.insert(0,df_list.pop(1))
        # print(element)
        result = self.get_command_results(connection,command,"tmp.out",df_list)
        t_list = self.remove_empty_rows(result.get('output'))
        list_of_dict_objects=list()
        for e in t_list:
            string =str(e)
            # print(string)
            try:
                for i in df_list:
                    # print(i)
                    if string.strip().__eq__(i.strip()):


                        idx=t_list.index(e)
                        data=t_list.pop(idx+4).split('|')
                        header=list(t_list.pop(idx+2).split('|'))
                        header.append('NAME')
                        data.append(e)
                        header=self.remove_empty_elements(header)
                        data=self.remove_empty_elements(data)
                        dict_object=dict(zip(header,data))
                        list_of_dict_objects.append(dict_object)


            except:
                print("ERROR**")
            # print("=========================================")
        print(list_of_dict_objects)

    def check_out_list(self,connection,command):
        self.get_flow_version(connection)

    def dataflow_export(self, connection,command, fileName):
        command = "{}  --e True --o exports --d ".format(command)
        tfile = self.utility.set_command_file(connection, command, "dataflowexport.out",
                                              self.utility.get_file_content(fileName))
        result=self.run.execute_cli(tfile)
        print(result)
        return "executed dataflow export "

    def dataflow_import(self, connection,command, fileName):
        command = "{} --u True --f ".format(command)
        dflist = self.utility.add_path(self.utility.add_job_extention(self.utility.get_file_content(fileName), "df"),"exports")
        tfile = self.utility.set_command_file(connection, command, "dataflowimport.out", dflist)
        self.run.execute_cli(tfile)
        print(tfile)

    def help(self):
        command="help"

class ArgumentHandler:

    commandList = ('dataflow export', 'processflow export', 'dataflow list','check out')

    def __init__(self, args):

        self.args=args
        self.cmd = CommandHandler()
        self.connection=Connection()


    def run(self):
        self.switch()

    def switch(self):

        if str(self.args.command).__eq__("dataflow list"):
            self.cmd.dataflow_list(self.connection.get_connection_string(self.args.env))

        elif str(self.args.command).__eq__("dataflow export"):
            try:
                #self.connection.set_hostname(self.args.servername)
                self.cmd.dataflow_export(self.connection.get_connection_string(self.args.env),self.args.command, self.args.filename)
            except:
                print("Invalid arguments ... try help : [ {} -h ]".format(path.basename(sys.argv[0])))

        elif str(self.args.command).__eq__("dataflow import"):
            try:
                #self.connection.set_hostname(self.args.servername)
                self.cmd.dataflow_import(self.connection.get_connection_string(self.args.env),self.args.command, self.args.filename)
            except:
                print("Invalid arguments ... try help : [ {} -h ]".format(path.basename(sys.argv[0])))

        elif str(self.args.command).__eq__("check out"):
            try:

                # self.connection.set_hostname(self.args.servername)
                self.cmd.check_out_list(self.connection.get_connection_string(self.args.env), self.args.command)
            except:
                print("Invalid arguments ... try help : [ {} -h ]".format(path.basename(sys.argv[0])))

        # switcher={
        #
        #     #'dataflow list': "hello umesh"
        #     'dataflow list':self.cmd.dataflow_list(Connection().get_connection_string()),
        #     'dataflow export':self.cmd.dataflow_export(Connection(self.hostname).
        #                                                 get_connection_string(),self.filename)
        #     # 'dataflow import':self.cmd.dataflow_import(self.c.set_hostname(self.args.servername).
        #     #                                            get_connection_string(),self.args.filename)
        #
        # }
        # func=switcher.get(str(argument),lambda:"Invalid command")
        # print (func)

    def validate_arguments(self):
        print(self.args)
        #
        # else:
        #     if self.args.command not in self.commandList:
        #         print("Supported commands are:")
        #         for e in self.commandList:
        #             print(e)
        #         exit(1)


def main():
    # cmd.dataflow_export(c.get_connection_string(),"dataflowexport.txt")
    # cmd.dataflow_import(c.get_connection_string(), "dataflowexport.txt")
    parser = argparse.ArgumentParser()
    #parser.add_argument("-h",help="Usage : spcli.py -e dev -c dataflow list")
    parser.add_argument("-c", "--command", help=textwrap.dedent("""Usage: Spectrum command name
                                               eg: "dataflow list"
                        """), type=str)
    parser.add_argument("-s", "--servername", help="Host name of machine where to execute command")
    parser.add_argument("-u", "--username", help="")
    parser.add_argument("-pw", "--password", help="")
    parser.add_argument("-p", "--port", help="")
    parser.add_argument("-f", "--filename",
                        help="File name having names of [dataflows] OR [processflows] OR [subflows]")
    parser.add_argument("-e","--env",help="")

    parser.add_argument("-setenv",help="Set dev,sit,uat,prod environemnt connection variables "
                            "-e 'environmentType' -s 'servername' -p 'port' -u 'username' -pw 'password' "
                                       "-setenv=y -e dev -s localhost -p 9090 -u admin -pw admin")

    args = parser.parse_args()
    arg_exist=0

    for i in vars(args):
        if not str(getattr(args, i)).__eq__('None'):
            arg_exist=1
            break
    if arg_exist == 0:
        print("""
            Note    :Must set environment before running any command
            Example :spcli.py -setenv=y -e dev -s localhost -p 9090 -u admin -pw admin
            Usage   :spcli.py -e "environment" -c "command" 
            Example :spcli.py -e dev -c "dataflow list"
            For help type:  spcli.py -h 
            """)
        exit(1)
    if str(args.setenv).__eq__("y"):
        print("Set environment ")
        c=Connection(args.servername,args.port,args.username,args.password)
        c.set_environment(args.env)
    else:
        arg_handler = ArgumentHandler(args)
        arg_handler.run()


if __name__ == '__main__':
    main()


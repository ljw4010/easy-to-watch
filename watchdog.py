#!/usr/bin/env python
# encoding: utf-8
"""
@file: watchdog.py
@version: 1.1
@history: 2016/10/25 10:39
@history: 2016/12/01 15:51
@author: ljw4010@sina.cn
"""

import os,sys,time,getpass,logging,copy
import socket
from optparse import OptionParser,OptionGroup

class WatchDog():
    def __init__(self,app_name,work_dir=None,app_port=None,start_scripts=None,action=None,pid_file=None,proc_num=None,check_times=None,wait_time=None,cron_task=None):
        
        #初始化参数
        self.app_name = app_name
        self.app_port = app_port
        self.work_dir = work_dir
        self.proc_num = proc_num
        self.start_scripts = start_scripts
        self.pid_file = pid_file
        self.check_times = check_times
        self.action = action
        self.SHELL = os.environ.get('SHELL', '/bin/sh')
        self.task = cron_task
        self.default_task = '*:*:*:*:*'
        #任务初始化
        if not self.task:
            self.task = self.default_task
        #检查次数初始化
        if not self.check_times:
            self.check_times = 3
        
        #脚本当前路径
        self.file_path = os.path.split(os.path.realpath(sys.argv[0]))[0] 
        #获取pid命令
        self.get_pid_cmd = '''ps -ef | grep -E '[^-]+%s' | grep -v -w grep | grep -v -w watchdog.py | grep -v -w watchdog|grep -v -w tail | grep -v -w less | grep -v -w vi| grep -v -w vim''' %self.app_name
        
        #初始化启动脚本
        if not self.start_scripts:
            self.start_scripts = "start_%s.sh" % app_name

        #可视通默认脚本
        self.app_kst_script = "control"
       
        #tomcat启动脚本及路径
        self.tomcat_script = "startup.sh"
        self.catalina_dir = self.work_dir + os.sep + 'bin'
        
        #初始化pid文件名
        if not self.pid_file:
            self.pid_file = self.app_name + ".pid"
        
        #每次检测等待时间 (秒)
        self.wait_time = wait_time
        if not self.wait_time:
            self.wait_time = 2

        #日志处理
        logging.basicConfig(level=logging.DEBUG,
            format = '%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt = '%a, %d %b %Y %H:%M:%S',
            filename = self.app_name+'_cron.log',
            filemode = 'a+')

        if time.strftime("%H:%M",time.localtime()) == '02:00':
            with open(self.app_name+'_cron.log','w+') as f:
                f.truncate()
        #任务处理
        os.chdir(self.file_path)
        def check_task(task):
            """简单检测task是否符合要求"""
            real_task = self.default_task
            try:
                task = task.split(":")
            except:
                logging.warning("'%s' task format setting error,now use default!" %self.task)
                task = self.default_task
            if len(task)==5:
                real_task = task[0] + ' ' + task[1] + ' ' + task[2] + ' ' + task[3] + ' ' + task[4]  
            return real_task
        task = check_task(self.task)
        self.CRON_CMD = task + " cd " + self.file_path + '; /usr/bin/env python ' + sys.argv[0] + ' ' + ' '.join(sys.argv[1:]) + ' > /dev/null 2>&1'

    def _is_port_exist(self):
        '''端口检测'''
        port_flag = True
        address = ('127.0.0.1', int(self.app_port))

        #socket_type = socket.SOCK_STREAM if protocol == 'tcp' else socket.SOCK_DGRAM
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.bind(address)
        except Exception, e:
            logging.info("port[%s] is listening!" %self.app_port)
        else:
            logging.info('port[%s] is lost! \n' % (self.app_port))
            port_flag = False
        finally:
            client.close()
            return port_flag

    def _is_scripts_exist(self,scripts):
        '''脚本检测'''
        filepath = []
        script_flag = False

        if os.path.exists(scripts):
            script_flag = True
            return script_flag

        for dirpath, dirnames, filenames in os.walk(self.work_dir):
            filepath.append(os.path.join(dirpath, scripts))

        # 检索List中文件路径是否存在,存在的话读取pid文件数据
        for real_dir in filepath:
            if os.path.exists(real_dir):
                logging.info("%s start-script do exists, you can also start it!" % self.app_name)
                script_flag = True
                return script_flag
        if not script_flag:
            logging.info("%s start-script do not exists !" %self.app_name)
            return script_flag

    def _is_pid(self):
        '''进程检测'''
        pid_list = []

        for line in os.popen(self.get_pid_cmd).readlines():
            pid_list.append(line.split()[1])

        return pid_list 

    def _is_pid_exist(self,pid_list):
            
        if len(pid_list) <= 0:
            logging.info("%s process is not existed, or start failed!" % self.app_name)
        else:
            logging.info("%s process is existed ,current pid:%s!" % (self.app_name,pid_list))

    def _is_pid_exist_status(self,pid_list):
        if len(pid_list) <= 0:
            return False
        else:
            return True

    def _crontab(self,cmd):
        '''添加|删除定时任务 '''
        job = CronTab(self.CRON_CMD,self.app_name)
        if cmd == 'remove':
            job._remove()
        if cmd == 'add':
            job._add()
        if cmd == 'disenable':
            job._disenable()

    def _check_proc(self,work_dir,scripts):
        time.sleep(self.wait_time)
        for times in range(0,self.check_times):
            if not self._is_pid():
                os.chdir(work_dir)
                if self.action:
                    os.system(self.SHELL + ' ' + scripts + ' ' + self.action + ' > /dev/null 2>&1')
                else:
                    os.system(self.SHELL + ' ' + scripts + ' > /dev/null 2>&1')
                if times == (self.check_times - 1) :
                    self._crontab('disenable')
            else:
                continue
            time.sleep(self.wait_time)
        self._is_pid_exist(self._is_pid())
 
        result = self._is_pid_exist_status(self._is_pid())
        if result:
            print "starting successfull."
        else:
            print "starting failed."

    def _start_proc(self):
        '''启动程序'''

        if self.app_name in ['front', 'back']:
            if self._is_scripts_exist(self.tomcat_script):
                os.chdir(self.catalina_dir)
                os.system(self.SHELL + ' ' + self.tomcat_script + ' > /dev/null 2>&1')
                self._crontab('add')
                self._check_proc(self.catalina_dir,self.tomcat_script)
            else:
                logging.info("%s do not exists!"%self.tomcat_script)

        elif self.app_name in ['lbs', 'tms', 'rms', 'relay']:
            if self._is_scripts_exist(self.app_kst_script):
                os.chdir(self.work_dir)
                app_kst_script = self.SHELL + ' ' + self.app_kst_script + ' start' + ' > /dev/null 2>&1'
                os.system(app_kst_script)
                self._crontab('add')
                self._check_proc(self.work_dir,app_kst_script)
            else:
                logging.info("%s do not exists!"%self.app_kst_script)

        else:
            if self._is_scripts_exist(self.start_scripts):
                os.chdir(self.work_dir)
                if self.action:
                    os.system(self.SHELL + ' '  + self.start_scripts + ' ' + self.action + ' > /dev/null 2>&1')
                else:
                    os.system(self.SHELL + ' '  + self.start_scripts + ' > /dev/null 2>&1')
                self._crontab('add')
                self._check_proc(self.work_dir,self.start_scripts)
            else:
                logging.info("start script do not exist,plz check work space is ok? ")

    def _stop_proc(self):
        '''停止进程'''
        if len(self._is_pid()) > 0:
            for pid in self._is_pid():
                killpid = "kill -9 %d"%int(pid)
                if os.system(killpid):
                    logging.info("exec %s failed" % killpid)
                else:
                    logging.info("exec %s success" % killpid)
        else:
            logging.info("pid list is null, no processes need to kill !")
                
    def _is_pid_file_exist(self):
        '''检测pid文件'''
        real_path = ''
        pid = ''
        file_path = []

        def get_pid(real_path):
            pid = ''
            f = open(real_path, 'r')
            try:
                pid = f.read().split()[0]
            except:
                logging.info("pid file is empty!")
            f.close()
            return pid

        if os.path.exists(self.pid_file):
            real_path = self.pid_file
            pid = get_pid(real_path)
        else:
            for dir_path, dir_names, file_names in os.walk(self.work_dir):
                file_path.append(os.path.join(dir_path, self.pid_file))

            # 检索List中文件路径是否存在,存在的话读取pid文件数据
            for real_dir in file_path:
                if os.path.exists(real_dir):
                    real_path = real_dir
                    pid = get_pid(real_dir)
                    break
        return real_path,pid

    #状态判断
    #No.1 支持pid文件方式 
    def _judge_status_section_1(self):
        pidfile_path,pid_in_pidfile = self._is_pid_file_exist()
        pid_list = self._is_pid()
        self._is_pid_exist(pid_list)

        result = self._is_pid_exist_status(pid_list)
        if result:
            print "process exists."

        self._judge_status_section_3()
        self._judge_status_section_4()
        # 1.pid文件不存在,且进程也不存在
        if not os.path.exists(pidfile_path) and len(pid_list) == 0:
            logging.info("%s process is not running, start it now !" % self.app_name)
            self._start_proc()
            sys.exit(0)

        #2. pid文件不存在，进程存在
        if not os.path.exists(pidfile_path) and  len(pid_list) > 0:
            logging.info("Not found pid file ,but %s process do exists, restart it now !" % self.app_name)
            self._stop_proc()
            time.sleep(self.wait_time)
            self._start_proc()
            sys.exit(0)

        #3. pid文件存在，进程存在 
        if  os.path.exists(pidfile_path) and  len(pid_list) > 0:
            if pid_in_pidfile not in pid_list:
                logging.info("master pid is not found, restart it now !")
                os.remove(pidfile_path)
                self._stop_proc()
                time.sleep(self.wait_time)
                self._start_proc()
                sys.exit(0)

        #4. pid文件存在，进程不存在 
        if  os.path.exists(pidfile_path) and  len(pid_list) == 0:
            logging.info("%s process do not exists, start it now! "% self.app_name)
            os.remove(pidfile_path)
            self._start_proc()
            sys.exit(0)


    #No.2 不支持pid文件方式
    def _judge_status_section_2(self):

        pid_list = self._is_pid()
        self._is_pid_exist(pid_list)

        result = self._is_pid_exist_status(pid_list)
        if result:
            print "process exists."

        self._judge_status_section_3()
        self._judge_status_section_4()
        # 1.进程不存在
        if len(pid_list) == 0:
            logging.info("%s process is not running, start it now !" % self.app_name)
            self._start_proc()

        sys.exit(0)
            
    def _judge_status_section_3(self):
        #检查端口
        if self.app_port:
            if not self._is_port_exist():
                logging.info("%s process port is unnormal, restart it now !" % self.app_name)
                self._stop_proc()
                time.sleep(self.wait_time)
                self._start_proc()
                sys.exit()

    def _judge_status_section_4(self):
        #2. 进程数异常
        pid_list = self._is_pid()
        if self.proc_num:
            if  len(pid_list) != self.proc_num:
                logging.info("%s process num is unnormal, restart it now !" % self.app_name)
                self._stop_proc()
                time.sleep(self.wait_time)
                self._start_proc()
                sys.exit()

    def _judge_status_section_5(self):
        #杀死进程
        job=CronTab(self.CRON_CMD,self.app_name)
        job._disenable()
        self._stop_proc()
        #for cmdb
        result = self._is_pid_exist_status(self._is_pid())
        if result:
            print "stoping failed."
        else:
            print "stoping successfull."
        sys.exit()
        

class CronTab(object):
    def __init__(self,job,proc):
        self.CRONCMD = "/usr/bin/crontab "
        self.tmp_file = ".tmp_cron"
        self.job = job
        self.app_name = proc
        self.lines = []
 
    def _read(self):
        os.system(self.CRONCMD + '-l ' + '> ' + self.tmp_file)
        self.lines = []
        with open(self.tmp_file,'r') as file:
            for line in file.readlines():
                self.lines.append(' '.join(line.split())) 
        os.remove(self.tmp_file)

    def _write(self):
        with open(self.tmp_file,'w') as file:
            for line in self.lines:
                file.write(line + '\n')
        os.system(self.CRONCMD + ' ' + self.tmp_file )
        os.remove(self.tmp_file)

    def _exist(self):
        self._read()
        for job in self.lines:
            job_list = job.split()
            if job_list.count("-m") == 1 :
                if job_list[job_list.index("-m")+1] == self.app_name:
                    return True
                else:
                    continue 
            else:
                for item in job_list:
                    if item.startswith("-m") and item.split('-m')[1]==self.app_name:
                        return True
                    else:
                        continue
        return False

    def _add(self):
        if self._exist():
            self.__remove()
        self.lines.append(' '.join(self.job.split()))
        self._write()

    def _remove(self):
        if self._exist():
            self.__remove()
            self._write()

    def __remove(self):
        tmp_lines = copy.deepcopy(self.lines)
        for job in self.lines:
            job_list = job.split()
            if job_list.count("-m") == 1 and job_list[job_list.index("-m")+1] == self.app_name:
                tmp_lines.remove(job)
            else:
                for item in job_list:
                    if item.startswith("-m") and item.split('-m')[1]==self.app_name:
                        tmp_lines.remove(job)
        self.lines = copy.deepcopy(tmp_lines)

    def _disenable(self):
        if self._exist():
            tmp_lines = copy.deepcopy(self.lines)
            for job in self.lines:
                job_list = job.split()
                if job_list.count("-m") == 1 and not job_list[0].startswith("#"):
                    if job_list[job_list.index("-m")+1] == self.app_name:
                        tmp_lines.remove(job)
                        job = '#' + job
                        tmp_lines.append(job)
                else:
                    for item in job_list:
                        if item.startswith("-m") and not job_list[0].startswith("#"):
                            if item.split('-m')[1]==self.app_name:
                                tmp_lines.remove(job)
                                job = '#' + job
                                tmp_lines.append(job)
            self.lines = copy.deepcopy(tmp_lines)
            self._write()

    def _enable(self):
        new_job = '#' + self.job
        if self._exist():
            tmp_lines = copy.deepcopy(self.lines)
            for job in self.lines:
                job_list = job.split()
                if job_list.count("-m") == 1 and job_list[0].startswith("#"):
                    if job_list[job_list.index("-m")+1] == self.app_name:
                        tmp_lines.remove(job)
                        job = ''.join(job.split('#')[1])
                        tmp_lines.append(job)
                else:
                    for item in job_list:
                        if item.startswith("-m") and job_list[0].startswith("#"):
                            if item.split('-m')[1]==self.app_name:
                                tmp_lines.remove(job)
                                job = ''.join(job.split('#')[1])
                                tmp_lines.append(job)
            self.lines = copy.deepcopy(tmp_lines)
            self._write()
            
        
def prase_arg():
    '''参数解析'''
    Args = {"app_name":'',"app_port":None,
            "work_dir":'',"start_scripts":None,
            'action':None,'pid_file':None,
            'proc_num':None,'check_times':None,
            'wait_time':None,'cron_task':None}

    parser = OptionParser(usage="\n%prog [options] ",version="%prog 1.1")
    parser.add_option("-m","--app_name",
                      action="store",dest="app_name",
                      help='''app process name(Default and Necessary):
                              example:                               
                              ./watchdog -m process_name -p work_space                     
                              eg. ./watchdog -m nginx -p /mnt/hswx/nginx
                              ''')

    parser.add_option("-P","--app_port",
                      action="store",dest="app_port",
                      type="int",
                      help='''app listening port
                              example:                       
                              ./watchdog -m process_name -P port     
                              eg. ./watchdog -m nginx -P 80
                              ''')

    parser.add_option("-p","--work_dir",
                      action="store",dest="work_dir",
                      help='''app work space                         
                              example:                                      
                              eg. ./watchdog -m nginx -p /mnt/hswx/nginx
                              ''')

    parser.add_option("-s","--start_scripts",
                      action="store",dest="start_scripts",
                      help='''app start script path
                              example:                                   
                              ./watchdog -m process_name -p work_space -s scripts_path                    
                              eg. ./watchdog -m nginx -p /mnt/hswx/nginx -s /mnt/hswx/nginx/start_nginx.sh
                              ''')

    parser.add_option("-a","--action",
                      action="store",dest="action",
                      help='''action for app script start or stop
                              example:                                   
                              ./watchdog -m process_name -p work_space -s scripts_path -a start                   
                              eg. ./watchdog -m dgw -p /mnt/hswx/DGW -s /mnt/hswx/DGW/control -a start
                              ps. Using 'stop' will be remove cront task.
                              ./watchdog -m process_name -a stop
                              eg. ./watchdog -m dgw -a stop
                              ''')

    parser.add_option("-i","--pid_file",
                      action="store",dest="pid_file",
                      help='''app pid file path              
                              example:                                                                              
                              ./watchdog -m process_name -p work_space -i pid_file_path                                        
                              eg. ./watchdog -m nginx -p /mnt/hswx/nginx -i /mnt/hswx/nginx/logs/nginx.pid
                              ''')

    parser.add_option("-n","--proc_num",
                      action="store",dest="proc_num",type='int',
                      help='''app proc numbers                        
                              example:                                                                               
                              ./watchdog -m process_name -p work_space -n int_nummber                       
                              eg. ./watchdog -m nginx -p /mnt/hswx/nginx -n 5
                              ''')         

    parser.add_option("-c","--check_times",
                      action="store",dest="check_times",type='int',
                      help='''check times                               
                              example:                                                      
                              ./watchdog -m process_name -p work_space -c int_nummber                               
                              eg. ./watchdog -m nginx -p /mnt/hswx/nginx -c 4
                              ''')

    parser.add_option("-t","--wait_time",
                      action="store",dest="wait_time",type='float',
                      help='''wait time                                                 
                              example:                                                            
                              ./watchdog -m process_name -p work_space -t float_wait_time                             
                              eg. ./watchdog -m nginx -p /mnt/hswx/nginx -t 5
                              ''')

    parser.add_option("-T","--cron_task",
                      action="store",dest="cron_task",type='string',
                      help='''cron task format: split by ':'
                              example:                                    
                              ./watchdog -m process_name -p work_space -T cron_task
                              eg. ./watchdog -m nginx -p /mnt/hswx/nginx -T '*/2:*:*:*:*' 
                              ''')


    group = OptionGroup(parser,'Warning',
                        "Default and Necessary option:   '-m'   "                                                                                             
                        "                         ./watchdog -m process_name -p work_space  "                  
                        "                              eg. ./watchdog -m nginx -p /mnt/hswx/nginx"
                        "                           if you want to start and monitor ,plz must use '-p' "
                        "which give your start scripts path co-operating with the '-s','-a' and so on.")
    group.add_option('-w',action='store_true',help='Warning option')
    parser.add_option_group(group)

    (options,args) = parser.parse_args()

    if options.app_name:
        Args["app_name"] = options.app_name
    if options.app_port:
        Args["app_port"] = options.app_port
    if options.work_dir:
        Args["work_dir"] = options.work_dir
    if options.start_scripts:
        Args["start_scripts"] = options.start_scripts
    if options.pid_file:
        Args["pid_file"] = options.pid_file
    if options.proc_num:
        Args["proc_num"] = options.proc_num
    if options.check_times:
        Args["check_times"] = options.check_times
    if options.wait_time:
        Args["wait_time"] = options.wait_time 
    if options.action:
        Args["action"] = options.action
    if options.cron_task:
        Args["cron_task"] = options.cron_task
    return Args 

if __name__ == '__main__':
    Args = prase_arg()
    if len(sys.argv) < 2:
        print "\nArguments unavailable ,using '-h|--help' to get help.\n"
    instance = WatchDog(Args["app_name"],Args["work_dir"],
                        Args["app_port"],Args["start_scripts"],Args["action"],
                        Args["pid_file"],Args["proc_num"],
                        Args["check_times"],Args["wait_time"],Args["cron_task"])
    pid_file,_ = instance._is_pid_file_exist()
    if Args["action"] == 'stop':
        instance._judge_status_section_5()
    if not Args["pid_file"]:
        if pid_file:
            instance._judge_status_section_1()
        else:
            instance._judge_status_section_2()
    else:
        instance._judge_status_section_1()

# easy-to-watch
for watch process

Usage: 
watchdog [options] 

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -m APP_NAME, --app_name=APP_NAME
                        app process name(Default and Necessary):
                        example:
                        ./watchdog -m process_name -p work_space
                        eg. ./watchdog -m nginx -p /mnt/hswx/nginx
  -P APP_PORT, --app_port=APP_PORT
                        app listening port
                        example:
                        ./watchdog -m process_name -P port
                        eg. ./watchdog -m nginx -P 80
  -p WORK_DIR, --work_dir=WORK_DIR
                        app work space
                        example:
                        eg. ./watchdog -m nginx -p /mnt/hswx/nginx
  -s START_SCRIPTS, --start_scripts=START_SCRIPTS
                        app start script path
                        example:
                        ./watchdog -m process_name -p work_space -s
                        scripts_path
                        eg. ./watchdog -m nginx -p /mnt/hswx/nginx -s
                        /mnt/hswx/nginx/start_nginx.sh
  -a ACTION, --action=ACTION
                        action for app script start or stop
                        example:
                        ./watchdog -m process_name -p work_space -s
                        scripts_path -a start
                        eg. ./watchdog -m dgw -p /mnt/hswx/DGW -s
                        /mnt/hswx/DGW/control -a start
                        ps. Using 'stop' will be remove cront task.
                        ./watchdog -m process_name -a stop
                        eg. ./watchdog -m dgw -a stop
  -i PID_FILE, --pid_file=PID_FILE
                        app pid file path
                        example:
                        ./watchdog -m process_name -p work_space -i
                        pid_file_path
                        eg. ./watchdog -m nginx -p /mnt/hswx/nginx -i
                        /mnt/hswx/nginx/logs/nginx.pid
  -n PROC_NUM, --proc_num=PROC_NUM
                        app proc numbers
                        example:
                        ./watchdog -m process_name -p work_space -n
                        int_nummber
                        eg. ./watchdog -m nginx -p /mnt/hswx/nginx -n 5
  -c CHECK_TIMES, --check_times=CHECK_TIMES
                        check times
                        example:
                        ./watchdog -m process_name -p work_space -c
                        int_nummber
                        eg. ./watchdog -m nginx -p /mnt/hswx/nginx -c 4
  -t WAIT_TIME, --wait_time=WAIT_TIME
                        wait time
                        example:
                        ./watchdog -m process_name -p work_space -t
                        float_wait_time
                        eg. ./watchdog -m nginx -p /mnt/hswx/nginx -t 5
  -T CRON_TASK, --cron_task=CRON_TASK
                        cron task format: split by ':'
                        example:
                        ./watchdog -m process_name -p work_space -T cron_task
                        eg. ./watchdog -m nginx -p /mnt/hswx/nginx -T
                        '*/2:*:*:*:*'

  Warning:
    Default and Necessary option:   '-m'
    ./watchdog -m process_name -p work_space
    eg. ./watchdog -m nginx -p /mnt/hswx/nginx
    if you want to start and monitor ,plz must use '-p' which give your
    start scripts path co-operating with the '-s','-a' and so on.

    -w                  Warning option

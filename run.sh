#!/bin/bash

while true
do
   run_py=`ps -ef|grep "MyTimingReptile.py"|grep -v grep|wc -l `
   if [ ${run_py} -eq 0 ];then
       nohup python -u MyTimingReptile.py >> runlog.log 2>&1 &
       echo "MyTimingReptile.py,started"
   fi
   sleep 60
done
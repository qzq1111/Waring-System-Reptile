#!/bin/bash

while true
do
   run_py=`ps -ef|grep "MyReptile.py"|grep -v grep|wc -l `
   if [ ${run_py} -eq 0 ];then
       nohup python -u MyReptile.py>>runxlog.log 2>&1 &
       echo "MyReptile.py,started"
   fi
   sleep 60
done
#!/bin/bash
runpy_id=`ps -ef|grep "MyTimingReptile.py"|grep -v grep|awk '{print $2}'`
runsh_id=`ps -ef|grep "run.sh"|grep -v grep|awk '{print $2}'`
kill -9 ${runsh_id}
kill -9 ${runpy_id}
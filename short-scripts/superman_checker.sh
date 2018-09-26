#!/bin/bash
while true
do
  RUNNING=$(ssh superman "condor_q netfor | grep 'netfor.*R' | wc -l")
  IDLE=$(ssh superman "condor_q netfor | grep 'netfor.*I' | wc -l")
  OTHER=$(ssh superman "condor_q netfor | grep 'netfor.*' | sed 's/\s\s*/ /g' | cut -d' ' -f6 | grep [^RI] | wc -l")

  ALL=$(($RUNNING + $IDLE + $OTHER))
  if [ $ALL -eq 0 ]; then
    notifypbl -t 'Superman job' -b 'There is no running job on superman'
    exit 0
  fi

  notifypbl -t 'Superman state' -b "I: $IDLE; R: $RUNNING; O: $OTHER"

  sleep 300
done

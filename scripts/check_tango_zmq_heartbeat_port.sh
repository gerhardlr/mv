#!/bin/bash
: "${SERVER_IP:=127.0.0.1}"
: "${TANGO_ZMQ_HEARTBEAT_PORT:=30004}"
TIMEOUT=5
    
(echo ^]; echo quit) | timeout --signal=9 5 telnet $SERVER_IP $TANGO_ZMQ_HEARTBEAT_PORT > /dev/null 2>&1    
TELNET_EXIT_CODE=$?
    
if [ $TELNET_EXIT_CODE -ne 0 ]; then
    nc -w $TIMEOUT -z $SERVER_IP $TANGO_ZMQ_HEARTBEAT_PORT > /dev/null 2>&1
    NC_EXIT_CODE=$?
fi

if [ $TELNET_EXIT_CODE -eq 0 ] || [ $NC_EXIT_CODE -eq 0 ]; then
    echo "success"
else
    echo "fail"
fi
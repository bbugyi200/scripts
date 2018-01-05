#!/bin/bash

FILE=$(basename -s .sh $0).pid
echo $$ > $FILE

until ((COUNT >= 10))
do
    sleep 10
    ((COUNT ++))
done
exit 0

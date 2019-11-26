#!/bin/bash

#!/bin/bash
paramf=
dataf=

usage()
{
    echo "usage: hnn.sh [-paramf file] [-dataf file]  [-help]"
}


while [ "$1" != "" ]; do
    case $1 in
        -paramf | --paramf )    shift
                                paramf=$1
                                ;;
        -dataf | --dataf )      shift
                                dataf=$1
                                ;;
        -h | --help )           usage
                                exit
                                ;;
        * )                     usage
                                exit 1
    esac
    shift
done

if [ -f "$paramf" ] && [ -f "$dataf" ]
then python3 hnn.py -paramf $paramf -dataf $dataf
elif [ -f "$paramf" ]
then python3 hnn.py -paramf $paramf
elif [ -f "$dataf" ]
then python3 hnn.py -dataf $dataf
else python3 hnn.py
fi

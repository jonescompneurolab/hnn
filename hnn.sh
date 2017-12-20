#!/bin/bash
export CPU=$(uname -m)
export PATH=$PATH:/usr/lib64/openmpi/bin:/usr/local/nrn/$CPU/bin

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
then python3 hnn.py hnn.cfg -paramf $paramf -dataf $dataf
elif [ -f "$paramf" ]
then python3 hnn.py hnn.cfg -paramf $paramf
elif [ -f "$dataf" ]
then python3 hnn.py hnn.cfg -dataf $dataf
else python3 hnn.py hnn.cfg
fi


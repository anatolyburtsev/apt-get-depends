#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# update package with almost all dependence
# 19/10/2014 Anatoly Burtsev onotole@yandex-team.ru

import argparse, sys
import subprocess as sb

def parse():
    AP = argparse.ArgumentParser( description = "update dep package with all dependences" )
    #AP.add_argument( '--depth', '-d', type=int, default=2, dest='depth', help = "depth of update. fox ex: depth=1 just update packag e and its dependences" )
    AP.add_argument( '--no-update', '-n', action='store_false', dest='noupdate', help = "Do not perform apt-get update" )
    AP.add_argument( 'package_name', default=None)
    return AP.parse_args()

def uniq(seq):
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if not (x in seen or seen_add(x))]

def install_packages(packages_names):
    #install a lot of packages
    #may be "package (>=1.0-23)"
    #TODO check this versions condition
    if packages_names == []:
        return True
    for i in range(len(packages_names)):
        packages_names[i] = packages_names[i].split(' ')[0]
    install="apt-get install -y --force-yes".split()
    install += packages_names
    print(install)
    command_install = sb.Popen( install, stdout = sb.PIPE, stderr = sb.PIPE )
    out, err = command_install.communicate()
    print(out.decode())
    if err:
        print(err.decode())
        raise OSError

def get_dependence(package_name):
    # cut version condition
    # for dependence like nginx-core (>= 1.6.2-4) | nginx-full (>= 1.6.2-4) | ... return ... nothing
    # fix problem with nginx VS nginx-core
    package_name = package_name.split(' ')[0]
    full_list = "apt-cache show " + package_name
    full_list = full_list.split()
    head = "head -17".split()
    dep_and_pred = "grep Depends".split()
    dependence = "grep -v Pre-Depends".split()
    predependence = "grep Pre-Depends".split()
    package_dep_list = []
    package_predep_list = []

    #get dependence list
    command_full_list = sb.Popen( full_list, stdout = sb.PIPE )
    command_head = sb.Popen( head, stdin = command_full_list.stdout, stdout = sb.PIPE )
    command_dep_and_pred = sb.Popen( dep_and_pred, stdin = command_head.stdout, stdout = sb.PIPE )
    command_dependence = sb.Popen ( dependence, stdin = command_dep_and_pred.stdout, stdout = sb.PIPE )

    out, err = command_dependence.communicate()
    #cut Depends:
    if out != b"":
        try:
            package_dep_list = out.decode().split(": ")[1]
            #split
            package_dep_list = package_dep_list.split(', ')
            package_dep_list[-1] = package_dep_list[-1].replace("\n","")
            #remove "|"
            for i in range(len(package_dep_list)-1,-1,-1):
                if "|" in package_dep_list[i] or 'nginx' in package_dep_list[i]:
                    del(package_dep_list[i])
        except IndexError:
            print("Error in build dependence list")
            pass

    #get predependence list
    command_full_list = sb.Popen( full_list, stdout = sb.PIPE )
    command_head = sb.Popen( head, stdin = command_full_list.stdout, stdout = sb.PIPE )
    command_dep_and_pred = sb.Popen( dep_and_pred, stdin = command_head.stdout, stdout = sb.PIPE )
    command_predependence = sb.Popen ( predependence, stdin = command_dep_and_pred.stdout, stdout = sb.PIPE )

    out, err = command_predependence.communicate()

    #cut Pre-Depends:
    if out != b"":
        try:
            package_predep_list = out.decode().split(": ")[1]
            #split
            package_predep_list = package_predep_list.split(', ')
            package_predep_list[-1] = package_predep_list[-1].replace("\n","")
            #remove "|"
            for i in range(len(package_predep_list)-1,-1,-1):
                if "|" in package_predep_list[i] or 'nginx' in package_predep_list[i]:
                    del(package_predep_list[i])
        except IndexError:
            print("Error in build pre-dependence list")
            pass

    return [package_dep_list,package_predep_list]

def update():
    #apt-get update
    update="apt-get update".split()
    command_update = sb.Popen( update, stdout = sb.PIPE, stderr = sb.PIPE )
    out,err = command_update.communicate()
    if err:
        print(err)
        raise OSError

#first stupid revision
def get_list_of_lists_to_install(package_name):
    [dep_list, predep_list] = get_dependence(package_name)
    prepredep_list=[]
    deppredep_list=[]
    predepdep_list=[]
    depdepdep_list=[]
    for package in predep_list:
        [prepredep_list_cur, deppredep_list_cur] = get_dependence(package)
        prepredep_list += prepredep_list_cur
        deppredep_list += deppredep_list_cur
    for package in dep_list:
        [predepdep_list_cur, depdepdep_list_cur] = get_dependence(package)
        predepdep_list += predepdep_list_cur
        depdepdep_list += depdepdep_list_cur
    prepredep_list = uniq(prepredep_list)
    deppredep_list = uniq(deppredep_list)
    predepdep_list = uniq(predepdep_list)
    depdepdep_list = uniq(depdepdep_list)

    return [prepredep_list, deppredep_list, predepdep_list, depdepdep_list]

def install_all(package_name,noupdate):
    #list of lists sorted in logical order (pre pre dependence, dependence of predependence and so on    
    if noupdate: update()
    list_of_packages = get_list_of_lists_to_install(package_name)
    for current_list in list_of_packages:
        install_packages(current_list) 

if __name__ == '__main__':
    ARGS = parse()
    install_all(ARGS.package_name, ARGS.noupdate)

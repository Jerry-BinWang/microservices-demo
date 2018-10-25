#!/usr/bin/env python3
import os
import sys
import subprocess


FRONTEND_STACK_PREFIX = "sockshop_frontend_"
BACKEND_STACK = "sockshop_backend"


def print_usage():
    print("This script takes exactly one argument.")
    print("Usage: {} HOSTNAME".format(sys.argv[0]))
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print_usage()
    hostname = sys.argv[1]
    
    print("Generating compose file for host {}".format(hostname))
    temp_config_file = "{}.yml".format(hostname)
    with open(temp_config_file, "w") as fout:
        subprocess.run(["sed", "s/{{hostname}}/"+hostname+"/g", "frontend.yml"], check=True, stdout=fout)

    print("Deploying frontend stack")
    stack_name = FRONTEND_STACK_PREFIX + hostname
    subprocess.run(["docker", "stack", "deploy", "-c", temp_config_file, stack_name], check=True)

    print("Adding backend services to network")
    process = subprocess.run(["docker", "stack", "services", BACKEND_STACK], check=True, stdout=subprocess.PIPE)
    process = subprocess.run(["tail", "-n", "+2"], input=process.stdout, check=True, stdout=subprocess.PIPE)
    process = subprocess.run(["awk", "{print $2}"], input=process.stdout, check=True, stdout=subprocess.PIPE)
    for line in process.stdout.decode().split("\n"):
        service = line.strip()
        if service:
            alias = service.replace(BACKEND_STACK+"_", "")
            subprocess.run(
                ["docker", "service", "update", "--network-add",
                 "name={},alias={}".format(stack_name + "_default", alias), service], check=True)

    print("Cleaning up")
    os.remove(temp_config_file)

#!/usr/bin/python3
# -----------------------------------------------------------------------------
#    Copyright 2021 Stephen Stebbing. telecnatron.com
#
#    Licensed under the Telecnatron License, Version 1.0 (the “License”);
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        https://telecnatron.com/software/licenses/
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an “AS IS” BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
# -----------------------------------------------------------------------------
import tinytuya

"""
Arlec Grid Connect (or similar) wifi-controlled powerboard. 
see: https://www.bunnings.com.au/arlec-grid-connect-smart-4-outlet-powerboard_p0161023

Requires tinytuya module. See: https://github.com/jasonacox/tinytuya
"""

# Exception class which is raised when an error is detected
class APBException(Exception):
    pass

class APB:
    
    def __init__(self, id, hostname, key):
        # Needs to be set on a per device basis. Here we only have one device
        # device_id, hostname/ip, local_key
        self._device= tinytuya.OutletDevice(id, hostname, key)
        self._device.set_version(3.3)
        # socket parameters
        self._device.set_socketRetryLimit(4)
        self._device.set_socketTimeout(4)
        

    @property
    def state(self):
        status=self._device.status()
        if 'Error' in status:
            raise APBException(f"{status['Err']}: {status['Error']}")
        if status['dps']['1']:
            return 1
        else:
            return 0

    @state.setter
    def state(self, value):
        if value==0:
            self.off()
        else:
            self.on()

    def on(self):
        r=self._device.set_status(True)
        if 'Error' in r:
            raise APBException(f"{r['Err']}: {r['Error']}")


    def off(self):
        r=self._device.set_status(False)
        if 'Error' in r:
            raise APBException(f"{r['Err']}: {r['Error']}")

        
    def toggle(self):
        s=not self.state
        self.state=s
        return int(s)
        
# -----------------------------------------------------------------------------
import argparse
import json
import socket
import sys


# silly little function to print to sdterr
def print_stderr(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# display passed error message to stderr and exit with passed status code.
def exit_nicely(status=0, error_msg=''):
    if error_msg != '':
        print_stderr(f'ERROR: {error_msg}')
    exit(status)


if __name__ == "__main__":


    # default path to device table file.
    # The json should be dictionary of hostname->[id, key]
    # note that hostname should be fqdn or IP number.
    # eg:
    #{
    #  "apb0.home.ss": ["7553155390339f8fa571", "f201b3618e4f3f10"],
    #  "slap.home.ss": ["744315537003af8f9571", "f94j23118e2f5810"]
    #}
    device_conf_path = "/etc/apb.json"

    
    # handle command line
    parser=argparse.ArgumentParser()
    parser.add_argument("host",help="hostname or IP number of the device")    
    parser.add_argument("cmd", choices=['0','on','1','off','t','toggle','s','state'], default='s')
    parser.add_argument("-k","--key",help="device key")
    parser.add_argument("-d","--id",help="device id")
    parser.add_argument("-f","--config",help="path to json device-configuration file, default is {device_conf_path}", default=f'{device_conf_path}')    
    args=parser.parse_args()

    # note that we convert specified hostname to fqdn
    host = args.host
    key = args.key
    id = args.id

  
    if key == None or id == None:
        # one or more of key and id where not specified on command line.
        # Read json config file
        try:
            with open(args.config) as jsonf:
                devices=json.load(jsonf)
        except json.decoder.JSONDecodeError as e:
            # syntax error in json file
            exit_nicely(1, f"In config file {args.config}: {e}");
        except FileNotFoundError as e:
            exit_nicely(2, f"{e}");
            
    
    # look up the host details for this device in the device dictionary
    try:
        # note: we use fqdn as key for device lookup
        fqdn=socket.getfqdn(host)
        if id == None:
            id  = devices[fqdn][0]
        if key == None:
            key = devices[fqdn][1]
    except KeyError as ke:
        exit_nicely(2, error_msg=f"no entry in device table for host/ip: {host}\nPlease specify --key and --id for this host.")

    # connect to host
    try:
        apb = APB(id,host,key)

        # do what we've been commanded to do
        cmd=args.cmd
        #XXX steves: bloody python, doesn't have switch statement, does have match statement, but not until 3.10,
        #XXX we're using 3.8.10, bloody python
        if cmd == '0' or cmd == 'off':
            apb.off()
        elif cmd == '1' or cmd == 'on':
            apb.on()
        elif cmd == 't' or cmd == 'toggle':
            apb.toggle()
        elif cmd == 's' or cmd == 'state':
            print(f'{apb.state}')

    except APBException as ae:
        exit_nicely(3, error_msg=f"{ae}")

        
exit_nicely()

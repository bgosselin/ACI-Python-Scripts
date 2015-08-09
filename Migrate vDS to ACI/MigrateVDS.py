#!/usr/bin/env python
# VMware vSphere Python SDK
# Cisco Systems ACI Cobra SDK
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Python program to re-create Existing vCenter VDS Portgroups in ACI as EPGs.
It also establishes a connection between ACI and vCenter,
and creates a new ACI controlled VDS.

Users can apply this script to port legacy virtual networks into ACI
to begin applying policy based networks to existing applicaiton.
"""

# ACI Cobra SDK packages that must be imported for this script to work
import cobra.mit.access
import cobra.mit.naming
import cobra.mit.request
import cobra.mit.session
import cobra.model.infra
import cobra.model.vmm
import cobra.model.fvns
import cobra.model.draw
import cobra.model.fv
from cobra.internal.codec.xmlcodec import toXMLStr

# Other packages that must be imported including VMware vSphere Python SDK
import atexit
import argparse
import getpass
from pyVim import connect
from pyVmomi import vmodl


# Work around to omit certificate verification
# WARNING! not recommended
import requests
requests.packages.urllib3.disable_warnings()
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

#....
# End of work around



'''
get_args
retrive command line arguments
If the passwords or contract type are not inlcuded in the arguments, prompt the user
'''
def get_args():
    """Get command line args from the user.
    """
    parser = argparse.ArgumentParser(
        description='Standard Arguments for talking to vCenter')

    # because -h is reserved for 'help' we use -s for service
    parser.add_argument('-vs', '--vSphereHost',
                        required=True,
                        action='store',
                        help='vSphere service to connect to')

    # because we want -p for password, we use -o for port
    parser.add_argument('-vo', '--vSpherePort',
                        type=int,
                        default=443,
                        action='store',
                        help='Port to connect on for vSphere')

    parser.add_argument('-vu', '--vSphereUser',
                        required=True,
                        action='store',
                        help='User name to use when connecting to vSphere host')

    parser.add_argument('-vp', '--vSpherePassword',
                        required=False,
                        action='store',
                        help='Password to use when connecting to host')

     # because -h is reserved for 'help' we use -s for service
    parser.add_argument('-as', '--apicHost',
                        required=True,
                        action='store',
                        help='APIC to connect to')

    # because we want -p for password, we use -o for port
    parser.add_argument('-ao', '--apicPort',
                        default=443,
                        action='store',
                        help='Port to connect on')

    parser.add_argument('-au', '--apicUser',
                        required=True,
                        action='store',
                        help='User name to use when connecting to host')

    parser.add_argument('-ap', '--apicPassword',
                        required=False,
                        action='store',
                        help='Password to use when connecting to host')

    parser.add_argument('-c', '--contract',
                        required=False,
                        action='store',
                        help='specify whitelist or blacklist connections for new EPGs in ACI based on VDS Portgroups')

    args = parser.parse_args()

    if not args.vSpherePassword:
        args.password = getpass.getpass(
            prompt='Enter vSphere password for host %s and user %s: ' %
                   (args.vSphereHost, args.vSphereUser))

    if not args.apicPassword:
        args.password = getpass.getpass(
            prompt='Enter APIC password for host %s and user %s: ' %
                   (args.apicHost, args.apicUser))

    if not args.contract:
        args.contract = raw_input('Default contract for Migrated Portgroups in ACI (whitelist/blacklist): ')
    return args


'''
getPortGroups

'''
def getPortGroups(args):
    """
    Simple command-line program for listing the Portgroups on a system.
    """
    portGroups=[]
    
    print 'Existing Portgroups:'
  
    # Connect to vCenter
    try:
        service_instance = connect.SmartConnect(host=args.vSphereHost,
                                                user=args.vSphereUser,
                                                pwd=args.vSpherePassword,
                                                port=int(args.vSpherePort))

        atexit.register(connect.Disconnect, service_instance)

        # Get dataModel from vCetner
        content = service_instance.RetrieveContent()
        children = content.rootFolder.childEntity
        for child in children:
            if hasattr(child, 'network'):
                datacenter = child
            else:
                # some other non-datacenter type object
                continue

            # For each vDS add it to the list and print it on the screen
            networks = datacenter.network
            for network in networks:
                if network._wsdlName == 'DistributedVirtualPortgroup':
                    portGroups.append(network.name)
                    print network.name

    except vmodl.MethodFault as error:
        print "Caught vmodl fault : " + error.msg
        return -1

    print ''

    # Return a list of the Portgroups in vCenter if the user wants to built them in ACI
    migratePortgroups = raw_input("Build these Portgroups in ACI? (Yes/No): ")
    if (migratePortgroups == 'Yes'):
        return portGroups
    else:
        return -1

'''
buildAciDvs
Creates a VLAN pool and a connection between ACI and vCenter to deploy an ACI controlled VDS
'''
def buildAciDvs(args, startingVlan, numVlans):

    endingVlan = startingVlan + numVlans + 10

    print 'Syncing ACI with vCenter...'

    # log into an APIC and create a directory object
    ls = cobra.mit.session.LoginSession('https://'+args.apicHost, args.apicUser, args.apicPassword)
    md = cobra.mit.access.MoDirectory(ls)
    md.login()

    # the top level object on which operations will be made
    # Confirm the dn below is for your top dn
    topDn = cobra.mit.naming.Dn.fromString('uni/infra/vlanns-[ACILab_VLAN_Pool]-dynamic')
    topParentDn = topDn.getParent()
    topMo = md.lookupByDn(topParentDn)

    # build the request using cobra syntax
    fvnsVlanInstP = cobra.model.fvns.VlanInstP(topMo, ownerKey=u'', name=u'ACILab_VLAN_Pool', descr=u'', ownerTag=u'', allocMode=u'dynamic')
    fvnsEncapBlk = cobra.model.fvns.EncapBlk(fvnsVlanInstP, to=u'vlan-'+str(endingVlan), from_=u'vlan-'+str(startingVlan), name=u'encap', descr=u'') #***********************make this dyanmic


    # commit the generated code to APIC
    # print ''
    # print toXMLStr(topMo)
    c = cobra.mit.request.ConfigRequest()
    c.addMo(topMo)
    md.commit(c)


    # the top level object on which operations will be made
    # Confirm the dn below is for your top dn
    topDn = cobra.mit.naming.Dn.fromString('uni/vmmp-VMware/dom-My-vCenter')
    topParentDn = topDn.getParent()
    topMo = md.lookupByDn(topParentDn)

    # build the request using cobra syntax
    vmmDomP = cobra.model.vmm.DomP(topMo, mcastAddr=u'0.0.0.0', ownerKey=u'', name=u'My-vCenter', mode=u'default', ownerTag=u'', enfPref=u'hw')
    vmmRsDefaultStpIfPol = cobra.model.vmm.RsDefaultStpIfPol(vmmDomP, tnStpIfPolName=u'default')
    vmmRsDefaultLldpIfPol = cobra.model.vmm.RsDefaultLldpIfPol(vmmDomP, tnLldpIfPolName=u'default')
    vmmCtrlrP = cobra.model.vmm.CtrlrP(vmmDomP, name=u'dCloudDC', inventoryTrigSt=u'untriggered', statsMode=u'disabled', mode=u'default', dvsVersion=u'5.5', hostOrIp=args.vSphereHost, port=args.vSpherePort, rootContName=u'dCloudDC')
    vmmRsAcc = cobra.model.vmm.RsAcc(vmmCtrlrP, tDn=u'uni/vmmp-VMware/dom-My-vCenter/usracc-defaultAccP')
    infraRsVlanNs = cobra.model.infra.RsVlanNs(vmmDomP, tDn=u'uni/infra/vlanns-[ACILab_VLAN_Pool]-dynamic')
    vmmRsDefaultCdpIfPol = cobra.model.vmm.RsDefaultCdpIfPol(vmmDomP, tnCdpIfPolName=u'default')
    vmmRsDefaultLacpLagPol = cobra.model.vmm.RsDefaultLacpLagPol(vmmDomP, tnLacpLagPolName=u'default')
    vmmRsDefaultL2InstPol = cobra.model.vmm.RsDefaultL2InstPol(vmmDomP, tnL2InstPolName=u'default')
    vmmUsrAccP = cobra.model.vmm.UsrAccP(vmmDomP, usr=args.vSphereUser, ownerKey=u'', name=u'defaultAccP', descr=u'', ownerTag=u'', pwd=args.vSpherePassword)


    # commit the generated code to APIC
    # print ''
    # print toXMLStr(topMo)
    c = cobra.mit.request.ConfigRequest()
    c.addMo(topMo)
    md.commit(c)
    print 'Sync complete'

'''
mapPortGroups
Create an EPG for each Portgroup retrieved from vCenter
Put all EPGs in the 'Legacy' tenant, under the 'PortGroupMigration' app profile
Binds the EPGs to the vCenter domain created in the buildAciDvs function
Apply the default contract if 'blacklist' was selected, otherwise do not inlcude any contracts
'''
def mapPortGroups(args, portGroups):

    print 'Mapping vCenter Portgroups to EPGs...'

    # log into an APIC and create a directory object
    ls = cobra.mit.session.LoginSession('https://'+args.apicHost, args.apicUser, args.apicPassword)
    md = cobra.mit.access.MoDirectory(ls)
    md.login()

    # the top level object on which operations will be made
    # Confirm the dn below is for your top dn
    topDn = cobra.mit.naming.Dn.fromString('uni/tn-Legacy')
    topParentDn = topDn.getParent()
    topMo = md.lookupByDn(topParentDn)

    # build the request using cobra syntax
    fvTenant = cobra.model.fv.Tenant(topMo, ownerKey=u'', name=u'Legacy', descr=u'', ownerTag=u'')
    fvAp = cobra.model.fv.Ap(fvTenant, ownerKey=u'', prio=u'unspecified', name=u'PortGroupMigration', descr=u'', ownerTag=u'')

    for portGroup in portGroups:

        fvAEPg = cobra.model.fv.AEPg(fvAp, prio=u'unspecified', matchT=u'AtleastOne', name=portGroup, descr=u'')
        if args.contract=='blacklist':
            fvRsCons = cobra.model.fv.RsCons(fvAEPg, tnVzBrCPName=u'default', prio=u'unspecified')
        fvRsDomAtt = cobra.model.fv.RsDomAtt(fvAEPg, instrImedcy=u'lazy', tDn=u'uni/vmmp-VMware/dom-My-vCenter', resImedcy=u'lazy')
        #fvRsBd = cobra.model.fv.RsBd(fvAEPg, tnFvBDName=u'')
        #fvRsCustQosPol = cobra.model.fv.RsCustQosPol(fvAEPg, tnQosCustomPolName=u'')
        #fvRsTenantMonPol = cobra.model.fv.RsTenantMonPol(fvTenant, tnMonEPGPolName=u'')


    # commit the generated code to APIC
    # print toXMLStr(topMo)
    c = cobra.mit.request.ConfigRequest()
    c.addMo(topMo)
    md.commit(c)

    print 'Mapping complete'
    print '**'
    print 'Migration complete!'
    print 'Go to Tenants> Legacy> Applicaiton Profiles> PortGroupMigration to view the new EPGs'

def main():
    print 'Recreate Legacy VDS Portgroups in ACI'
    print '**'


    #Get User inputs from command line arguments
    args = get_args()
    print '**'
    print '**'
    print '**'
   
    #Get Existing Portgroups from vSphere
    portGroups = getPortGroups(args)
   
    #If there are any Portgroups to be migrated to ACI then build a new ACI controller VDS and populate it with Portgroups mapped 1:1 with EPGs
    if portGroups!=-1:
        if len(portGroups)>0:
               buildAciDvs(args, 1000, len(portGroups))
               mapPortGroups(args, portGroups)
    print ''
    print '**'
    print 'end'

   

# Start program
if __name__ == "__main__":
    main()
# Blair Gosselin  <blair.gosselin@live.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

# ACI Cobra SDK Libraries
from cobra.mit.access import MoDirectory
from cobra.mit.session import LoginSession
from cobra.model.fv import Ctx
from cobra.model.fv import *
from cobra.mit.request import *

# APIC Login Credentials
apicUrl = 'https://URL-of-APIC'
loginSession = LoginSession(apicUrl, 'username', 'password')

# APIC Managed Object Directory - starting at the top
moDir = MoDirectory(loginSession)

# Program asks for the name of the tenant to be created
TenantName = raw_input("Tenant Name: ")

moDir.login()

# Create new Tenant 
uniMo = moDir.lookupByDn('uni')
fvTenantMo = Tenant(uniMo, TenantName)

# Create new Private network/VRF under the new Tenant
fvContextMo = Ctx(fvTenantMo, 'myVRF')

# Add the new Tenant and its VRF Configuration to the APIC and commit these changes
cfgRequest = ConfigRequest()
cfgRequest.addMo(fvTenantMo)
moDir.commit(cfgRequest)

moDir.logout()
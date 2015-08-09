from cobra.mit.access import MoDirectory
from cobra.mit.session import LoginSession
from cobra.model.fv import Ctx
from cobra.model.fv import *
from cobra.mit.request import *

apicUrl = 'https://{IP-of-APIC}'
loginSession = LoginSession(apicUrl, 'user name', 'password')
moDir = MoDirectory(loginSession)

TenantName = raw_input("Tenant Name: ")

moDir.login()

uniMo = moDir.lookupByDn('uni')
fvTenantMo = Tenant(uniMo, TenantName)

fvContextMo = Ctx(fvTenantMo, 'myVRF')

cfgRequest = ConfigRequest()
cfgRequest.addMo(fvTenantMo)
moDir.commit(cfgRequest)


moDir.logout()
Hello World App (Python)
========================

# Description

Python Script that builds an ACI Tenant and creates a new VRF instance within it.

# Installation

### Environment

* Python 2.7+
* APIC Version Tested: 1.0(3f)
* [Cisco APIC Python SDK] (http://software.cisco.com/download/release.html?i=!y&mdfid=285968390&softwareid=286278832&release=1.0%281k%29&os),
  download the .egg file and follow the link to install acicobra:
  https://developer.cisco.com/media/apicDcPythonAPI_v0.1/install.html#

* [VMware vSphere Python SDK]
(https://pypi.python.org/pypi/pyvmomi)

### Downloading 


* Option A:
  Install the scripts to your python library form using pip install
    
    pip install apicPython

* Option B:

 If you have git installed, clone the repository

    git clone https://github.com/datacenter/ACI.git
    cd ACI/configuration-python/generic_code/
    python setup.py install

* Option C:

  If you don't have git, [download a zip copy of the repository](https://github.com/datacenter/ACI/archive/master.zip) and extract.
  Then,

    cd ACI/configuration-python/generic_code/
    python setup.py install
    
# License

Copyright 2014-2015 Cisco Systems, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

# Reference: 
[APIC Management Information Model Reference](https://developer.cisco.com/site/apic-dc/documents/mim-ref/)


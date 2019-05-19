# AC-PKI Configuration Guide

## About
AC-PKI is a system developed for my master thesis in information security. It provides a mechanism for creating and 
managing a public-key infrastructure (PKI) for a Cisco ACI network. This file provides the information needed to install 
and run the system in a local environment. 

Please note that this implementation is ONLY intended as a proof-of-concept and should not be used as or used for any 
production system. The code and framework has not been tested to the extent needed for a production system, and may be
genuinely vulnerable and insecure. However, the code may be used as a source of inspiration for future work on the topic
of SDN and Cisco ACI security as well as future implementations of the AC-PKI system. Please refer to the license for
terms of use. 

Author: Sigurd Haaheim \
Created: March 8, 2019 \
Updated: April 25, 2019

## License
Code in this repository may only be used for educational and non-commercial purposes, unless explicit and written 
permission is granted by the author. Frameworks and tools included in the repository may be subject to their own
licenses and terms of use. 

## Requirements

* Python 2.7
* Your favourite git client
* pip
* venv (recommended)
* Linux operating system (recommended)

## Installation
1. Clone the Github repository to your system. \
    ``git clone https://github.com/sigurd120/acpki.git``
1. (Recommended) Setup your local virtual environment (venv) with Python 2.7 as the project interpreter. If you *do not*
    use venv, make sure that you have Python 2.7 installed system-wide and that you have access to it from your command
    line or terminal. In this case you will have to install packages globally.
1. Install everything in requirements.txt (preferrably while in your virtual environment). This includes all 
requirements for packages used as well as for the AC-PKI software itself. \
    ``pip install -r requirements.txt``

## Using the prototype
1. Install the system as described above.
1. Start the Program class with the command below \
    ``python3 <project directory>/acpki/endpoints/Program.py`` \
   This class will create instances of the CA, RA, PSA, Client and Server classes, and the Client will prompt you to
   to send a message. The message will be sent to the Server and sent in return. 
1. Follow the instructions on the Client to send data to the server. You will receive the responses from the Server in 
the client terminal. 
1. The tenant and application profile will be automatically created if they do not exist. This is useful when using the
Cisco APIC Sandbox, which deletes tenants daily. 
1. The client and server do not exist on the APIC, only virtually in AC-PKI. However, they do have the EPGs parameters
set to "epg-cli" and "epg-serv" respectively. For the client and server to be permitted to communicate, you must follow 
some simple steps to configure the Sandbox APIC. \
a) Go to https://sandboxapicdc.cisco.com/ and enter the username "admin" and password "ciscopsdt". You will have to
 accept the self-signed certificate to enter the login page. \
b) Go to the "Tenants" tab and double-click the "acpki_prototype" tenant. Under Tenant > Application Profile > 
prototype, right click "Application EPGs" and click "Create Application EPG". \
c) Enter the name "epg-serv" and choose the Bridge Domain "default". You do not have to fill out the other input fields
before clicking Finish. Do the same again, but name this EPG "epg-cli". \
d) Now you have to create a contract between the two endpoints (you only need one direction for the prototype). It does
not matter which contract is used, so we will just use one of the default contracts. \
e) Open the "epg-cli" in the left menu, and right click "Contracts". Choose "Add Consumed Contract" and choose the
"default" contract. Do the same for "epg-serv" but choose "Add Provided Contract" instead. That will ensure that the 
contract works between the two EPGs; and the client and server.\
f) Done! If you try running Program.py again, your input should be accepted and returned by the server - i.e. printed 
twice in the terminal. 
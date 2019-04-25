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

## Installation
1. Clone the Github repository to your system. \
    ``git clone https://github.com/sigurd120/acpki.git``
1. (Recommended) Setup your local virtual environment (venv) with Python 2.7 as the project interpreter. If you *do not*
    use venv, make sure that you have Python 2.7 installed system-wide and that you have access to it from your command
    line or terminal. 
1. Install [Microsoft Visual C++](https://www.microsoft.com/en-us/download/confirmation.aspx?id=44266) (Windows systems)
    or **???** for Linux systems. These are required for installing py-radix, a requirement for acitoolkit. 
1. Install everything in requirements.txt (preferrably while in your virtual environment). This includes all 
requirements for packages used as well as for the AC-PKI software itself. \
    ``pip install -r requirements.txt``

## Using the prototype
1. Install the system as described above.
1. Start the Server \
    ``python3 <project directory>/acpki/endpoints/Server.py``
1. Start the Client \
    ``python3 <project directory>/acpki/endpoints/Client.py``
1. Follow the instructions on the Client to send data to the server. You will receive the responses from the Server in 
the client terminal. 
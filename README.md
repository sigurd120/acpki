# AC-PKI Configuration Guide

## About
AC-PKI is a system developed for my master thesis in information security. It provides a mechanism for creating and 
managing a public-key infrastructure (PKI) for a Cisco ACI network. The system is intended as a prototype and proof of
concept for the theory presented in my thesis. This file provides the information needed to install and run the
system in a local environment. 

Author: Sigurd Haaheim \
Created: March 8, 2019 \
Updated: N/A

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
1. Install everything in requirements.txt (preferrably while in your virtual environment). This includes all 
requirements for packages used as well as for the AC-PKI software itself. \
    ``pip install -r requirements.txt``
1. 
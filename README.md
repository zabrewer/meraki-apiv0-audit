# Meraki Audit v0 API Requests (v0audit.py)
-----------------

![v0audit](https://github.com/zabrewer/meraki-apiv0-audit/blob/master/assets/single_org.png?raw=true)

## Description

CLI application that will export all Meraki Dashboard v0 API calls for one, multiple, or all Meraki Dashboard Organizations (for a given API key).

## Motivation

The v0 version of the Meraki API will be sunsetting in the near future. Meraki's customers are encouraged to migrate to v1 of the API. This tool will output API logs for v0 API calls including the associated admin, email, and user agent for v0 API calls.

Meraki Community Post
https://community.meraki.com/t5/Developers-APIs/Dashboard-API-v0-End-of-Support-Sunset-amp-Grace-Period/m-p/138696/highlight/true#M5473

Cisco DevNet Post
https://blogs.cisco.com/developer/merakidashboardapi02

Meraki Developer Hub
https://developer.cisco.com/meraki/whats-new/#!2022/2-2022


## Installation

Python Virtual Environment is the preferred install method but to install to your default python (3.6 or newer recommended):

**1. Clone this repository locally**
```
git clone https://github.com/zabrewer/meraki-apiv0-audit.git
```
**2. Install from setup.py**

```
pip install .
```

### Installing to a Python Virtual Environment

Note: For Mac OSX, replace "python" with "python3" and for both platforms, make sure the output of python -v (or python3 -v) is 3.6 or greater.

**1. Clone this repository locally**
```
git clone https://github.com/zabrewer/meraki-apiv0-audit.git
```
**2. Create the virtual environment**
```
python3 -m venv meraki-apiv0-audit
```

**3. Change to the meraki-apiv0-audit directory**
```
cd meraki-apiv0-audit
```

**4. Activate the virtual environment**

For Windows
```
Scripts\activate.bat
```

For Mac
```
source bin/activate
```

**5. Satisfy dependencies by installing external packages**
```
pip install .
```

**6. Launch meraki-apiv0-audit while in virtual environment**
```
v0audit.py
```

To deactivate the virtual environment:

For Windows
```
Scripts\deactivate.bat
```

For Mac
```
deactivate
```

## Example Use

Get all v0 API calls for the given orgs for the last 5 days:

```
v0audit 6bec4XXXXXXXXXXX 'DevNet Sandbox' 'My organization' Testlab --days 5
```

Get all v0 API calls for all orgs that the API key has access to for the last 31 days (max):

```
python v0audit.py 6bec4XXXXXXXXXXX all
```

- If the *--days* option is provided, the max is 31, minimum is 1.  The default (no --days option given) is 31
- You can provide one or more Meraki org names separated by a space. If there is a space with the org name itself, it must be wrapped in single ('org name') or double ("org name") quotes
- Providing the *all* orgs argument after the *<API-Key>* argument will return v0 API call audit for all organizations that the given API key has permission to access. 
- Meraki organizations without API enabled are ignored.

Hint: if you want to see all orgs that your API key has access to, simply pass in an org name that does not 

[all orgs](assets/all_orgs.png?raw=true)

## Credit

Thanks to [Nico Darrow aka wifiguru10](https://github.com/wifiguru10) for being a code hacking partner in crime and Justin Lenhart for helping with testing.

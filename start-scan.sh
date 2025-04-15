#!/bin/sh
echo "[*] Starting SpiderFoot scan for domain: $1"
if [ -z "$1" ]; then
  echo "email is required"
  exit 1
fi
 
# para tasks
/opt/venv/bin/python sf.py -m sfp_dnsresolve -s "$1" -o json -q


# run sublist3r
echo "[*] Running Sublist3r..."
/opt/venv/bin/python3 /opt/Sublist3r/sublist3r.py -d "$1" -o /tmp/subdomains.txt

# if [ -n "$1" ]; then
#   /opt/venv/bin/python subdomain_lookup.py "$1"
# fi

# #!/bin/sh
# # Check valid info
# if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
#   echo "Usage: $0 <ipaddress> <domainname> <email>"
#   exit 1
# fi
 
# # Assign parameters to variables for clarity
# ipaddress="$1"
# domainname="$2"
# email="$3"
 
# # Para tasks
# /opt/venv/bin/python sf.py -s "$ipaddress,$domainname,$email" -m "sfp_dnsresolve,sfp_emailsearch" -q -o json

echo "[*] Running ip-api"
#run ip_lookup.py
if [ -n "$1" ]; then
  /opt/venv/bin/python ip_lookup.py "$1"
fi

wait
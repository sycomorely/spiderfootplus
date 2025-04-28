#!/bin/sh
echo "[*] Starting SpiderFoot scan for domain: $1"
if [ -z "$1" ]; then
  echo "domain is required"
  exit 1
fi
 
# para tasks
/opt/venv/bin/python sf.py -u all -s "$1" -o json -q

# run sublist3r
echo "[*] Running Sublist3r..."
/opt/venv/bin/python3 /opt/Sublist3r/sublist3r.py -d "$1" -o sublist3r_output.txt

echo "[*] Looking up IP info for each subdomain..."
while IFS= read -r subdomain; do
  if [ -n "$subdomain" ]; then
    echo "[*] Processing: $subdomain"
    /opt/venv/bin/python ip_lookup.py "$subdomain"
  fi
done < sublist3r_output.txt



echo "[*] Running ip-api"
#run ip_lookup.py
if [ -n "$1" ]; then
  /opt/venv/bin/python ip_lookup.py "$1"
fi

wait
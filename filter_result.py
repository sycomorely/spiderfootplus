import json

# List of desired types
wanted_types = [
    "Account on External Site",
    "Hacked Account on External Site",
    "Hacked User Account on External Site",
    "Affiliate - Company Name",
    "Affiliate Description - Abstract",
    "Affiliate Description - Category",
    "Affiliate - Domain Name",
    "Affiliate - Domain Name Unregistered",
    "Affiliate - Domain Whois",
    "Affiliate - Email Address",
    "Affiliate - Internet Name",
    "Affiliate - Internet Name Hijackable",
    "Affiliate - Internet Name - Unresolved",
    "Affiliate - IP Address",
    "Affiliate - IPv6 Address",
    "Affiliate - Web Content",
    "App Store Entry",
    "Base64-encoded Data",
    "BGP AS Membership",
    "BGP AS Ownership",
    "Bitcoin Address",
    "Bitcoin Balance",
    "Blacklisted Affiliate Internet Name",
    "Blacklisted Affiliate IP Address",
    "Blacklisted Co-Hosted Site",
    "Blacklisted Internet Name",
    "Blacklisted IP Address",
    "Blacklisted IP on Owned Netblock",
    "Blacklisted IP on Same Subnet",
    "Cloud Storage Bucket",
    "Cloud Storage Bucket Open",
    "Company Name",
    "Country Name",
    "Co-Hosted Site",
    "Co-Hosted Site - Domain Name",
    "Co-Hosted Site - Domain Whois",
    "Credit Card Number",
    "Darknet Mention Web Content",
    "Darknet Mention URL",
    "Date of Birth",
    "Defaced Affiliate",
    "Defaced Affiliate IP Address",
    "Defaced Co-Hosted Site",
    "Defaced",
    "Defaced IP Address",
    "NON PRODUCTION SYSTEMS EXPOSED TO INTERNET",
    "Description - Category",
    "Device Type",
    "DNS SPF Record",
    "DNS SRV Record",
    "DNS TXT Record",
    "Domain Name",
    "Domain Name (Parent)",
    "Domain Registrar",
    "Domain Whois",
    "Email Address",
    "Hacked Email Address",
    "Deliverable Email Address",
    "Disposable Email Address",
    "Email Address - Generic",
    "Undeliverable Email Address",
    "Error Message",
    "Ethereum Address",
    "Ethereum Balance",
    "Physical Location",
    "Hash",
    "Compromised Password Hash",
    "HTTP Status Code",
    "Human Name",
    "IBAN Number",
    "Interesting File",
    "Historic Interesting File",
    "IP Address - Internal Network",
    "Internet Name",
    "Internet Name - Unresolved",
    "IPv6 Address",
    "IP Address",
    "Job Title",
    "Junk File",
    "Leak Site Content",
    "Leak Site URL",
    "Legal Entity Identifier",
    "Linked URL - External",
    "Linked URL - Internal",
    "Malicious Affiliate",
    "Malicious Affiliate IP Address",
    "Malicious AS",
    "Malicious Bitcoin Address",
    "Malicious Co-Hosted Site",
    "Malicious E-mail Address",
    "Malicious Internet Name",
    "Malicious IP Address",
    "Malicious IP on Owned Netblock",
    "Malicious Phone Number",
    "Malicious IP on Same Subnet",
    "Netblock IPv6 Membership",
    "Netblock IPv6 Ownership",
    "Netblock Membership",
    "Netblock Ownership",
    "Netblock Whois",
    "Operating System",
    "Compromised Password",
    "PGP Public Key",
    "Phone Number",
    "Phone Number Compromised",
    "Phone Number Type",
    "Physical Address",
    "Physical Coordinates",
    "Name Server (DNS NS Records)",
    "Hosting Provider",
    "Externally Hosted Javascript",
    "Email Gateway (DNS MX Records)",
    "Telecommunications Provider",
    "Proxy Host",
    "Public Code Repository",
    "Raw DNS Records",
    "Raw File Meta Data",
    "Raw Data from RIRs/APIs",
    "Internal SpiderFoot Root event",
    "Search Engine Web Content",
    "Similar Domain",
    "Similar Domain - Whois",
    "Similar Account on External Site",
    "Social Media Presence",
    "Software Used",
    "SSL Certificate Expired",
    "SSL Certificate Expiring",
    "SSL Certificate - Issued to",
    "SSL Certificate - Issued by",
    "SSL Certificate Host Mismatch",
    "SSL Certificate - Raw Data",
    "Web Content",
    "Web Content Type",
    "Cookies",
    "Open TCP Port",
    "Open TCP Port Banner",
    "TOR Exit Node",
    "Open UDP Port",
    "Open UDP Port Information",
    "URL (AdBlocked External)",
    "URL (AdBlocked Internal)",
    "URL (Uses Flash)",
    "Historic URL (Uses Flash)",
    "URL (Form)",
    "Historic URL (Form)",
    "URL (Uses Javascript)",
    "Historic URL (Uses Javascript)",
    "URL (Uses Java Applet)",
    "Historic URL (Uses Java Applet)",
    "URL (Accepts Passwords)",
    "Historic URL (Accepts Passwords)",
    "URL (Purely Static)",
    "Historic URL (Purely Static)",
    "URL (Accepts Uploads)",
    "Historic URL (Accepts Uploads)",
    "URL (Uses a Web Framework)",
    "Historic URL (Uses a Web Framework)",
    "Username",
    "VPN Host",
    "Vulnerability - CVE Critical",
    "Vulnerability - CVE High",
    "Vulnerability - CVE Low",
    "Vulnerability - CVE Medium",
    "Vulnerability - Third Party Disclosure",
    "Vulnerability - General",
    "Web Server",
    "HTTP Headers",
    "Non-Standard HTTP Header",
    "Web Technology",
    "Web Analytics",
    "WiFi Access Point Nearby",
    "3:174",
    "Lat"
]

def extract_blocks_with_types(file_path, wanted_types):
    matching_blocks = []
    found_types = set()
    total_items = 0
    
    print(f"Reading file: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-16') as file:
            for line_num, line in enumerate(file, 1):
                # Print first few lines to see what we're working with
                if line_num <= 5:
                    print(f"\nLine {line_num}: {repr(line[:200])}")
                
                # Skip non-JSON lines with debug output
                if not line.strip():
                    if line_num <= 5:
                        print(f"Skipping empty line {line_num}")
                    continue
                if line.startswith('[*]') or line.startswith('[9'):
                    if line_num <= 5:
                        print(f"Skipping log line {line_num}: {line.strip()}")
                    continue
                
                try:
                    line = line.strip()
                    # Debug JSON parsing for first few lines
                    if line_num <= 5:
                        print(f"\nProcessing line {line_num}:")
                        print(f"Line starts with '[{{': {line.startswith('[{')}")
                        print(f"Line ends with '}}]': {line.endswith('}]')}")
                        print(f"Line content: {repr(line)}")
                    
                    if '[{' in line and '}]' in line:
                        # Extract JSON array part
                        start = line.find('[{')
                        end = line.rfind('}]') + 2
                        json_str = line[start:end]
                        
                        if line_num <= 5:
                            print(f"Attempting to parse JSON: {repr(json_str)}")
                        
                        items = json.loads(json_str)
                        total_items += len(items)
                        for item in items:
                            if isinstance(item, dict) and 'type' in item:
                                type_value = item['type']
                                found_types.add(type_value)
                                if type_value in wanted_types:
                                    matching_blocks.append(item)
                                    print(f"Match found: {type_value} - {item.get('data', 'N/A')}")
                    
                    elif '{' in line and '}' in line:
                        # Extract single JSON object
                        start = line.find('{')
                        end = line.rfind('}') + 1
                        json_str = line[start:end]
                        
                        if line_num <= 5:
                            print(f"Attempting to parse single JSON: {repr(json_str)}")
                        
                        item = json.loads(json_str)
                        total_items += 1
                        if isinstance(item, dict) and 'type' in item:
                            type_value = item['type']
                            found_types.add(type_value)
                            if type_value in wanted_types:
                                matching_blocks.append(item)
                                print(f"Match found: {type_value} - {item.get('data', 'N/A')}")
                
                except json.JSONDecodeError as e:
                    if line_num <= 5:
                        print(f"JSON decode error at line {line_num}: {str(e)}")
                    continue
                
                if line_num % 5000 == 0:
                    print(f"Processed {line_num} lines, {total_items} items, {len(matching_blocks)} matches...")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return "[]"
    
    print("\n=== Summary ===")
    print(f"Total lines processed: {line_num}")
    print(f"Total JSON items found: {total_items}")
    print(f"Matching blocks found: {len(matching_blocks)}")
    if found_types:
        print("\nTypes found:")
        for t in sorted(found_types):
            mark = "✓" if t in wanted_types else "×"
            print(f"{mark} {t}")
    
    return json.dumps(matching_blocks, indent=2)

file_path = 'result.json'
output_path = 'filtered_result.json'

matching_blocks_json = extract_blocks_with_types(file_path, wanted_types)

with open(output_path, 'w') as f:
    f.write(matching_blocks_json)

print(f"Results saved to {output_path}")
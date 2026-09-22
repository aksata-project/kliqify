import re

with open('c:/Users/ACER/Documents/kliqify/dashboard.xml', 'r', encoding='utf-8') as f:
    text = f.read()

# Find all script blocks
scripts = re.finditer(r'<script.*?>', text)
for m in scripts:
    line_num = text[:m.start()].count('\n') + 1
    # Look for the next </script>
    end_script = text.find('</script>', m.end())
    if end_script == -1:
        print(f"ERROR: Unclosed <script> at line {line_num}")
        continue
    
    script_content = text[m.end():end_script].strip()
    if not script_content.startswith('//<![CDATA['):
        print(f"WARNING: Script at line {line_num} does not start with //<![CDATA[")
    if not script_content.endswith('//]]>'):
        print(f"WARNING: Script at line {line_num} does not end with //]]>")
    
    # Check for any ]]> inside the content that is NOT at the end
    if ']]>' in script_content[:-5]:
        print(f"ERROR: Illegal ]]> inside script content at line {line_num}")

print("CDATA check complete")

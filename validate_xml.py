import xml.etree.ElementTree as ET
import sys

def validate_xml(filename):
    try:
        ET.parse(filename)
        print(f"Successfully validated {filename}")
    except ET.ParseError as e:
        print(f"XML Parse Error in {filename}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    validate_xml('dashboard.xml')

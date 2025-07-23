#!/usr/bin/env python3
"""Extract coverage percentage from coverage.xml file."""
import xml.etree.ElementTree as ET

try:
    tree = ET.parse("coverage.xml")
    root = tree.getroot()
    line_rate = float(root.attrib.get("line-rate", "0"))
    print(round(line_rate * 100, 2))
except Exception:
    print(0)


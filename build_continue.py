import os
import re

# Web App URL
GAS_APP_URL = "https://script.google.com/macros/s/AKfycbwfrvMHobcqELJknZzUButaPCZhnWQQbNyYldC_UIHcwQEzgLplcrhaz8lbkApHyvAB/exec"

def make_xml_safe(html_str):
    """Make HTML safe for Blogger XML by fixing void elements, boolean attrs, and entities."""
    # Fix boolean attributes
    def fix_booleans(match):
        tag_content = match.group(0)
        boolean_attrs = ['required', 'disabled', 'checked', 'readonly', 'selected', 'multiple', 'autofocus', 'defer', 'async']
        for attr in boolean_attrs:
            pattern = re.compile(r'\b' + attr + r'\b(?!\s*=)', re.IGNORECASE)
            tag_content = pattern.sub(f'{attr}="{attr}"', tag_content)
        return tag_content

    html_str = re.sub(r'<[^>]+>', fix_booleans, html_str)

    # Self-close void elements
    void_elements = ['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr']
    for tag in void_elements:
        pattern = re.compile(r'<' + tag + r'\b([^>]*?)(?<!/)>', re.IGNORECASE)
        html_str = pattern.sub(r'<' + tag + r'\1/>', html_str)
    
    # Fix HTML entities to XML-safe equivalents
    html_str = html_str.replace('&nbsp;', '&#160;')
    html_str = html_str.replace('&trade;', '&#8482;')
    html_str = html_str.replace('&reg;', '&#174;')
    html_str = html_str.replace('&middot;', '&#183;')
    html_str = html_str.replace('&bull;', '&#8226;')
    html_str = html_str.replace('&laquo;', '&#171;')
    html_str = html_str.replace('&raquo;', '&#187;')
    html_str = html_str.replace('&copy;', '&#169;')
    
    # Escape standalone ampersands (e.g. in URLs like &display=swap)
    # This ignores ampersands that are already part of an entity like &#160; or &amp;
    html_str = re.sub(r'&(?![a-zA-Z0-9#]+;)', '&amp;', html_str)

    return html_str

def build_continue_xml():
    with open('continue.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace GAS_APP_URL placeholder
    content = content.replace("'<?= GAS_APP_URL ?>'", f"'{GAS_APP_URL}'")

    # Extract CSS from <style> tags
    css_content = ""
    style_matches = re.finditer(r'<style[^>]*>(.*?)</style>', content, re.IGNORECASE | re.DOTALL)
    for match in style_matches:
        css_content += match.group(1) + "\n"
    
    # Strip CSS comments for clean output
    css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)

    # Remove style tags from content
    content_no_style = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.IGNORECASE | re.DOTALL)

    # Extract scripts
    scripts = []
    def script_extractor(match):
        attrs = match.group(1)
        inner = match.group(2)
        placeholder = f"__SCRIPT_{len(scripts)}__"
        scripts.append((placeholder, attrs, inner))
        return placeholder
    
    content_no_scripts = re.sub(r'<script([^>]*)>(.*?)</script>', script_extractor, content_no_style, flags=re.IGNORECASE | re.DOTALL)

    # Extract body
    body_match = re.search(r'<body[^>]*>(.*?)</body>', content_no_scripts, re.IGNORECASE | re.DOTALL)
    body_content = body_match.group(1) if body_match else ""
    body_content = make_xml_safe(body_content)

    # Restore scripts with CDATA wrapping
    for placeholder, attrs, inner in scripts:
        if '<![CDATA[' not in inner:
            inner = f"\n//<![CDATA[\n{inner}\n//]]>\n"
        restored = f"<script{attrs}>{inner}</script>"
        body_content = body_content.replace(placeholder, restored)

    # Extract <link> and <meta> from head
    head_match = re.search(r'<head[^>]*>(.*?)</head>', content, re.IGNORECASE | re.DOTALL)
    head_content = head_match.group(1) if head_match else ""
    
    # Get external links (fonts, icons)
    external_links = re.findall(r'<link[^>]*href=["\'][^"\']*["\'][^>]*/?\s*>', head_content, re.IGNORECASE)
    external_links_str = "\n    ".join(make_xml_safe(l) for l in external_links)

    # Build the Blogger XML template
    xml_template = f"""<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html>
<html b:css='false' b:defaultwidgetversion='2' b:layoutsVersion='3' b:responsive='true' b:templateUrl='vegeclub.xml' b:templateVersion='1.0.0' expr:dir='data:blog.languageDirection' xmlns='http://www.w3.org/1999/xhtml' xmlns:b='http://www.google.com/2005/gml/b' xmlns:data='http://www.google.com/2005/gml/data' xmlns:expr='http://www.google.com/2005/gml/expr'>
<head>
    <b:include data='blog' name='all-head-content'/>
    <meta content='width=device-width, initial-scale=1' name='viewport'/>
    <title><data:blog.pageTitle/></title>
    
    {external_links_str}

    <b:skin><![CDATA[
{css_content}
    ]]></b:skin>
</head>
<body>
    <b:section class='main' id='main' showaddelement='yes'>
        <b:widget id='HTML1' locked='false' title='Continue App' type='HTML' version='2' visible='true'>
            <b:includable id='main'>
{body_content}
            </b:includable>
        </b:widget>
    </b:section>
</body>
</html>"""

    with open('continue.xml', 'w', encoding='utf-8') as f:
        f.write(xml_template)
    
    print("Successfully built continue.xml")

if __name__ == '__main__':
    build_continue_xml()

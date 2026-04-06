import re

with open('app.py', 'r') as f:
    content = f.read()

if "render_template_string" not in content[:500]:
    content = content.replace("from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash", "from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, render_template_string")

with open('app.py', 'w') as f:
    f.write(content)

#!/usr/bin/env python3
"""
FinSight Jenkins Plugin Auto-Installer
Installs all required plugins via Jenkins REST API after server startup.
Run this AFTER Jenkins is fully started and you've completed initial setup.
"""

import subprocess
import sys
import time
import urllib.request
import urllib.error
import base64

JENKINS_URL = "http://localhost:8080"
ADMIN_USER = "admin"

REQUIRED_PLUGINS = [
    "git",
    "workflow-aggregator",   # Pipeline
    "docker-workflow",       # Docker Pipeline
    "docker-plugin",         # Docker plugin
    "blueocean",             # Blue Ocean UI
    "pipeline-stage-view",   # Classic pipeline visualization
    "junit",                 # Test results
    "timestamper",           # Timestamps in console
    "build-timeout",         # Build timeout
    "ws-cleanup",            # Workspace cleanup
    "github",                # GitHub integration
    "pipeline-github-lib",   # GitHub library
    "credentials-binding",   # Credentials binding
    "ssh-slaves",            # SSH agents
    "matrix-auth",           # Matrix authorization
    "pam-auth",              # PAM authentication
    "ldap",                  # LDAP
    "email-ext",             # Email notification
    "mailer",                # Mailer
    "ant",                   # Ant
    "gradle",                # Gradle
]

def get_crumb(jenkins_url, user, password):
    """Get CSRF crumb for Jenkins API calls."""
    req = urllib.request.Request(f"{jenkins_url}/crumbIssuer/api/json")
    credentials = base64.b64encode(f"{user}:{password}".encode()).decode()
    req.add_header("Authorization", f"Basic {credentials}")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            import json
            data = json.loads(response.read())
            return data["crumbRequestField"], data["crumb"]
    except Exception as e:
        print(f"Warning: Could not get crumb: {e}")
        return None, None

def install_plugins(jenkins_url, user, password):
    """Install plugins via Jenkins Plugin Manager API."""
    crumb_field, crumb = get_crumb(jenkins_url, user, password)
    
    plugins_xml = "".join([f"<install plugin='{p}@latest'/>" for p in REQUIRED_PLUGINS])
    xml_body = f"<jenkins><install>{plugins_xml}</install></jenkins>"
    
    credentials = base64.b64encode(f"{user}:{password}".encode()).decode()
    req = urllib.request.Request(
        f"{jenkins_url}/pluginManager/installNecessaryPlugins",
        data=xml_body.encode(),
        method="POST"
    )
    req.add_header("Authorization", f"Basic {credentials}")
    req.add_header("Content-Type", "text/xml")
    if crumb_field:
        req.add_header(crumb_field, crumb)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            print(f"Plugin installation triggered: HTTP {response.status}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        
def main():
    print("FinSight Jenkins Plugin Installer")
    print("=" * 40)
    
    # Get admin password
    password = input("Enter Jenkins admin password (from 'cat jenkins_admin_password.txt'): ").strip()
    
    if not password:
        print("Error: Password cannot be empty")
        sys.exit(1)
    
    print(f"\nConnecting to Jenkins at {JENKINS_URL}...")
    print(f"Installing {len(REQUIRED_PLUGINS)} plugins...")
    
    install_plugins(JENKINS_URL, ADMIN_USER, password)
    
    print("\n✅ Plugin installation triggered!")
    print("Jenkins will restart automatically after installation.")
    print("Wait ~2-3 minutes then refresh http://localhost:8080")

if __name__ == "__main__":
    main()

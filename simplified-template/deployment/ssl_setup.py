#!/usr/bin/env python3
"""
SSL/TLS Certificate Setup for Simplified Template

This script helps set up SSL certificates for HTTPS communication.
Supports both self-signed certificates for development and production certificates.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, timedelta

def create_self_signed_cert(
    domain: str = "localhost",
    cert_dir: str = "./certs",
    days: int = 365
) -> tuple[str, str]:
    """
    Create self-signed SSL certificate for development/testing.

    Returns:
        Tuple of (cert_file_path, key_file_path)
    """
    cert_path = Path(cert_dir)
    cert_path.mkdir(exist_ok=True)

    cert_file = cert_path / f"{domain}.crt"
    key_file = cert_path / f"{domain}.key"

    print(f"Creating self-signed certificate for {domain}...")

    # Create certificate with OpenSSL
    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:4096",
        "-keyout", str(key_file),
        "-out", str(cert_file),
        "-days", str(days),
        "-nodes",  # No passphrase
        "-subj", f"/C=US/ST=Test/L=Test/O=Test/CN={domain}"
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Certificate created: {cert_file}")
        print(f"✅ Private key created: {key_file}")

        # Set secure permissions
        os.chmod(key_file, 0o600)
        os.chmod(cert_file, 0o644)

        return str(cert_file), str(key_file)

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create certificate: {e}")
        print(f"Error output: {e.stderr.decode()}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ OpenSSL not found. Please install OpenSSL first.")
        sys.exit(1)


def setup_letsencrypt_cert(domain: str, email: str) -> tuple[str, str]:
    """
    Setup Let's Encrypt certificate using certbot.

    Returns:
        Tuple of (cert_file_path, key_file_path)
    """
    print(f"Setting up Let's Encrypt certificate for {domain}...")

    # Check if certbot is installed
    try:
        subprocess.run(["certbot", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Certbot not found. Please install certbot first:")
        print("   Ubuntu/Debian: sudo apt install certbot")
        print("   CentOS/RHEL: sudo yum install certbot")
        print("   macOS: brew install certbot")
        sys.exit(1)

    # Run certbot
    cmd = [
        "sudo", "certbot", "certonly",
        "--standalone",
        "--email", email,
        "--agree-tos",
        "--no-eff-email",
        "-d", domain
    ]

    try:
        subprocess.run(cmd, check=True)

        cert_file = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
        key_file = f"/etc/letsencrypt/live/{domain}/privkey.pem"

        print(f"✅ Let's Encrypt certificate created: {cert_file}")
        print(f"✅ Private key created: {key_file}")

        return cert_file, key_file

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create Let's Encrypt certificate: {e}")
        sys.exit(1)


def generate_env_config(cert_file: str, key_file: str, output_file: str = ".env.ssl"):
    """Generate environment configuration for SSL."""
    config = f"""# SSL Configuration
SSL_CERT_FILE={cert_file}
SSL_KEY_FILE={key_file}
HTTPS_ENABLED=true
ENVIRONMENT=production

# Auto-generated on {datetime.now().isoformat()}
"""

    with open(output_file, 'w') as f:
        f.write(config)

    print(f"✅ SSL configuration written to {output_file}")
    print(f"💡 To use: cp {output_file} .env")


def verify_certificates(cert_file: str, key_file: str):
    """Verify SSL certificate and key."""
    print("Verifying SSL certificate...")

    # Check if files exist
    if not Path(cert_file).exists():
        print(f"❌ Certificate file not found: {cert_file}")
        return False

    if not Path(key_file).exists():
        print(f"❌ Key file not found: {key_file}")
        return False

    # Check certificate validity
    try:
        cmd = ["openssl", "x509", "-in", cert_file, "-text", "-noout"]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        # Extract expiry date
        for line in result.stdout.split('\n'):
            if 'Not After' in line:
                print(f"📅 Certificate expires: {line.strip()}")
                break

        # Verify key matches certificate
        cert_cmd = ["openssl", "x509", "-noout", "-modulus", "-in", cert_file]
        key_cmd = ["openssl", "rsa", "-noout", "-modulus", "-in", key_file]

        cert_result = subprocess.run(cert_cmd, check=True, capture_output=True, text=True)
        key_result = subprocess.run(key_cmd, check=True, capture_output=True, text=True)

        if cert_result.stdout == key_result.stdout:
            print("✅ Certificate and key match")
            return True
        else:
            print("❌ Certificate and key do not match")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Certificate verification failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="SSL Certificate Setup for Simplified Template")
    parser.add_argument("--domain", default="localhost", help="Domain name for certificate")
    parser.add_argument("--type", choices=["self-signed", "letsencrypt"],
                       default="self-signed", help="Certificate type")
    parser.add_argument("--email", help="Email for Let's Encrypt (required for letsencrypt)")
    parser.add_argument("--days", type=int, default=365,
                       help="Days valid for self-signed cert")
    parser.add_argument("--cert-dir", default="./certs",
                       help="Directory for certificates")
    parser.add_argument("--verify-only", action="store_true",
                       help="Only verify existing certificates")
    parser.add_argument("--cert-file", help="Certificate file to verify")
    parser.add_argument("--key-file", help="Key file to verify")

    args = parser.parse_args()

    if args.verify_only:
        if not args.cert_file or not args.key_file:
            print("❌ --cert-file and --key-file required for verification")
            sys.exit(1)

        if verify_certificates(args.cert_file, args.key_file):
            print("✅ Certificate verification passed")
        else:
            print("❌ Certificate verification failed")
            sys.exit(1)
        return

    if args.type == "letsencrypt":
        if not args.email:
            print("❌ --email required for Let's Encrypt certificates")
            sys.exit(1)
        cert_file, key_file = setup_letsencrypt_cert(args.domain, args.email)
    else:
        cert_file, key_file = create_self_signed_cert(args.domain, args.cert_dir, args.days)

    # Verify the created certificates
    if verify_certificates(cert_file, key_file):
        generate_env_config(cert_file, key_file)

        print("\n🎉 SSL setup complete!")
        print("\nNext steps:")
        print("1. Copy .env.ssl to .env")
        print("2. Set ENVIRONMENT=production in .env")
        print("3. Start the agent with: python src/agent.py")
        print(f"4. Test HTTPS: curl -k https://{args.domain}:8000/health")

        if args.type == "self-signed":
            print("\n⚠️  Note: Self-signed certificates will show browser warnings.")
            print("   For production, use Let's Encrypt or a trusted CA.")
    else:
        print("❌ SSL setup failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
"""
Certificate loader module for handling P12 certificate extraction and management.

This module provides optional certificate-based authentication support.
By default, certificate auth is disabled - set CERT_PATH and CERT_PASSWORD
environment variables to enable it.
"""

import tempfile
import subprocess
import os
import atexit
from typing import Tuple, Optional


class CertificateManager:
    """Manages P12 certificate extraction and temporary file cleanup."""

    def __init__(self):
        """Initialize the certificate manager."""
        self.temp_files = []
        # Register cleanup function to run on exit
        atexit.register(self.cleanup)

    def setup_certificate(self, cert_path: str, cert_password: str) -> Tuple[str, str]:
        """
        Extract certificate and key from a P12 file using openssl.

        Args:
            cert_path: Path to the .p12 certificate file
            cert_password: Password for the P12 certificate

        Returns:
            Tuple of (cert_temp_path, key_temp_path) for use with requests

        Raises:
            FileNotFoundError: If the certificate file doesn't exist
            subprocess.CalledProcessError: If openssl extraction fails
            RuntimeError: If certificate setup fails for other reasons
        """
        # Validate certificate file exists
        if not os.path.exists(cert_path):
            raise FileNotFoundError(f"Certificate file not found: {cert_path}")

        try:
            # Create temporary files for the certificate and key
            cert_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.crt')
            key_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.key')
            cert_temp.close()
            key_temp.close()

            # Track temp files for cleanup
            self.temp_files.extend([cert_temp.name, key_temp.name])

            # Extract certificate from P12 file
            extract_cert_cmd = [
                "openssl", "pkcs12", "-in", cert_path,
                "-clcerts", "-nokeys", "-out", cert_temp.name,
                "-passin", f"pass:{cert_password}",
                "-passout", f"pass:{cert_password}"
            ]

            # Extract private key from P12 file
            extract_key_cmd = [
                "openssl", "pkcs12", "-in", cert_path,
                "-nocerts", "-nodes", "-out", key_temp.name,
                "-passin", f"pass:{cert_password}"
            ]

            # Run the commands to extract cert and key
            subprocess.run(
                extract_cert_cmd,
                check=True,
                capture_output=True,
                text=True
            )
            subprocess.run(
                extract_key_cmd,
                check=True,
                capture_output=True,
                text=True
            )

            # Verify the extracted files exist and are not empty
            if not os.path.exists(cert_temp.name) or os.path.getsize(cert_temp.name) == 0:
                raise RuntimeError("Certificate extraction failed: output file is empty")
            if not os.path.exists(key_temp.name) or os.path.getsize(key_temp.name) == 0:
                raise RuntimeError("Key extraction failed: output file is empty")

            print(f"[confluence-mcp] Certificate extracted successfully from {cert_path}")
            return (cert_temp.name, key_temp.name)

        except subprocess.CalledProcessError as e:
            error_msg = f"OpenSSL extraction failed: {e.stderr if e.stderr else str(e)}"
            self.cleanup()  # Clean up any partially created files
            raise RuntimeError(error_msg) from e
        except Exception as e:
            self.cleanup()  # Clean up any partially created files
            raise RuntimeError(f"Certificate setup failed: {str(e)}") from e

    def cleanup(self):
        """Clean up temporary certificate and key files."""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except (OSError, FileNotFoundError) as e:
                print(f"[confluence-mcp] Warning: Could not delete temporary file {temp_file}: {e}")
        self.temp_files.clear()


def validate_openssl_available() -> bool:
    """
    Validate that openssl is available on the system.

    Returns:
        True if openssl is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["openssl", "version"],
            check=True,
            capture_output=True,
            text=True
        )
        version = result.stdout.strip()
        print(f"[confluence-mcp] OpenSSL is available: {version}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[confluence-mcp] OpenSSL is not available on the system")
        return False


# Global certificate manager instance
cert_manager = CertificateManager()

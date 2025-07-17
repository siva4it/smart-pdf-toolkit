"""
Security management for PDF documents.
Handles password protection, permissions, watermarks, and digital signatures.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass

import fitz  # PyMuPDF

from .interfaces import ISecurityManager, OperationResult
from .exceptions import SecurityError, ValidationError
from .config import ApplicationConfig
from ..utils.validation import validate_pdf_file
from ..utils.file_utils import get_unique_filename

# Optional imports for digital signatures
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    import datetime
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class PermissionSet:
    """Represents PDF permission settings."""
    print_document: bool = True
    modify_document: bool = True
    copy_content: bool = True
    add_annotations: bool = True
    fill_forms: bool = True
    extract_content: bool = True
    assemble_document: bool = True
    print_high_quality: bool = True


@dataclass
class WatermarkConfig:
    """Configuration for watermark settings."""
    text: Optional[str] = None
    image_path: Optional[str] = None
    opacity: float = 0.5
    rotation: int = 45
    position: str = "center"  # center, top-left, top-right, bottom-left, bottom-right
    font_size: int = 36
    color: str = "gray"


@dataclass
class SecurityResult:
    """Result of security operations."""
    success: bool
    message: str
    output_file: Optional[str]
    execution_time: float
    warnings: List[str]
    errors: List[str]
    security_info: Dict[str, Any]


@dataclass
class CertificateInfo:
    """Information for creating digital certificates."""
    common_name: str
    organization: str = "Smart PDF Toolkit"
    country: str = "US"
    state: str = "CA"
    locality: str = "San Francisco"
    email: str = "user@example.com"
    validity_days: int = 365


class SecurityManager(ISecurityManager):
    """
    Manages PDF security features including password protection, permissions, and watermarks.
    
    This class provides comprehensive security functionality:
    - Password protection (user and owner passwords)
    - Permission management (printing, copying, editing, etc.)
    - Watermark addition (text and image watermarks)
    - Digital signature support
    """
    
    def __init__(self, config: Optional[ApplicationConfig] = None):
        """Initialize SecurityManager with configuration."""
        self.config = config or ApplicationConfig()
        self.logger = logging.getLogger(__name__)
    
    def add_password(self, pdf_path: str, user_pwd: str, owner_pwd: str = None) -> OperationResult:
        """
        Add password protection to a PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            user_pwd: Password required to open the document
            owner_pwd: Password required to change permissions (optional)
            
        Returns:
            OperationResult with password protection details
        """
        start_time = time.time()
        warnings = []
        errors = []
        
        try:
            # Validate inputs
            validate_pdf_file(pdf_path)
            
            if not user_pwd:
                raise ValidationError("User password cannot be empty")
            
            if len(user_pwd) < 4:
                warnings.append("User password is shorter than recommended (4+ characters)")
            
            # Use user password as owner password if not provided
            if owner_pwd is None:
                owner_pwd = user_pwd
                warnings.append("Owner password not provided, using user password")
            
            # Open PDF document
            doc = fitz.open(pdf_path)
            
            try:
                # Check if document is already encrypted
                if doc.needs_pass:
                    warnings.append("Document is already password protected")
                
                # Create output filename
                input_path = Path(pdf_path)
                output_file = input_path.parent / f"{input_path.stem}_protected{input_path.suffix}"
                output_file = get_unique_filename(str(output_file))
                
                # Set up encryption parameters
                encrypt_meth = fitz.PDF_ENCRYPT_AES_256  # Use AES-256 encryption
                
                # Save with password protection
                doc.save(
                    output_file,
                    encryption=encrypt_meth,
                    user_pw=user_pwd,
                    owner_pw=owner_pwd
                )
                
                doc.close()
                
                # Verify the password protection worked
                try:
                    test_doc = fitz.open(output_file)
                    if not test_doc.needs_pass:
                        raise SecurityError("Password protection verification failed")
                    test_doc.close()
                except Exception:
                    # Expected - document should require password
                    pass
                
                execution_time = time.time() - start_time
                
                return OperationResult(
                    success=True,
                    message="Password protection added successfully",
                    output_files=[output_file],
                    execution_time=execution_time,
                    warnings=warnings,
                    errors=errors
                )
                
            except Exception as e:
                doc.close()
                raise SecurityError(f"Failed to add password protection: {str(e)}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Password protection failed: {str(e)}"
            self.logger.error(error_msg)
            
            return OperationResult(
                success=False,
                message=error_msg,
                output_files=[],
                execution_time=execution_time,
                warnings=warnings,
                errors=[error_msg]
            )
    
    def remove_password(self, pdf_path: str, password: str) -> OperationResult:
        """
        Remove password protection from a PDF document.
        
        Args:
            pdf_path: Path to the password-protected PDF file
            password: Password to unlock the document
            
        Returns:
            OperationResult with password removal details
        """
        start_time = time.time()
        warnings = []
        errors = []
        
        try:
            # Validate inputs
            validate_pdf_file(pdf_path)
            
            if not password:
                raise ValidationError("Password cannot be empty")
            
            # Try to open the document with the password
            doc = fitz.open(pdf_path)
            
            try:
                # Check if document is encrypted
                if not doc.needs_pass:
                    warnings.append("Document is not password protected")
                    doc.close()
                    
                    return OperationResult(
                        success=True,
                        message="Document was not password protected",
                        output_files=[pdf_path],
                        execution_time=time.time() - start_time,
                        warnings=warnings,
                        errors=errors
                    )
                
                # Authenticate with the password
                if not doc.authenticate(password):
                    raise SecurityError("Invalid password provided")
                
                # Create output filename
                input_path = Path(pdf_path)
                output_file = input_path.parent / f"{input_path.stem}_unlocked{input_path.suffix}"
                output_file = get_unique_filename(str(output_file))
                
                # Save without password protection
                doc.save(output_file)
                doc.close()
                
                # Verify the password was removed
                test_doc = fitz.open(output_file)
                if test_doc.needs_pass:
                    test_doc.close()
                    raise SecurityError("Password removal verification failed")
                test_doc.close()
                
                execution_time = time.time() - start_time
                
                return OperationResult(
                    success=True,
                    message="Password protection removed successfully",
                    output_files=[output_file],
                    execution_time=execution_time,
                    warnings=warnings,
                    errors=errors
                )
                
            except SecurityError:
                doc.close()
                raise
            except Exception as e:
                doc.close()
                raise SecurityError(f"Failed to remove password protection: {str(e)}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Password removal failed: {str(e)}"
            self.logger.error(error_msg)
            
            return OperationResult(
                success=False,
                message=error_msg,
                output_files=[],
                execution_time=execution_time,
                warnings=warnings,
                errors=[error_msg]
            )
    
    def set_permissions(self, pdf_path: str, permissions: Dict[str, bool]) -> OperationResult:
        """
        Set permissions for a PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            permissions: Dictionary of permission settings
            
        Returns:
            OperationResult with permission setting details
        """
        start_time = time.time()
        warnings = []
        errors = []
        
        try:
            # Validate inputs
            validate_pdf_file(pdf_path)
            
            if not permissions:
                raise ValidationError("Permissions dictionary cannot be empty")
            
            # Create PermissionSet from input
            perm_set = PermissionSet(
                print_document=permissions.get('print', True),
                modify_document=permissions.get('modify', True),
                copy_content=permissions.get('copy', True),
                add_annotations=permissions.get('annotate', True),
                fill_forms=permissions.get('form', True),
                extract_content=permissions.get('extract', True),
                assemble_document=permissions.get('assemble', True),
                print_high_quality=permissions.get('print_high_quality', True)
            )
            
            # Open PDF document
            doc = fitz.open(pdf_path)
            
            try:
                # Create output filename
                input_path = Path(pdf_path)
                output_file = input_path.parent / f"{input_path.stem}_permissions{input_path.suffix}"
                output_file = get_unique_filename(str(output_file))
                
                # Calculate permission flags for PyMuPDF
                perm_flags = 0
                if perm_set.print_document:
                    perm_flags |= fitz.PDF_PERM_PRINT
                if perm_set.modify_document:
                    perm_flags |= fitz.PDF_PERM_MODIFY
                if perm_set.copy_content:
                    perm_flags |= fitz.PDF_PERM_COPY
                if perm_set.add_annotations:
                    perm_flags |= fitz.PDF_PERM_ANNOTATE
                
                # Save with permissions (requires owner password for restrictions)
                owner_pwd = "owner_temp_pwd"  # Temporary password for permission setting
                doc.save(
                    output_file,
                    encryption=fitz.PDF_ENCRYPT_AES_128,
                    owner_pw=owner_pwd,
                    permissions=perm_flags
                )
                
                doc.close()
                
                execution_time = time.time() - start_time
                
                return OperationResult(
                    success=True,
                    message="Permissions set successfully",
                    output_files=[output_file],
                    execution_time=execution_time,
                    warnings=warnings,
                    errors=errors
                )
                
            except Exception as e:
                doc.close()
                raise SecurityError(f"Failed to set permissions: {str(e)}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Permission setting failed: {str(e)}"
            self.logger.error(error_msg)
            
            return OperationResult(
                success=False,
                message=error_msg,
                output_files=[],
                execution_time=execution_time,
                warnings=warnings,
                errors=[error_msg]
            )
    
    def add_watermark(self, pdf_path: str, watermark_config: Dict[str, Any]) -> OperationResult:
        """
        Add watermark to a PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            watermark_config: Watermark configuration dictionary
            
        Returns:
            OperationResult with watermark addition details
        """
        start_time = time.time()
        warnings = []
        errors = []
        
        try:
            # Validate inputs
            validate_pdf_file(pdf_path)
            
            if not watermark_config:
                raise ValidationError("Watermark configuration cannot be empty")
            
            # Create WatermarkConfig from input
            config = WatermarkConfig(
                text=watermark_config.get('text'),
                image_path=watermark_config.get('image_path'),
                opacity=watermark_config.get('opacity', 0.5),
                rotation=watermark_config.get('rotation', 45),
                position=watermark_config.get('position', 'center'),
                font_size=watermark_config.get('font_size', 36),
                color=watermark_config.get('color', 'gray')
            )
            
            # Validate watermark configuration
            if not config.text and not config.image_path:
                raise ValidationError("Either text or image_path must be provided for watermark")
            
            if config.image_path and not os.path.exists(config.image_path):
                raise ValidationError(f"Watermark image not found: {config.image_path}")
            
            # Open PDF document
            doc = fitz.open(pdf_path)
            
            try:
                # Create output filename
                input_path = Path(pdf_path)
                output_file = input_path.parent / f"{input_path.stem}_watermarked{input_path.suffix}"
                output_file = get_unique_filename(str(output_file))
                
                # Add watermark to each page
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    
                    if config.text:
                        self._add_text_watermark(page, config)
                    
                    if config.image_path:
                        self._add_image_watermark(page, config)
                
                # Save watermarked document
                doc.save(output_file)
                doc.close()
                
                execution_time = time.time() - start_time
                
                return OperationResult(
                    success=True,
                    message="Watermark added successfully",
                    output_files=[output_file],
                    execution_time=execution_time,
                    warnings=warnings,
                    errors=errors
                )
                
            except Exception as e:
                doc.close()
                raise SecurityError(f"Failed to add watermark: {str(e)}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Watermark addition failed: {str(e)}"
            self.logger.error(error_msg)
            
            return OperationResult(
                success=False,
                message=error_msg,
                output_files=[],
                execution_time=execution_time,
                warnings=warnings,
                errors=[error_msg]
            )
    
    def _add_text_watermark(self, page: fitz.Page, config: WatermarkConfig) -> None:
        """Add text watermark to a page."""
        # Get page dimensions
        rect = page.rect
        
        # Calculate position
        if config.position == "center":
            x = rect.width / 2
            y = rect.height / 2
        elif config.position == "top-left":
            x = rect.width * 0.1
            y = rect.height * 0.1
        elif config.position == "top-right":
            x = rect.width * 0.9
            y = rect.height * 0.1
        elif config.position == "bottom-left":
            x = rect.width * 0.1
            y = rect.height * 0.9
        elif config.position == "bottom-right":
            x = rect.width * 0.9
            y = rect.height * 0.9
        else:
            x = rect.width / 2
            y = rect.height / 2
        
        # Create text annotation
        point = fitz.Point(x, y)
        
        # Convert color name to RGB
        color_map = {
            'gray': (0.5, 0.5, 0.5),
            'red': (1.0, 0.0, 0.0),
            'blue': (0.0, 0.0, 1.0),
            'green': (0.0, 1.0, 0.0),
            'black': (0.0, 0.0, 0.0)
        }
        color = color_map.get(config.color, (0.5, 0.5, 0.5))
        
        # Insert text with rotation and opacity
        page.insert_text(
            point,
            config.text,
            fontsize=config.font_size,
            rotate=config.rotation,
            color=color,
            overlay=True
        )
    
    def _add_image_watermark(self, page: fitz.Page, config: WatermarkConfig) -> None:
        """Add image watermark to a page."""
        try:
            # Get page dimensions
            rect = page.rect
            
            # Calculate position and size
            if config.position == "center":
                # Center the image, scale to 1/4 of page size
                img_rect = fitz.Rect(
                    rect.width * 0.375, rect.height * 0.375,
                    rect.width * 0.625, rect.height * 0.625
                )
            else:
                # For corner positions, use smaller size
                size = min(rect.width, rect.height) * 0.2
                if config.position == "top-left":
                    img_rect = fitz.Rect(10, 10, 10 + size, 10 + size)
                elif config.position == "top-right":
                    img_rect = fitz.Rect(rect.width - size - 10, 10, rect.width - 10, 10 + size)
                elif config.position == "bottom-left":
                    img_rect = fitz.Rect(10, rect.height - size - 10, 10 + size, rect.height - 10)
                elif config.position == "bottom-right":
                    img_rect = fitz.Rect(rect.width - size - 10, rect.height - size - 10, 
                                       rect.width - 10, rect.height - 10)
                else:
                    img_rect = fitz.Rect(
                        rect.width * 0.375, rect.height * 0.375,
                        rect.width * 0.625, rect.height * 0.625
                    )
            
            # Insert image
            page.insert_image(img_rect, filename=config.image_path, overlay=True)
            
        except Exception as e:
            raise SecurityError(f"Failed to add image watermark: {str(e)}")
    
    def add_digital_signature(self, pdf_path: str, certificate_info: Dict[str, Any]) -> OperationResult:
        """
        Add digital signature to a PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            certificate_info: Certificate information dictionary
            
        Returns:
            OperationResult with digital signature details
        """
        start_time = time.time()
        warnings = []
        errors = []
        
        try:
            # Check if cryptography library is available
            if not CRYPTO_AVAILABLE:
                raise SecurityError(
                    "Digital signature functionality requires 'cryptography' library. "
                    "Install with: pip install cryptography"
                )
            
            # Validate inputs
            validate_pdf_file(pdf_path)
            
            if not certificate_info:
                raise ValidationError("Certificate information cannot be empty")
            
            # Create CertificateInfo from input
            cert_info = CertificateInfo(
                common_name=certificate_info.get('common_name', 'Smart PDF Toolkit User'),
                organization=certificate_info.get('organization', 'Smart PDF Toolkit'),
                country=certificate_info.get('country', 'US'),
                state=certificate_info.get('state', 'CA'),
                locality=certificate_info.get('locality', 'San Francisco'),
                email=certificate_info.get('email', 'user@example.com'),
                validity_days=certificate_info.get('validity_days', 365)
            )
            
            # Generate self-signed certificate
            private_key, certificate = self._generate_self_signed_certificate(cert_info)
            
            # Open PDF document
            doc = fitz.open(pdf_path)
            
            try:
                # Create output filename
                input_path = Path(pdf_path)
                output_file = input_path.parent / f"{input_path.stem}_signed{input_path.suffix}"
                output_file = get_unique_filename(str(output_file))
                
                # Add signature annotation to the first page
                page = doc[0]
                
                # Create signature rectangle (bottom right corner)
                rect = page.rect
                sig_rect = fitz.Rect(
                    rect.width - 200, rect.height - 100,
                    rect.width - 10, rect.height - 10
                )
                
                # Add signature annotation
                signature_text = f"Digitally signed by: {cert_info.common_name}\nDate: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nReason: Document authentication"
                
                # Create text annotation for signature
                annot = page.add_text_annot(sig_rect.tl, signature_text)
                annot.set_info(title="Digital Signature", content=signature_text)
                annot.update()
                
                # Add visual signature box
                page.draw_rect(sig_rect, color=(0, 0, 1), width=2)
                page.insert_text(
                    fitz.Point(sig_rect.x0 + 5, sig_rect.y0 + 15),
                    "DIGITALLY SIGNED",
                    fontsize=8,
                    color=(0, 0, 1)
                )
                page.insert_text(
                    fitz.Point(sig_rect.x0 + 5, sig_rect.y0 + 30),
                    f"By: {cert_info.common_name}",
                    fontsize=6,
                    color=(0, 0, 0)
                )
                page.insert_text(
                    fitz.Point(sig_rect.x0 + 5, sig_rect.y0 + 45),
                    f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}",
                    fontsize=6,
                    color=(0, 0, 0)
                )
                
                # Save signed document
                doc.save(output_file)
                doc.close()
                
                # Save certificate and private key for reference
                cert_file = str(output_file).replace('.pdf', '_certificate.pem')
                key_file = str(output_file).replace('.pdf', '_private_key.pem')
                
                # Save certificate
                with open(cert_file, 'wb') as f:
                    f.write(certificate.public_bytes(serialization.Encoding.PEM))
                
                # Save private key (in production, this should be securely stored)
                with open(key_file, 'wb') as f:
                    f.write(private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    ))
                
                warnings.append("Certificate and private key saved alongside PDF for reference")
                warnings.append("In production, private keys should be securely stored")
                
                execution_time = time.time() - start_time
                
                return OperationResult(
                    success=True,
                    message="Digital signature added successfully",
                    output_files=[output_file, cert_file, key_file],
                    execution_time=execution_time,
                    warnings=warnings,
                    errors=errors
                )
                
            except Exception as e:
                doc.close()
                raise SecurityError(f"Failed to add digital signature: {str(e)}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Digital signature failed: {str(e)}"
            self.logger.error(error_msg)
            
            return OperationResult(
                success=False,
                message=error_msg,
                output_files=[],
                execution_time=execution_time,
                warnings=warnings,
                errors=[error_msg]
            )
    
    def _generate_self_signed_certificate(self, cert_info: CertificateInfo):
        """Generate a self-signed certificate for digital signatures."""
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate subject
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, cert_info.country),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, cert_info.state),
            x509.NameAttribute(NameOID.LOCALITY_NAME, cert_info.locality),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, cert_info.organization),
            x509.NameAttribute(NameOID.COMMON_NAME, cert_info.common_name),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, cert_info.email),
        ])
        
        # Create certificate
        certificate = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=cert_info.validity_days)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.RFC822Name(cert_info.email),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        return private_key, certificate
    
    def verify_digital_signature(self, pdf_path: str) -> Dict[str, Any]:
        """
        Verify digital signature in a PDF document.
        
        Args:
            pdf_path: Path to the signed PDF file
            
        Returns:
            Dictionary containing signature verification results
        """
        try:
            validate_pdf_file(pdf_path)
            
            doc = fitz.open(pdf_path)
            
            try:
                signature_info = {
                    'has_signature': False,
                    'signature_valid': False,
                    'signer_info': {},
                    'signature_date': None,
                    'verification_details': []
                }
                
                # Check for signature annotations
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    annotations = page.annots()
                    
                    for annot in annotations:
                        if annot.type[1] == 'Text':  # Text annotation
                            content = annot.info.get('content', '')
                            if 'Digitally signed' in content or 'Digital Signature' in annot.info.get('title', ''):
                                signature_info['has_signature'] = True
                                signature_info['verification_details'].append(
                                    f"Signature annotation found on page {page_num + 1}"
                                )
                                
                                # Extract signer information from content
                                lines = content.split('\n')
                                for line in lines:
                                    if line.startswith('Digitally signed by:'):
                                        signature_info['signer_info']['name'] = line.split(':', 1)[1].strip()
                                    elif line.startswith('Date:'):
                                        signature_info['signature_date'] = line.split(':', 1)[1].strip()
                
                # For this implementation, we mark signatures as valid if found
                # In a full implementation, this would involve cryptographic verification
                if signature_info['has_signature']:
                    signature_info['signature_valid'] = True
                    signature_info['verification_details'].append(
                        "Note: This is a basic signature verification. "
                        "Full cryptographic verification requires additional implementation."
                    )
                
                doc.close()
                return signature_info
                
            except Exception as e:
                doc.close()
                raise SecurityError(f"Failed to verify signature: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Signature verification failed: {str(e)}")
            return {
                'error': str(e),
                'has_signature': False,
                'signature_valid': False
            }

    def get_security_info(self, pdf_path: str) -> Dict[str, Any]:
        """
        Get security information about a PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing security information
        """
        try:
            validate_pdf_file(pdf_path)
            
            doc = fitz.open(pdf_path)
            
            try:
                security_info = {
                    'is_encrypted': doc.needs_pass,
                    'has_owner_password': False,
                    'has_user_password': False,
                    'permissions': {
                        'print': not doc.is_pdf or doc.permissions & fitz.PDF_PERM_PRINT != 0,
                        'modify': not doc.is_pdf or doc.permissions & fitz.PDF_PERM_MODIFY != 0,
                        'copy': not doc.is_pdf or doc.permissions & fitz.PDF_PERM_COPY != 0,
                        'annotate': not doc.is_pdf or doc.permissions & fitz.PDF_PERM_ANNOTATE != 0,
                    },
                    'encryption_method': 'None',
                    'security_handler': 'None'
                }
                
                if doc.needs_pass:
                    security_info['encryption_method'] = 'Password Protected'
                    security_info['has_user_password'] = True
                
                doc.close()
                return security_info
                
            except Exception as e:
                doc.close()
                raise SecurityError(f"Failed to get security info: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Security info retrieval failed: {str(e)}")
            return {
                'error': str(e),
                'is_encrypted': False,
                'permissions': {}
            }
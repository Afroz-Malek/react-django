"""
Debug OTP Verification Issues
Run: python debug_otp.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockstar_backend.settings')
django.setup()

from stockstarauthversionone.models import User, OTPVerification
from django.utils import timezone

def debug_otp():
    """Debug OTP verification issues"""
    print("=" * 80)
    print("OTP DEBUGGING TOOL")
    print("=" * 80)
    print()
    
    # Ask for email
    email = input("Enter email to check: ").strip().lower()
    
    # Check if user exists
    try:
        user = User.objects.get(email=email)
        print(f"\n✓ User found: {user.email}")
        print(f"  - User ID: {user.id}")
        print(f"  - Name: {user.get_full_name()}")
        print(f"  - Is Verified: {user.is_verified}")
        print(f"  - Is Active: {user.is_active}")
    except User.DoesNotExist:
        print(f"\n✗ User not found with email: {email}")
        return
    
    print("\n" + "-" * 80)
    print("OTP CODES FOR THIS USER:")
    print("-" * 80)
    
    # Get all OTPs for this user
    all_otps = OTPVerification.objects.filter(user=user).order_by('-created_at')
    
    if not all_otps.exists():
        print("✗ No OTP codes found for this user")
        return
    
    print(f"\nTotal OTP codes generated: {all_otps.count()}\n")
    
    for idx, otp in enumerate(all_otps, 1):
        print(f"OTP #{idx}:")
        print(f"  Code: {otp.otp_code}")
        print(f"  Created: {otp.created_at}")
        print(f"  Expires: {otp.expires_at}")
        print(f"  Used: {otp.is_used}")
        print(f"  Type: {otp.verification_type}")
        
        # Check if valid
        if otp.is_valid():
            time_left = otp.expires_at - timezone.now()
            minutes_left = int(time_left.total_seconds() / 60)
            print(f"  Status: ✓ VALID (expires in {minutes_left} minutes)")
            print(f"  👉 USE THIS CODE: {otp.otp_code}")
        else:
            if otp.is_used:
                print(f"  Status: ✗ ALREADY USED")
            elif timezone.now() >= otp.expires_at:
                print(f"  Status: ✗ EXPIRED")
            else:
                print(f"  Status: ✗ INVALID")
        print()
    
    # Show latest valid OTP
    print("=" * 80)
    valid_otp = OTPVerification.objects.filter(
        user=user,
        is_used=False,
        expires_at__gt=timezone.now()
    ).order_by('-created_at').first()
    
    if valid_otp:
        print("✓ CURRENT VALID OTP:")
        print(f"  Email: {email}")
        print(f"  OTP Code: {valid_otp.otp_code}")
        time_left = valid_otp.expires_at - timezone.now()
        minutes_left = int(time_left.total_seconds() / 60)
        print(f"  Expires in: {minutes_left} minutes")
        print()
        print("Use this in Postman:")
        print(f"""
{{
    "email": "{email}",
    "otp_code": "{valid_otp.otp_code}"
}}
        """)
    else:
        print("✗ NO VALID OTP FOUND")
        print("\nReasons:")
        print("  1. All OTPs have expired (10 minute limit)")
        print("  2. All OTPs have been used")
        print("\nSolution:")
        print("  Use the 'Resend OTP' endpoint to get a new code")
        print(f"""
POST /api/authentication/stockstarcapital-usercreation-versionone/resend-otp/
{{
    "email": "{email}"
}}
        """)
    
    print("=" * 80)

if __name__ == "__main__":
    debug_otp()
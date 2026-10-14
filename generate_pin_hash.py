import sys
import bcrypt

def generate_pin_hash(pin: str = "1234"):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pin.encode('utf-8'), salt).decode('utf-8')
    print("=" * 60)
    print(f"Plain PIN: {pin}")
    print(f"Bcrypt Hash: {hashed}")
    print("=" * 60)
    print("Copy this hash into your .env file as:")
    print(f'MASTER_PIN_HASH="{hashed}"')
    print("=" * 60)

if __name__ == "__main__":
    pin_input = sys.argv[1] if len(sys.argv) > 1 else "1234"
    generate_pin_hash(pin_input)

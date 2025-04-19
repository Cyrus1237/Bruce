from mini_bdx_runtime.feet_contacts import FeetContacts
import time



if __name__ == "__main__":
    import time
    from datetime import datetime

    feet_contacts = FeetContacts()
    
    try:
        print("Foot Contact Test - Press CTRL+C to exit")
        while True:
            contacts = feet_contacts.get()
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Create human-readable status
            left_status = "PRESSED" if contacts[0] else "open"
            right_status = "PRESSED" if contacts[1] else "open"
            
            print(f"[{timestamp}] Left: {left_status:<7} | Right: {right_status:<7}")
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nTest terminated by user")
    finally:
        GPIO.cleanup()  # Important for proper hardware reset

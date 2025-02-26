# Global configuration variables
test_mode = False

def set_test_mode(value: bool):
    global test_mode
    test_mode = value
    print(f"config.py:: Running in {'test' if test_mode else 'production'} mode") 
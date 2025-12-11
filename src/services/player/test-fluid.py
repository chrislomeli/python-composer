from ctypes import cdll
import ctypes.util
import os

# Method 1: Try find_library with just the name
lib_path = ctypes.util.find_library('fluidsynth')
print(f"find_library('fluidsynth'): {lib_path}")

# Method 2: Try the full library name
lib_path2 = ctypes.util.find_library('libfluidsynth')
print(f"find_library('libfluidsynth'): {lib_path2}")

# Method 3: Direct path to where brew installed it
direct_path = "/opt/homebrew/Cellar/fluid-synth/2.5.1/lib/libfluidsynth.dylib"
print(f"File exists at direct path: {os.path.exists(direct_path)}")

# Method 4: Try loading directly
try:
    handle = cdll.LoadLibrary(direct_path)
    print(f"✓ Successfully loaded from: {direct_path}")
    print(f"Handle: {handle}")
except Exception as e:
    print(f"✗ Failed to load: {e}")

# Method 5: Check if it's in the library path
brew_lib = "/opt/homebrew/lib/libfluidsynth.dylib"
print(f"Symlink in brew lib exists: {os.path.exists(brew_lib)}")
if os.path.exists(brew_lib):
    try:
        handle2 = cdll.LoadLibrary(brew_lib)
        print(f"✓ Successfully loaded from brew lib: {brew_lib}")
    except Exception as e:
        print(f"✗ Failed: {e}")
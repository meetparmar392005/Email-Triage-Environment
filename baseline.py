"""
Compatibility shim.

The submission-required baseline script is `inference.py`.
This file delegates execution to keep older commands working.
"""

from inference import main


if __name__ == "__main__":
    main()

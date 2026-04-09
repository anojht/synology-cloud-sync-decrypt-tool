# -*- coding: utf-8 -*-
"""py2app entry-point shim. The real GUI lives in ``syndecrypt.gui``."""
from syndecrypt.gui import main

if __name__ == "__main__":
    main()

# Third-party inventory

The selected source modules had no third-party attribution headers or vendored code identified during review. They were supplied as the maintainer's MATRIX application; this is an inventory, not a legal opinion.

| Component | Use | License / status |
|---|---|---|
| Python standard library | Runtime: pathlib, SQLite wrapper, JSON, Tkinter and helpers | Python Software Foundation license; Python is separately installed |
| SQLite | Local database through Python | Public domain; supplied with Python, not vendored |
| Tcl/Tk | Optional desktop UI through Tkinter | Tcl/Tk license; supplied with compatible Python installations, not vendored |
| setuptools | Build tooling only | MIT; separately installed, not vendored |
| GitHub official checkout/setup-python/upload-artifact actions | CI only | Separate upstream projects; not distributed runtime code |

No cloud SDKs, provider assets, model weights, logos, PDF files or commercial images are shipped. New dependencies require a license and security review.
Sources: https://docs.python.org/3/license.html · https://sqlite.org/copyright.html · https://www.tcl-lang.org/software/tcltk/license.html · https://github.com/pypa/setuptools/blob/main/LICENSE

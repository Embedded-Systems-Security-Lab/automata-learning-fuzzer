## Installing Netzob
* Phython 3
* libpcap for pcapy: `sudo apt-get install libpcap-dev libpq-dev`
* Manual install of Netzob from the ["fix-layer-build" branch](git@github.com:skleber/netzob.git)
  -- ~~currently NOT the official~~ [~~"next" branch~~](https://github.com/netzob/netzob/tree/next/netzob)! --
  (the current Netzob version available in the official repository and via PyPI lacks some required fixes):
    * clone Netzob next branch to a local folder: `git clone --single-branch -b next https://github.com/netzob/netzob.git`
    * Inside a virtual environment ( eg `python3 -m venv env_name`)
    * `pip install pylstar`
    * `pip install numpy`
    * `python setup.py install`

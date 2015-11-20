SFTP Beamer
===========

SFTP Beamer is an open source Web server for transferring ("beaming") over files between
two SFTP servers, some times referred to as "Managed File Transfer" or "MFT".

SFTP Beamer is built on [Python](https://www.python.org/) 3,
[Django](https://www.djangoproject.com/) 1.8.3, [JQuery](https://jquery.com/),
[Bootstrap](http://getbootstrap.com/), and a bunch of other libraries.

Screenshot
----------
![Screenshot of the SFTP beamer dashboard, logged in to two servers](http://i.imgur.com/7TJdZwa.png)

A Screenshot of the SFTP beamer dashboard, logged in to two servers.

Getting started
---------------

Requirements:

- Python 3 (3.4.3 recommended)
- The following versions of python libraries:
```
Django==1.8.3
django-extensions==1.5.5
django-omnibus==0.2.0
ecdsa==0.13
paramiko==1.15.2
pycrypto==2.6.1
pyzmq==14.1.1
six==1.9.0
sockjs-tornado==1.0.1
tornado==3.1.1
uWSGI==2.0.11.1
```

If you use the Python Package Index installer (`pip`), you can install these
requirements via the supplised `requirements.txt` file, like so:

```bash
pip install -r requirements.txt
```

Clone the repository:

```bash
git clone https://github.com/neicnordic/sftpbeamer.git
cd sftpbeamer
```

Create the settings file:
```bash
cp sftp_beamer/webserver/settings.py{.template,}
```
(Then edit the file manually to your liking!)

Optional: Create the hostinfo file:
```bash
cp sftp_beamer/sftp_beamer/static/js/hostinfo.json{.template,}
```
(Again, edit the file manually to your liking!)

Start the background process:
```
python sftp_beamer/sftp_beamer/backend_process.py
```

Start the (front-end) web server:
```
python sftp_beamer/manage.py runserver
```

Navigate to the SFTP Beamer dashboard:
- http://localhost:8000/sftp_beamer/dashboard

Copyright
-------
[Nordic e-Infrastructures Collaboration (NeIC)](http://neic.nordforsk.org)

License
-------
MIT (see the [LICENSE file](https://github.com/neicnordic/sftpbeamer/blob/master/LICENSE) for more info)

Contributors
------------
- [Xiaxi Li](http://github.com/xiaxi-li)
- [Johan Viklund](http://github.com/viklund)
- [Samuel Lampa](http://github.com/samuell)

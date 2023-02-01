# How to install a new qwc2 service

- Clone the service repository.
- Give the folder permisions `chmod 777 <service-folder>`
- Install the pip requirements to the virtual environment:
```bash
source /qwc-services/.venv/bin/activate
pip install -r requirements.txt
```
- Configure it in the `config-in/default/tenantConfig.json` file.
- Use the config-generator service: `/qwc-services/qwc-config-generator/generate_all.sh`
- Add the `<service-name>.ini` file to the new service:
```ini
[uwsgi]
uid = www-data
socket = <socket-name>.socket
chmod-socket = 660
chdir = <dir-of-the-service>
mount = /<nginx-mountpoint>=server:app
manage-script-name = true
master = true
```
- Add the `run.sh` file to the new service:
```bash
#!/bin/bash
source /qwc-services/.venv/bin/activate
CONFIG_PATH=/qwc-services/auto-config/ JWT_SECRET_KEY=<secret-key> uwsgi <ini-file-path>
```
- Add the service to nginx modifying the `/etc/nginx/sites-enabled/qwc2.bgeo.es.conf` file adding:
```
location /<service-mountpoint> {
    uwsgi_pass unix:<service-socket-path>;
    include uwsgi_params;
}
```
- Restart the nginx service `systemctl restart nginx`.
- Add the .service file to autostart the service:
```ini
[Unit]
Description=<service-description>
After=syslog.target

[Service]
User=www-data
Group=www-data
ExecStart=<path-to-the-service>/run.sh
RuntimeDirectory=uwsgi
Restart=always
KillSignal=SIGQUIT
Type=notify
StandardError=syslog
NotifyAccess=all


[Install]
WantedBy=multi-user.target
```
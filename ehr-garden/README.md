EHR Garden
------

| EHR Server | Source | Username/Password | Port | Notes |
| ---------  | ------ | ----------------- | ---- | ------ |
| GNU Health | [GNU Health Dockerized setup](https://github.com/paramburu/gnuhealth) | admin/ehrgarden | 8000 | |
| OpenEMR| [OpenEMR Production Setup](https://github.com/openemr/openemr/blob/master/docker/production/docker-compose.yml) | admin/pass | 443 | Only works on the HTTPS port, takes a while to load the first time, you might also need to run `docker compose down -v` to erase volumes. |
| VistA | [Dockerized FHIR on VistA](https://github.com/WorldVistA/FHIR-on-VistA) | None | None | There are no exposed ports but you can interact with the fhir api by making http requests into the fhir-api container using the vista-requests container |

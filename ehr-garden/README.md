EHR Garden
------

| EHR Server | Source | Username/Password | Port | Notes |
| ---------  | ------ | ----------------- | ---- | ------ |
| GNU Health | [GNU Health Dockerized setup](https://github.com/paramburu/gnuhealth) | admin/ehrgarden | 8000 | Cannot export FHIR as of now |
| OpenEMR| [OpenEMR Production Setup](https://github.com/openemr/openemr/blob/master/docker/production/docker-compose.yml) | admin/pass | 8001/8443 | Takes a while to load the first time, you might also need to run `docker compose down -v` to erase volumes. |
| VistA | [Dockerized FHIR on VistA](https://github.com/WorldVistA/FHIR-on-VistA) | None | 8002 | None |
| OpenMRS| [OpenMRS Core Repository](https://github.com/openmrs/openmrs-core) | None | 8003 | None | 

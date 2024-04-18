EHR Garden
------

| EHR Server | Source | Username/Password | Port | FHIR Path | Notes |
| ---------  | ------ | ----------------- | ---- | ------ |
| GNU Health | [GNU Health Dockerized setup](https://github.com/paramburu/gnuhealth) | admin/ehrgarden | 8000 | N/A | Cannot export FHIR as of now |
| OpenEMR| [OpenEMR Production Setup](https://github.com/openemr/openemr/blob/master/docker/production/docker-compose.yml) | admin/pass | 8001/8443 | `/apis/default/fhir/Patient` | Takes a while to load the first time, you might also need to run `docker compose down -v` to erase volumes. |
| VistA | [Dockerized FHIR on VistA](https://github.com/WorldVistA/FHIR-on-VistA) | None | 8002 | `/api/Patient` | None |
| OpenMRS| [OpenMRS Core Repository](https://github.com/openmrs/openmrs-core) | None | 8003 | | None |
| HAPI FHIR | [HAPI FHIR](https://hapifhir.io/) | None | 8004 | `/baseR4/Patient` | None |
| IBM FHIR | [Linux For Health FHIR](https://github.com/LinuxForHealth/FHIR) | fhiruser/change-password | 8005 | `/fhir-server/api/v4/Patient` | Needs HTTPS. Requires a username and password in the FHIR requests. When using curl, use -u. |

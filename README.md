EHR-FIST: Digital Format Rehabilitation to Improve Interoperability of EHR Systems and Records
============

We have currently built and hosted the following services in this Docker Compose Project.
- OpenEMR
- GNU Health
- OSEHRA VistA
- OpenMRS
- HAPI FHIR
- LinuxForHealth FHIR (by IBM)

Running
-----

- `git submodule update --init --recursive`
- `cd ehr-garden && docker compose up` should get the containers built and spinning.

Components
-----

- `tools`: contains clients for the FHIR APIs and tools to chain requests and responses across them
- `ehr-garden`: docker setup to create instances of various EHRs and FHIR servers

Web UIs
-----

The Web UIs live in various containers and can be accessed using the port mappings specified in the docker-compose.yml file.

| EHR Server | Source | Username/Password | Port | FHIR Path | Notes |
| ---------  | ------ | ----------------- | ---- | ------ | ----|
| GNU Health | [GNU Health Dockerized setup](https://github.com/paramburu/gnuhealth) | admin/ehrgarden | 8000 | N/A | Cannot export FHIR as of now |
| OpenEMR| [OpenEMR Production Setup](https://github.com/openemr/openemr/blob/master/docker/production/docker-compose.yml) | admin/pass | 8001/8443 | `/apis/default/fhir/Patient` | Takes a while to load the first time, you might also need to run `docker compose down -v` to erase volumes. |
| VistA | [Dockerized FHIR on VistA](https://github.com/WorldVistA/FHIR-on-VistA) | None | 8002 | `/api/Patient` | None |
| OpenMRS| [OpenMRS Core Repository](https://github.com/openmrs/openmrs-core) | None | 8003 | | None |
| HAPI FHIR | [HAPI FHIR](https://hapifhir.io/) | None | 8004 | `/fhir/Patient` | None |
| IBM FHIR | [Linux For Health FHIR](https://github.com/LinuxForHealth/FHIR) | fhiruser/change-password | 8005 | `/fhir-server/api/v4/Patient` | Needs HTTPS. Requires a username and password in the FHIR requests. When using curl, use -u. |

License
-----

This project is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.



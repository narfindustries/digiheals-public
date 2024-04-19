import os
import sys

import requests as r

form_user_id = "authUser"
form_password = "clearPass"
user = "admin"
password = "pass"

base_url = "https://localhost"
auth_url = "https://localhost/interface/main/main_screen.php?auth=login&site=default"
new_session = "new_login_session_management"
enc = "https://localhost/interface/modules/zend_modules/public/carecoordination/upload?id=1"

path = None


def main():
    session = r.Session()
    # Login request
    # verify is set to False since we don't have a https certificate
    req = session.post(
        url=auth_url,
        data={form_user_id: user, form_password: password, new_session: "1"},
        verify=False,
        allow_redirects=True,
    )

    if len(sys.argv) == 2:
        if os.path.exists(sys.argv[1]) and os.path.isdir(sys.argv[1]):
            path = sys.argv[1]
    else:
        path = "../../sample_data"

    statuses = upload_ccda_docs(session, path)
    print(statuses)
    create_patients_after_upload(session)


def upload_ccda_docs(session, path):
    # /interface/modules/zend_modules/public/carecoordination/upload
    # Content-Disposition: form-data; name="file"; filename="Bertram873_Hintz995_401251f1-324d-21eb-9b4c-6a1b95ead191.xml"
    upload_url = (
        base_url + "/interface/modules/zend_modules/public/carecoordination/upload"
    )
    fcount = 0
    statuses = {}
    for file in os.listdir(path):
        # TODO: check for CCDA XML files, and upload them via post requests.
        print(os.path.splitext(file))
        if os.path.splitext(file)[-1].lower() == ".xml":
            fcount += 1
            with open(path + file) as file_to_upload:
                try:
                    req = session.post(url=base_url, files=file_to_upload)
                except r.HTTPError as e:
                    print(e)
                    statuses[file] = req.status_code
    if fcount == 0:
        print("Could not locate CCDA/XML files in the specified directory: " + path)
    return statuses


def create_patients_after_upload(session):
    # CCDA iFrame request
    nreq = session.get(url=enc, verify=False, allow_redirects=True)
    word = ""
    docs = []
    url_search_string = (
        "/interface/modules/zend_modules/public/documents/documents/retrieve/"
    )

    # The request comes in as a series of bytes. We make words out of the byte series and check for our string.
    for line in nreq.content.decode():
        # print(line)
        if url_search_string in word:
            if word[-1] == ">":
                t = word.split("/")[-1]
                t = t.split('"')[0]
                docs.append(t)
        if line != " ":
            word += line
        else:
            word = ""

    if len(docs) > 0:
        for item in docs:
            new_patient_creation_url = base_url + url_search_string + item
            try:
                ccda_req = session.get(
                    url=new_patient_creation_url, verify=False, allow_redirects=True
                )
            except r.HTTPError as e:
                print(e)
    else:
        raise Exception(
            "Could not locate any indexes to create. Verify CCDA documents have been uploaded."
        )


if __name__ == "__main__":
    main()

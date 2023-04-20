import pandas as pd
import argparse
import yaml
from pathlib import Path
import re
import logging

logger = logging.getLogger()
expected_status_code = [200, 201, 404]

# Load active config
def load_upptimerc(path):
    with open(path) as file_handle:
        return yaml.load(file_handle, Loader=yaml.SafeLoader)


def save_upptimerc(config, path):
    with open(path, "w") as file_handle:
        yaml.dump(config, file_handle, default_flow_style=False)


def get_erddap_datasets_upptime_checks(erddap_server, realtime_buffer="1day"):
    """
    Generates the sites block in .upptimerc.yml :
    https://github.com/HakaiInstitute/hakai-datasets-upptime/blob/master/.upptimerc.yml
    """

    def _get_realtime_dataset_test_query(dataset_url):
        return f"{dataset_url}.htmlTable?time&time<=now-1week&distinct()"

    # Retrieve list of datasets
    url = f'{erddap_server}/tabledap/allDatasets.csv?&datasetID!="allDatasets"&accessible="public"'
    logger.info("Get datasetID list from %s",url)
    sites = pd.read_csv(url, skiprows=[1])
    site_checks = []
    for _, row in sites.dropna(subset=["tabledap"]).iterrows():
        # regular check that looks at all variables
        site_checks += [
            dict(
                name=row["tabledap"],
                url=f'{row["tabledap"]}.htmlTable?&time>now-1minute',
                expectedStatusCodes=[200, 201, 404],
            )
        ]

        # realtime check if data exist within given time buffer
        if re.search(r"real[-\s]*time", row["title"], re.IGNORECASE):
            site_checks += [
                dict(
                    name=f"Real-Time: {row['tabledap']}",
                    url=f"{row['tabledap']}.htmlTable?time&time>=now-{realtime_buffer}",
                    expectedStatusCodes=[200],
                )
            ]
            
    return site_checks


def update_upptimerc(config_path, erddap_server="", realtime_buffer="1day"):

    config = load_upptimerc(config_path)

    site_check_names = [site["name"] for site in config["sites"]]

    # Retrieve list of erddap tests
    new_site_checks = [
        site
        for server in erddap_server.split(",")
        for site in get_erddap_datasets_upptime_checks(
            server, realtime_buffer=realtime_buffer
        )
        if site["name"] not in site_check_names
    ]

    if not new_site_checks:
        return

    print(f"{len(new_site_checks)} new test sites added")
    config["sites"] += new_site_checks
    save_upptimerc(config, config_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="generate-erddap-datasets-checks",
        description="Generate upptime yaml entries specific to an erddap server datset",
    )
    parser.add_argument(
        "erddap_servers", help="comma separated list of erddap servers url"
    )
    parser.add_argument(
        "--upptimerc_file",
        help="upptimeerc.yml file to load and update",
        default=".upptimerc.yml",
    )
    parser.add_argument(
        "--realtime_buffer",
        help="Acceptable buffer time to test realtime datasets",
        default="1day",
    )
    args = parser.parse_args()
    update_upptimerc(args.upptimerc_file, args.erddap_servers, args.realtime_buffer)

import os
import sys
from datetime import datetime, UTC
from typing import Generator, TYPE_CHECKING
from uuid import uuid4

import requests
from cloudflare import Cloudflare, NOT_GIVEN
from cloudflare.types.dns import RecordResponse
from cloudflare.types.zones import Zone
from loguru import logger

from environment_config import get_env_config

if TYPE_CHECKING:
    from loguru import Record

_DNS_RECORD_UPDATE_COMMENT = "Automatically updated by cloudflare-dns-update @ {iso_dt}."


def get_public_ipv4_address() -> str:
    old_has_ipv6 = requests.packages.urllib3.util.connection.HAS_IPV6

    requests.packages.urllib3.util.connection.HAS_IPV6 = False
    resp = requests.get("https://checkip.amazonaws.com")
    requests.packages.urllib3.util.connection.HAS_IPV6 = old_has_ipv6

    return resp.text.strip()


def a_dns_record_generator(cf_client: Cloudflare, zone_name: str) -> Generator[tuple[Zone, RecordResponse], None, None]:
    zones = cf_client.zones.list()
    zone = next((z for z in zones if z.name == zone_name), None)

    if not zone:
        return

    resp = cf_client.dns.records.list(zone_id=zone.id, page=1, per_page=100, type="A")
    while True:
        yield from [(zone, dr) for dr in (resp.result or [])]

        if len(resp.result) < resp.result_info.per_page:
            break

        resp = cf_client.dns.records.list(
            zone_id=zone.id, page=resp.result_info.page + 1, per_page=resp.result_info.per_page, type="A"
        )


def main():
    env_config = get_env_config()
    ipv4_address = get_public_ipv4_address()
    client = Cloudflare(api_token=env_config.api_token.get_secret_value())

    logger.info("Checking if there are DNS records with outdated IPv4 addresses in zone '{}'.", env_config.zone_name)

    updated_record_names: list[str] = []
    for zone, dns_record in a_dns_record_generator(cf_client=client, zone_name=env_config.zone_name):
        if dns_record.content == ipv4_address:
            logger.debug("DNS record {} is up to date.", dns_record.name)
            continue

        iso_dt = datetime.now(tz=UTC).isoformat()
        client.dns.records.update(
            dns_record_id=dns_record.id,
            zone_id=zone.id,
            comment=_DNS_RECORD_UPDATE_COMMENT.format(iso_dt=iso_dt),
            content=ipv4_address,
            name=dns_record.name,
            proxied=getattr(dns_record, "proxied", None) or NOT_GIVEN,
            settings=getattr(dns_record, "settings", None) or NOT_GIVEN,
            tags=getattr(dns_record, "tags", None) or NOT_GIVEN,
            ttl=getattr(dns_record, "ttl", None) or NOT_GIVEN,
            type=getattr(dns_record, "type", None) or NOT_GIVEN,
            priority=getattr(dns_record, "priority", None) or NOT_GIVEN,
        )

        updated_record_names.append(dns_record.name)

    logger.info("Updated {} DNS records ({}).", len(updated_record_names), ", ".join(updated_record_names))


def _configure_loguru() -> None:
    def _custom_format(record: "Record"):
        record["extra"] |= {"relpath": f"{record['name'].replace('.', os.sep)}.py"}
        return "[{time}][LEVEL={level}][FILE={extra[relpath]}:{line}][TRACE={extra[trace_id]}] {message}\n{exception}"

    logger.configure(extra={"trace_id": None})
    logger.remove()
    logger.add(sink=sys.stdout, level="INFO", format=_custom_format)


if __name__ == "__main__":
    _configure_loguru()

    uuid = str(uuid4())
    trace_id = uuid.rsplit("-", maxsplit=1)[-1]
    with logger.contextualize(trace_id=trace_id):
        main()

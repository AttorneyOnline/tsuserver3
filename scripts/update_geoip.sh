#!/bin/sh
LICENSE_KEY = YOUR_LICENSE_KEY

wget -O geoipasn.tar.gz "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key=$LICENSE_KEY&suffix=tar.gz"

tar -xvz --wildcards -f geoipasn.tar.gz --strip-components 1 --overwrite "GeoLite2-AS*/*.mmdb"
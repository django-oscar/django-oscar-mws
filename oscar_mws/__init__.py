__version__ = '0.1.0'

MWS_REGION_US = 'US'
MWS_REGION_CA = 'CA'
MWS_REGION_EU = 'EU'
MWS_REGION_IN = 'IN'
MWS_REGION_JP = 'JP'
MWS_REGION_CN = 'CN'

MWS_ENDPOINT_CA = 'mws.amazonservices.ca'
MWS_ENDPOINT_US = 'mws.amazonservices.com'
MWS_ENDPOINT_EU = 'mws-eu.amazonservices.com'
MWS_ENDPOINT_IN = 'mws.amazonservices.in'
MWS_ENDPOINT_JP = 'mws.amazonservices.jp'
MWS_ENDPOINT_CN = 'mws.amazonservices.com.cn'

MWS_MARKETPLACE_US = "US"
MWS_MARKETPLACE_CA = "CA"
MWS_MARKETPLACE_DE = "DE"
MWS_MARKETPLACE_ES = "ES"
MWS_MARKETPLACE_FR = "FR"
MWS_MARKETPLACE_IN = "IN"
MWS_MARKETPLACE_IT = "IT"
MWS_MARKETPLACE_GB = "GB"
MWS_MARKETPLACE_JP = "JP"
MWS_MARKETPLACE_CN = "CN"

MWS_FULFILLMENT_NA = 'AMAZON_NA'
MWS_FULFILLMENT_EU = 'AMAZON_EU'
MWS_FULFILLMENT_JP = 'AMAZON_JP'
MWS_FULFILLMENT_CN = 'AMAZON_CN'
MWS_FULFILLMENT_IN = 'AMAZON_IN'


MWS_MARKETPLACE_ENDPOINTS = {
    MWS_MARKETPLACE_US: MWS_ENDPOINT_US,
    MWS_MARKETPLACE_CA: MWS_ENDPOINT_CA,
    MWS_MARKETPLACE_DE: MWS_ENDPOINT_EU,
    MWS_MARKETPLACE_ES: MWS_ENDPOINT_EU,
    MWS_MARKETPLACE_FR: MWS_ENDPOINT_EU,
    MWS_MARKETPLACE_IN: MWS_ENDPOINT_IN,
    MWS_MARKETPLACE_IT: MWS_ENDPOINT_EU,
    MWS_MARKETPLACE_GB: MWS_ENDPOINT_EU,
    MWS_MARKETPLACE_JP: MWS_ENDPOINT_JP,
    MWS_MARKETPLACE_CN: MWS_ENDPOINT_CN,
}

MWS_FULFILLMENT_CENTERS = {
    MWS_MARKETPLACE_US: MWS_FULFILLMENT_NA,
    MWS_MARKETPLACE_CA: MWS_FULFILLMENT_NA,
    MWS_MARKETPLACE_DE: MWS_FULFILLMENT_EU,
    MWS_MARKETPLACE_ES: MWS_FULFILLMENT_EU,
    MWS_MARKETPLACE_FR: MWS_FULFILLMENT_EU,
    MWS_MARKETPLACE_IN: MWS_FULFILLMENT_IN,
    MWS_MARKETPLACE_IT: MWS_FULFILLMENT_EU,
    MWS_MARKETPLACE_GB: MWS_FULFILLMENT_EU,
    MWS_MARKETPLACE_JP: MWS_FULFILLMENT_JP,
    MWS_MARKETPLACE_CN: MWS_FULFILLMENT_CN,
}

MWS_REGION_ENDPOINTS = {
    MWS_REGION_CA: MWS_ENDPOINT_CA,
    MWS_REGION_US: MWS_ENDPOINT_US,
    MWS_REGION_EU: MWS_ENDPOINT_EU,
    MWS_REGION_IN: MWS_ENDPOINT_IN,
    MWS_REGION_JP: MWS_ENDPOINT_JP,
    MWS_REGION_CN: MWS_ENDPOINT_CN,
}

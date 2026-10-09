"""Public classification vocabularies used as routing indexes (governed data).

ISIC Rev.4 sections (UN), CPV 2008 divisions (EU, Regulation (EC) No 213/2008) and
NAICS 2022 sectors (US) — titles abbreviated. They normalize and route; they are never
an organization's economic reality, and a code is never evidence of fit.
"""

from __future__ import annotations

VOCABULARY_VERSION = "routing-vocabularies.v1"

ISIC_SECTIONS: dict[str, str] = {
    "A": "Agriculture, forestry and fishing",
    "B": "Mining and quarrying",
    "C": "Manufacturing",
    "D": "Electricity, gas, steam and air conditioning supply",
    "E": "Water supply, sewerage, waste management and remediation",
    "F": "Construction",
    "G": "Wholesale and retail trade; repair of motor vehicles",
    "H": "Transportation and storage",
    "I": "Accommodation and food service activities",
    "J": "Information and communication",
    "K": "Financial and insurance activities",
    "L": "Real estate activities",
    "M": "Professional, scientific and technical activities",
    "N": "Administrative and support service activities",
    "O": "Public administration and defence",
    "P": "Education",
    "Q": "Human health and social work activities",
    "R": "Arts, entertainment and recreation",
    "S": "Other service activities",
    "T": "Activities of households as employers",
    "U": "Activities of extraterritorial organizations",
}

CPV_DIVISIONS: dict[str, str] = {
    "03": "Agricultural, farming, fishing, forestry and related products",
    "09": "Petroleum products, fuel, electricity and other sources of energy",
    "14": "Mining, basic metals and related products",
    "15": "Food, beverages, tobacco and related products",
    "16": "Agricultural machinery",
    "18": "Clothing, footwear, luggage articles and accessories",
    "19": "Leather and textile fabrics, plastic and rubber materials",
    "22": "Printed matter and related products",
    "24": "Chemical products",
    "30": "Office and computing machinery, equipment and supplies",
    "31": "Electrical machinery, apparatus, equipment and consumables; lighting",
    "32": "Radio, television, communication and telecommunication equipment",
    "33": "Medical equipment, pharmaceuticals and personal care products",
    "34": "Transport equipment and auxiliary products to transportation",
    "35": "Security, fire-fighting, police and defence equipment",
    "37": "Musical instruments, sport goods, games, toys, handicraft and art materials",
    "38": "Laboratory, optical and precision equipment",
    "39": "Furniture, furnishings, domestic appliances and cleaning products",
    "41": "Collected and purified water",
    "42": "Industrial machinery",
    "43": "Machinery for mining, quarrying and construction",
    "44": "Construction structures and materials",
    "45": "Construction work",
    "48": "Software packages and information systems",
    "50": "Repair and maintenance services",
    "51": "Installation services (except software)",
    "55": "Hotel, restaurant and retail trade services",
    "60": "Transport services (excluding waste transport)",
    "63": "Supporting and auxiliary transport services; travel agencies",
    "64": "Postal and telecommunications services",
    "65": "Public utilities",
    "66": "Financial and insurance services",
    "70": "Real estate services",
    "71": "Architectural, construction, engineering and inspection services",
    "72": "IT services: consulting, software development, Internet and support",
    "73": "Research and development services and related consultancy",
    "75": "Administration, defence and social security services",
    "76": "Services related to the oil and gas industry",
    "77": "Agricultural, forestry, horticultural, aquacultural and apicultural services",
    "79": "Business services: law, marketing, consulting, recruitment, printing, security",
    "80": "Education and training services",
    "85": "Health and social work services",
    "90": "Sewage, refuse, cleaning and environmental services",
    "92": "Recreational, cultural and sporting services",
    "98": "Other community, social and personal services",
}

NAICS_SECTORS: dict[str, str] = {
    "11": "Agriculture, forestry, fishing and hunting",
    "21": "Mining, quarrying, and oil and gas extraction",
    "22": "Utilities",
    "23": "Construction",
    "31-33": "Manufacturing",
    "42": "Wholesale trade",
    "44-45": "Retail trade",
    "48-49": "Transportation and warehousing",
    "51": "Information",
    "52": "Finance and insurance",
    "53": "Real estate and rental and leasing",
    "54": "Professional, scientific, and technical services",
    "55": "Management of companies and enterprises",
    "56": "Administrative and support and waste management services",
    "61": "Educational services",
    "62": "Health care and social assistance",
    "71": "Arts, entertainment, and recreation",
    "72": "Accommodation and food services",
    "81": "Other services (except public administration)",
    "92": "Public administration",
}


def naics_prefixes(sector: str) -> tuple[str, ...]:
    """``"31-33"`` → ``("31", "32", "33")``; a plain sector is itself."""
    if "-" not in sector:
        return (sector,)
    low, high = (int(part) for part in sector.split("-"))
    return tuple(str(code) for code in range(low, high + 1))


#: Default routing per ISIC section where one CPV division / NAICS sector is the clear
#: buyer-side classification of the same services. Sections with many divisions (e.g.
#: manufacturing, trade) route only through an explicit judgment or the lexicon.
SECTION_ROUTING: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "D": (("65",), ("22",)),
    "E": (("90",), ("56",)),
    "F": (("45",), ("23",)),
    "H": (("60",), ("48-49",)),
    "I": (("55",), ("72",)),
    "J": (("72",), ("51",)),
    "K": (("66",), ("52",)),
    "L": (("70",), ("53",)),
    "M": (("71", "79"), ("54",)),
    "N": (("79",), ("56",)),
    "P": (("80",), ("61",)),
    "Q": (("85",), ("62",)),
    "R": (("92",), ("71",)),
    "S": (("98",), ("81",)),
}

#: schema.org types a site declares about itself → ISIC section (exact type names).
SCHEMA_TYPE_SECTIONS: dict[str, str] = {
    **dict.fromkeys(
        ["Electrician", "Plumber", "HVACBusiness", "RoofingContractor", "GeneralContractor",
         "HousePainter", "HomeAndConstructionBusiness"],
        "F",
    ),
    **dict.fromkeys(
        ["AutoRepair", "AutoDealer", "AutomotiveBusiness", "Store", "OnlineStore",
         "ClothingStore", "ElectronicsStore", "FurnitureStore", "GroceryStore",
         "HardwareStore", "BookStore", "ShoeStore", "SportingGoodsStore", "JewelryStore",
         "ConvenienceStore", "DepartmentStore", "GardenStore", "PetStore", "ToyStore"],
        "G",
    ),
    **dict.fromkeys(["MovingCompany"], "H"),
    **dict.fromkeys(
        ["Restaurant", "FoodEstablishment", "CafeOrCoffeeShop", "Bakery", "BarOrPub",
         "FastFoodRestaurant", "IceCreamShop", "Winery", "Brewery", "LodgingBusiness",
         "Hotel", "Hostel", "BedAndBreakfast", "Motel", "Resort", "Campground"],
        "I",
    ),
    **dict.fromkeys(
        ["SoftwareApplication", "WebApplication", "MobileApplication", "NewsMediaOrganization",
         "InternetCafe", "TelevisionStation", "RadioStation"],
        "J",
    ),
    **dict.fromkeys(
        ["FinancialService", "BankOrCreditUnion", "InsuranceAgency"],
        "K",
    ),
    **dict.fromkeys(["RealEstateAgent"], "L"),
    **dict.fromkeys(
        ["LegalService", "Attorney", "Notary", "AccountingService", "ProfessionalService",
         "ResearchOrganization"],
        "M",
    ),
    **dict.fromkeys(["TravelAgency", "EmploymentAgency"], "N"),
    **dict.fromkeys(["GovernmentOrganization", "GovernmentOffice"], "O"),
    **dict.fromkeys(
        ["EducationalOrganization", "School", "CollegeOrUniversity", "ElementarySchool",
         "HighSchool", "MiddleSchool", "Preschool", "Course"],
        "P",
    ),
    **dict.fromkeys(
        ["MedicalOrganization", "MedicalClinic", "Hospital", "Dentist", "Physician",
         "Optician", "DiagnosticLab", "MedicalBusiness"],
        "Q",
    ),
    **dict.fromkeys(
        ["SportsActivityLocation", "ExerciseGym", "EntertainmentBusiness", "MovieTheater",
         "SportsClub", "Museum", "PerformingGroup"],
        "R",
    ),
    **dict.fromkeys(
        ["HealthAndBeautyBusiness", "BeautySalon", "HairSalon", "DaySpa",
         "DryCleaningOrLaundry", "TattooParlor"],
        "S",
    ),
}  # fmt: skip

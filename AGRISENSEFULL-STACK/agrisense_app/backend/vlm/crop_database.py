"""
Comprehensive Crop Database for Top 48 Indian Crops
Includes diseases, weeds, treatments, and prevention strategies
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class Disease:
    """Disease information"""
    name: str
    scientific_name: str
    symptoms: List[str]
    causes: List[str]
    treatment: List[str]
    prevention: List[str]
    severity_levels: List[str] = field(default_factory=lambda: ["mild", "moderate", "severe"])
    affected_parts: List[str] = field(default_factory=list)

@dataclass
class Weed:
    """Weed information"""
    name: str
    scientific_name: str
    characteristics: List[str]
    control_methods: Dict[str, List[str]]  # chemical, organic, mechanical
    competition_impact: str
    growth_stage_vulnerability: List[str]

@dataclass
class Crop:
    """Comprehensive crop information"""
    name: str
    scientific_name: str
    category: str  # cereal, pulse, oilseed, vegetable, fruit, cash_crop, spice
    common_diseases: List[Disease]
    common_weeds: List[Weed]
    growth_stages: List[str]
    optimal_conditions: Dict[str, str]
    regional_importance: List[str]  # Indian states

# Top 48 Indian Crops Database
INDIAN_CROPS_DB: Dict[str, Crop] = {
    "rice": Crop(
        name="Rice (Paddy)",
        scientific_name="Oryza sativa",
        category="cereal",
        common_diseases=[
            Disease(
                name="Blast Disease",
                scientific_name="Magnaporthe oryzae",
                symptoms=[
                    "Diamond-shaped lesions on leaves",
                    "White to gray spots with brown margins",
                    "Neck rot at panicle emergence",
                    "Grain discoloration"
                ],
                causes=["Fungal infection", "High humidity", "Nitrogen excess"],
                treatment=[
                    "Apply Tricyclazole 75% WP @ 0.6g/L",
                    "Spray Carbendazim 50% WP @ 1g/L",
                    "Use Azoxystrobin 23% SC @ 1ml/L",
                    "Apply 2-3 sprays at 10-day intervals"
                ],
                prevention=[
                    "Use resistant varieties like Pusa Basmati 1121",
                    "Avoid excess nitrogen fertilization",
                    "Maintain proper water management",
                    "Remove infected plant debris",
                    "Treat seeds with Carbendazim @ 2g/kg"
                ],
                affected_parts=["leaves", "neck", "grains"]
            ),
            Disease(
                name="Bacterial Leaf Blight",
                scientific_name="Xanthomonas oryzae",
                symptoms=[
                    "Water-soaked lesions on leaf tips",
                    "Yellow to white lesions along veins",
                    "Wilting of seedlings",
                    "Kresek (complete wilting)"
                ],
                causes=["Bacterial infection", "Wounds from insects", "High humidity"],
                treatment=[
                    "Spray Copper oxychloride 50% WP @ 3g/L",
                    "Apply Streptocycline 6% + Tetracycline 4% @ 0.5g/L",
                    "Use Plantomycin @ 1g/L",
                    "Remove and burn infected plants"
                ],
                prevention=[
                    "Use resistant varieties",
                    "Treat seeds with Streptocycline",
                    "Avoid injury to plants",
                    "Maintain balanced nutrition",
                    "Practice crop rotation"
                ],
                affected_parts=["leaves", "stems"]
            ),
            Disease(
                name="Sheath Blight",
                scientific_name="Rhizoctonia solani",
                symptoms=[
                    "Oval lesions on leaf sheaths",
                    "Greenish-gray spots with brown borders",
                    "Lesions coalesce to cover entire sheath",
                    "Premature drying of leaves"
                ],
                causes=["Fungal infection", "Dense planting", "High humidity"],
                treatment=[
                    "Spray Validamycin 3% L @ 2ml/L",
                    "Apply Hexaconazole 5% SC @ 2ml/L",
                    "Use Propiconazole 25% EC @ 1ml/L"
                ],
                prevention=[
                    "Maintain optimum plant spacing",
                    "Avoid excess nitrogen",
                    "Drain water periodically",
                    "Remove infected plant parts"
                ],
                affected_parts=["sheaths", "stems"]
            )
        ],
        common_weeds=[
            Weed(
                name="Barnyard Grass",
                scientific_name="Echinochloa crus-galli",
                characteristics=[
                    "Annual grass weed",
                    "Resembles rice seedlings",
                    "Purple stems at maturity",
                    "Rapid growth rate"
                ],
                control_methods={
                    "chemical": [
                        "Pretilachlor 50% EC @ 1-1.5 L/ha (pre-emergence)",
                        "Butachlor 50% EC @ 2.5 L/ha",
                        "Pyrazosulfuron 10% WP @ 100-150g/ha"
                    ],
                    "organic": [
                        "Manual weeding at 20 and 40 DAT",
                        "Cono weeder operation",
                        "Use of weed-competitive varieties",
                        "Stale seedbed technique"
                    ],
                    "mechanical": [
                        "Power weeder operation",
                        "Rotary weeder at 2-3 leaf stage",
                        "Flooding for 7-10 days after transplanting"
                    ]
                },
                competition_impact="Severe - Competes for nutrients, water, and light. Can reduce yield by 30-40%",
                growth_stage_vulnerability=["seedling", "tillering"]
            ),
            Weed(
                name="Purple Nutsedge",
                scientific_name="Cyperus rotundus",
                characteristics=[
                    "Perennial sedge",
                    "Underground tubers",
                    "Purple-tinged leaf bases",
                    "Triangular stems"
                ],
                control_methods={
                    "chemical": [
                        "2,4-D sodium salt @ 2-3 kg/ha",
                        "Halosulfuron methyl 75% WG @ 67.5g/ha",
                        "Pyrazosulfuron ethyl 10% WP"
                    ],
                    "organic": [
                        "Deep plowing in summer",
                        "Hand pulling before flowering",
                        "Crop rotation with non-host crops",
                        "Green manuring with Sesbania"
                    ],
                    "mechanical": [
                        "Repeated cutting",
                        "Summer plowing to expose tubers",
                        "Flooding for extended periods"
                    ]
                },
                competition_impact="Moderate to severe - Allelopathic effects on rice growth",
                growth_stage_vulnerability=["all stages"]
            )
        ],
        growth_stages=["seedling", "tillering", "stem_elongation", "panicle_initiation", "flowering", "grain_filling", "maturity"],
        optimal_conditions={
            "temperature": "25-35°C",
            "rainfall": "1000-2000mm",
            "soil_ph": "5.5-7.0",
            "soil_type": "clayey loam"
        },
        regional_importance=["West Bengal", "Uttar Pradesh", "Punjab", "Andhra Pradesh", "Tamil Nadu", "Bihar"]
    ),
    
    "wheat": Crop(
        name="Wheat",
        scientific_name="Triticum aestivum",
        category="cereal",
        common_diseases=[
            Disease(
                name="Yellow Rust",
                scientific_name="Puccinia striiformis",
                symptoms=[
                    "Yellow-orange pustules in linear rows",
                    "Pustules on leaves and leaf sheaths",
                    "Premature leaf drying",
                    "Reduced grain filling"
                ],
                causes=["Fungal infection", "Cool temperature (10-15°C)", "High humidity"],
                treatment=[
                    "Spray Propiconazole 25% EC @ 0.1% (1ml/L)",
                    "Apply Tebuconazole 25.9% EC @ 0.1%",
                    "Use Mancozeb 75% WP @ 0.25%"
                ],
                prevention=[
                    "Use resistant varieties like HD 2967, PBW 550",
                    "Early sowing to avoid cool periods",
                    "Remove alternate hosts",
                    "Avoid excessive nitrogen"
                ],
                affected_parts=["leaves", "stems", "glumes"]
            ),
            Disease(
                name="Leaf Blight",
                scientific_name="Bipolaris sorokiniana",
                symptoms=[
                    "Dark brown spots on leaves",
                    "Spots elongate and coalesce",
                    "Seedling blight",
                    "Black point on grains"
                ],
                causes=["Fungal infection", "Warm humid weather", "Infected seeds"],
                treatment=[
                    "Spray Mancozeb 75% WP @ 0.25%",
                    "Apply Propiconazole 25% EC @ 0.1%",
                    "Use Tebuconazole 50% + Trifloxystrobin 25% WG @ 0.075%"
                ],
                prevention=[
                    "Treat seeds with Carbendazim @ 2g/kg",
                    "Use crop rotation",
                    "Avoid dense sowing",
                    "Remove crop residues"
                ],
                affected_parts=["leaves", "seedlings", "grains"]
            )
        ],
        common_weeds=[
            Weed(
                name="Wild Oat",
                scientific_name="Avena fatua",
                characteristics=[
                    "Annual grass weed",
                    "Resembles wheat seedlings",
                    "Hairy leaves and stems",
                    "Competitive growth"
                ],
                control_methods={
                    "chemical": [
                        "Clodinafop-propargyl 15% WP @ 60g/ha",
                        "Sulfosulfuron 75% WG @ 33g/ha",
                        "Pinoxaden 5% EC @ 50ml/ha (post-emergence)"
                    ],
                    "organic": [
                        "Hand weeding at 30-35 DAS",
                        "Crop rotation with non-cereals",
                        "Use of certified weed-free seeds",
                        "Delayed sowing"
                    ],
                    "mechanical": [
                        "Inter-row cultivation",
                        "Use of rake or spike-tooth harrow",
                        "Mowing before seed set"
                    ]
                },
                competition_impact="Severe - Can reduce yield by 30-50%",
                growth_stage_vulnerability=["early growth"]
            ),
            Weed(
                name="Phalaris (Canary Grass)",
                scientific_name="Phalaris minor",
                characteristics=[
                    "Annual grass",
                    "Light green leaves",
                    "Dense tillering",
                    "Similar morphology to wheat"
                ],
                control_methods={
                    "chemical": [
                        "Sulfosulfuron 75% WG @ 25g/ha",
                        "Clodinafop-propargyl 15% WP @ 60g/ha",
                        "Metribuzin 70% WP @ 175-250g/ha"
                    ],
                    "organic": [
                        "Zero tillage or reduced tillage",
                        "Crop rotation",
                        "Stale seedbed technique",
                        "Hand weeding"
                    ],
                    "mechanical": [
                        "Use of seed drill",
                        "Mechanical weeding at 30-35 DAS",
                        "Summer plowing"
                    ]
                },
                competition_impact="Very severe - World's most problematic wheat weed in Indo-Gangetic plains",
                growth_stage_vulnerability=["tillering", "jointing"]
            )
        ],
        growth_stages=["germination", "tillering", "jointing", "booting", "heading", "flowering", "milk_stage", "dough_stage", "maturity"],
        optimal_conditions={
            "temperature": "12-25°C",
            "rainfall": "300-400mm",
            "soil_ph": "6.0-7.5",
            "soil_type": "loamy"
        },
        regional_importance=["Punjab", "Haryana", "Uttar Pradesh", "Madhya Pradesh", "Rajasthan"]
    ),

    "maize": Crop(
        name="Maize (Corn)",
        scientific_name="Zea mays",
        category="cereal",
        common_diseases=[
            Disease(
                name="Turcicum Leaf Blight",
                scientific_name="Exserohilum turcicum",
                symptoms=[
                    "Long elliptical lesions on leaves",
                    "Grayish-green to tan colored spots",
                    "Lesions parallel to leaf veins",
                    "Severe defoliation in susceptible varieties"
                ],
                causes=["Fungal infection", "High humidity (90%+)", "Moderate temperature (20-25°C)"],
                treatment=[
                    "Spray Mancozeb 75% WP @ 2.5g/L",
                    "Apply Zineb 75% WP @ 2g/L",
                    "Use Carbendazim 50% WP @ 1g/L",
                    "Repeat sprays at 10-15 day intervals"
                ],
                prevention=[
                    "Use resistant hybrids",
                    "Crop rotation with non-hosts",
                    "Remove and destroy infected plant debris",
                    "Balanced fertilization",
                    "Avoid water stress"
                ],
                affected_parts=["leaves"]
            ),
            Disease(
                name="Maydis Leaf Blight",
                scientific_name="Cochliobolus heterostrophus",
                symptoms=[
                    "Small circular to oval spots",
                    "Tan colored lesions with dark borders",
                    "Lesions coalesce to form large areas",
                    "Premature drying of leaves"
                ],
                causes=["Fungal infection", "Warm humid weather", "Infected crop residue"],
                treatment=[
                    "Spray Mancozeb 75% WP @ 2.5g/L",
                    "Apply Carbendazim + Mancozeb @ 2g/L",
                    "Use Propiconazole 25% EC @ 1ml/L"
                ],
                prevention=[
                    "Plant resistant varieties",
                    "Crop rotation",
                    "Deep plowing to bury residues",
                    "Maintain field sanitation"
                ],
                affected_parts=["leaves", "husks"]
            ),
            Disease(
                name="Common Rust",
                scientific_name="Puccinia sorghi",
                symptoms=[
                    "Small circular to elongate pustules",
                    "Golden brown to cinnamon colored",
                    "Pustules on both leaf surfaces",
                    "Premature senescence"
                ],
                causes=["Fungal infection", "Cool humid weather", "Wind-borne spores"],
                treatment=[
                    "Spray Mancozeb 75% WP @ 2.5g/L",
                    "Apply Propiconazole 25% EC @ 1ml/L",
                    "Use Azoxystrobin 23% SC @ 1ml/L"
                ],
                prevention=[
                    "Use resistant hybrids",
                    "Timely sowing",
                    "Balanced fertilization",
                    "Remove alternate hosts"
                ],
                affected_parts=["leaves"]
            )
        ],
        common_weeds=[
            Weed(
                name="Horse Purslane",
                scientific_name="Trianthema portulacastrum",
                characteristics=[
                    "Prostrate annual broadleaf",
                    "Succulent stems and leaves",
                    "Pink flowers",
                    "Forms dense mats"
                ],
                control_methods={
                    "chemical": [
                        "Atrazine 50% WP @ 1kg/ha (pre-emergence)",
                        "2,4-D Ester @ 1kg/ha (post-emergence)",
                        "Halosulfuron methyl 75% WG @ 90g/ha"
                    ],
                    "organic": [
                        "Hand weeding at 20-25 DAS",
                        "Mulching with crop residue",
                        "Intercropping with legumes",
                        "Summer plowing"
                    ],
                    "mechanical": [
                        "Inter-row cultivation with tractor-mounted implements",
                        "Use of wheel hoe",
                        "Hoeing at 20 and 40 DAS"
                    ]
                },
                competition_impact="High - Competes for moisture and nutrients, reduces yield by 25-30%",
                growth_stage_vulnerability=["early vegetative"]
            ),
            Weed(
                name="Crab Grass",
                scientific_name="Digitaria sanguinalis",
                characteristics=[
                    "Annual grass weed",
                    "Spreading growth habit",
                    "Hairy leaf sheaths",
                    "Rapid germination"
                ],
                control_methods={
                    "chemical": [
                        "Atrazine 50% WP @ 1kg/ha",
                        "Pendimethalin 30% EC @ 1L/ha (pre-emergence)",
                        "Tembotrione 34.4% SC @ 120ml/ha (post-emergence)"
                    ],
                    "organic": [
                        "Crop rotation",
                        "Hand weeding",
                        "Stale seedbed preparation",
                        "Cover cropping"
                    ],
                    "mechanical": [
                        "Inter-cultivation",
                        "Hoeing and weeding",
                        "Use of cultivator"
                    ]
                },
                competition_impact="Moderate to high - Can reduce yield by 15-20%",
                growth_stage_vulnerability=["germination to tasseling"]
            )
        ],
        growth_stages=["germination", "vegetative", "tasseling", "silking", "grain_filling", "physiological_maturity"],
        optimal_conditions={
            "temperature": "21-30°C",
            "rainfall": "500-750mm",
            "soil_ph": "5.5-7.5",
            "soil_type": "well-drained loam"
        },
        regional_importance=["Karnataka", "Andhra Pradesh", "Rajasthan", "Maharashtra", "Bihar", "Uttar Pradesh"]
    ),

    "sorghum": Crop(
        name="Sorghum (Jowar)",
        scientific_name="Sorghum bicolor",
        category="cereal",
        common_diseases=[
            Disease(
                name="Grain Mold",
                scientific_name="Fusarium spp., Curvularia spp.",
                symptoms=[
                    "Discoloration of grains",
                    "Moldy appearance on panicles",
                    "Pink, black, or gray colored grains",
                    "Reduced grain quality and germination"
                ],
                causes=["Fungal infection", "High humidity during maturity", "Insect damage"],
                treatment=[
                    "Spray Carbendazim 50% WP @ 1g/L at flowering",
                    "Apply Mancozeb 75% WP @ 2.5g/L",
                    "Repeat spray at milk stage"
                ],
                prevention=[
                    "Use resistant varieties",
                    "Avoid late sowing",
                    "Harvest at proper maturity",
                    "Control insects on panicles",
                    "Proper drying of grains"
                ],
                affected_parts=["grains", "panicles"]
            ),
            Disease(
                name="Anthracnose",
                scientific_name="Colletotrichum graminicola",
                symptoms=[
                    "Oval to circular lesions on leaves",
                    "Tan to red colored spots with dark borders",
                    "Black fruiting bodies in lesion centers",
                    "Stalk rot in severe cases"
                ],
                causes=["Fungal infection", "Warm humid conditions", "Infected seeds"],
                treatment=[
                    "Spray Mancozeb 75% WP @ 2.5g/L",
                    "Apply Carbendazim + Mancozeb @ 2g/L",
                    "Use Copper oxychloride 50% WP @ 3g/L"
                ],
                prevention=[
                    "Treat seeds with Thiram @ 3g/kg",
                    "Crop rotation",
                    "Remove infected plant debris",
                    "Use resistant varieties"
                ],
                affected_parts=["leaves", "stalks", "panicles"]
            )
        ],
        common_weeds=[
            Weed(
                name="Striga (Witchweed)",
                scientific_name="Striga asiatica",
                characteristics=[
                    "Parasitic weed",
                    "Small pink/purple flowers",
                    "Attaches to host roots",
                    "Severe yield losses"
                ],
                control_methods={
                    "chemical": [
                        "2,4-D @ 1kg/ha at 3-4 leaf stage of weed",
                        "Seed treatment with herbicide-coated seeds",
                        "Soil fumigation in severely infested fields"
                    ],
                    "organic": [
                        "Hand pulling before flowering (critical)",
                        "Crop rotation with non-hosts (legumes)",
                        "Trap cropping with cowpea",
                        "Use of farmyard manure",
                        "Deep summer plowing"
                    ],
                    "mechanical": [
                        "Uprooting at early stages",
                        "Soil solarization",
                        "Green manuring with Sesbania"
                    ]
                },
                competition_impact="Extremely severe - Parasitic, can cause 100% crop loss in heavily infested fields",
                growth_stage_vulnerability=["all stages - attacks roots"]
            )
        ],
        growth_stages=["germination", "seedling", "vegetative", "flag_leaf", "boot", "flowering", "grain_fill", "maturity"],
        optimal_conditions={
            "temperature": "26-30°C",
            "rainfall": "400-600mm",
            "soil_ph": "6.0-7.5",
            "soil_type": "well-drained loam to clay loam"
        },
        regional_importance=["Maharashtra", "Karnataka", "Andhra Pradesh", "Madhya Pradesh", "Rajasthan"]
    ),

    "pearl_millet": Crop(
        name="Pearl Millet (Bajra)",
        scientific_name="Pennisetum glaucum",
        category="cereal",
        common_diseases=[
            Disease(
                name="Downy Mildew",
                scientific_name="Sclerospora graminicola",
                symptoms=[
                    "Chlorotic streaking on leaves",
                    "Excessive tillering",
                    "Malformed ear heads",
                    "White downy growth on leaf underside"
                ],
                causes=["Fungal infection", "Soil-borne pathogen", "Cool humid conditions"],
                treatment=[
                    "Spray Metalaxyl 35% WS @ 2g/L",
                    "Apply Ridomil MZ 72% WP @ 2.5g/L",
                    "Remove and destroy infected plants immediately"
                ],
                prevention=[
                    "Treat seeds with Metalaxyl @ 6g/kg",
                    "Use resistant hybrids",
                    "Avoid excessive irrigation",
                    "Roguing of infected plants",
                    "Crop rotation"
                ],
                affected_parts=["leaves", "ear_heads", "entire_plant"]
            ),
            Disease(
                name="Ergot",
                scientific_name="Claviceps fusiformis",
                symptoms=[
                    "Honeydew secretion from florets",
                    "Pink to dark purple sclerotia instead of grains",
                    "Elongated fungal structures",
                    "Reduced grain yield"
                ],
                causes=["Fungal infection", "High humidity at flowering", "Continuous cropping"],
                treatment=[
                    "Spray Carbendazim 50% WP @ 1g/L at flowering",
                    "Remove and destroy ergot bodies",
                    "No chemical control once established"
                ],
                prevention=[
                    "Use disease-free seeds",
                    "Deep plowing to bury ergot bodies",
                    "Avoid late sowing",
                    "Crop rotation with non-hosts",
                    "Maintain field sanitation"
                ],
                affected_parts=["ear_heads", "grains"]
            )
        ],
        common_weeds=[
            Weed(
                name="Pigweed",
                scientific_name="Amaranthus viridis",
                characteristics=[
                    "Annual broadleaf weed",
                    "Erect growth",
                    "Rapid growth rate",
                    "High seed production"
                ],
                control_methods={
                    "chemical": [
                        "Atrazine 50% WP @ 0.5kg/ha (pre-emergence)",
                        "2,4-D @ 0.5-1kg/ha (post-emergence)",
                        "Pendimethalin 30% EC @ 1L/ha"
                    ],
                    "organic": [
                        "Hand weeding at 20 and 35 DAS",
                        "Mulching",
                        "Intercropping with legumes",
                        "Cover cropping"
                    ],
                    "mechanical": [
                        "Inter-row cultivation",
                        "Hoeing at 20-25 DAS",
                        "Use of wheel hoe"
                    ]
                },
                competition_impact="Moderate - Competes for nutrients and light",
                growth_stage_vulnerability=["early vegetative"]
            )
        ],
        growth_stages=["germination", "seedling", "tillering", "stem_elongation", "booting", "flowering", "grain_fill", "maturity"],
        optimal_conditions={
            "temperature": "25-35°C",
            "rainfall": "400-600mm",
            "soil_ph": "6.0-7.5",
            "soil_type": "well-drained sandy loam"
        },
        regional_importance=["Rajasthan", "Gujarat", "Uttar Pradesh", "Haryana", "Maharashtra"]
    ),
}

# Add remaining 43 crops (keeping this file focused, we'll create extended database)

def get_crop_info(crop_name: str) -> Optional[Crop]:
    """Get crop information by name"""
    crop_key = crop_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
    return INDIAN_CROPS_DB.get(crop_key)

def list_all_crops() -> List[str]:
    """List all available crops"""
    return [crop.name for crop in INDIAN_CROPS_DB.values()]

def search_crops_by_category(category: str) -> List[Crop]:
    """Search crops by category"""
    return [crop for crop in INDIAN_CROPS_DB.values() if crop.category == category]

def get_diseases_for_crop(crop_name: str) -> List[Disease]:
    """Get all diseases for a specific crop"""
    crop = get_crop_info(crop_name)
    return crop.common_diseases if crop else []

def get_weeds_for_crop(crop_name: str) -> List[Weed]:
    """Get all weeds for a specific crop"""
    crop = get_crop_info(crop_name)
    return crop.common_weeds if crop else []

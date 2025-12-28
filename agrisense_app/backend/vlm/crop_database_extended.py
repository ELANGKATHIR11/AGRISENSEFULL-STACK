"""
Extended Crop Database - Remaining 43 Indian Crops
Part of the comprehensive 48-crop VLM system
"""

from .crop_database import Crop, Disease, Weed, INDIAN_CROPS_DB

# Continue adding crops to the main database
INDIAN_CROPS_DB.update({
    "chickpea": Crop(
        name="Chickpea (Chana)",
        scientific_name="Cicer arietinum",
        category="pulse",
        common_diseases=[
            Disease(
                name="Wilt",
                scientific_name="Fusarium oxysporum f.sp. ciceri",
                symptoms=["Drooping of leaves and petioles", "Yellowing of leaves", "Vascular browning", "Wilting of entire plant"],
                causes=["Soil-borne fungal infection", "High soil temperature", "Water stress"],
                treatment=["No chemical treatment effective once disease appears", "Remove infected plants", "Soil solarization"],
                prevention=["Use wilt-resistant varieties", "Seed treatment with Trichoderma @ 4g/kg", "Crop rotation with non-hosts for 3-4 years", "Early sowing"],
                affected_parts=["vascular_tissue", "entire_plant"]
            ),
            Disease(
                name="Ascochyta Blight",
                scientific_name="Ascochyta rabiei",
                symptoms=["Circular gray spots with dark borders on leaves", "Stem cankers", "Pod lesions", "Seedling death"],
                causes=["Fungal infection", "Cool humid weather", "Infected seeds"],
                treatment=["Spray Mancozeb 75% WP @ 2.5g/L", "Apply Carbendazim 50% WP @ 1g/L", "Repeat at 15-day intervals"],
                prevention=["Treat seeds with Carbendazim @ 2g/kg", "Use disease-free seeds", "Avoid overhead irrigation", "Crop rotation"],
                affected_parts=["leaves", "stems", "pods"]
            )
        ],
        common_weeds=[
            Weed(
                name="Chenopodium",
                scientific_name="Chenopodium album",
                characteristics=["Annual broadleaf", "Rapid growth", "Mealy white coating on leaves", "High seed production"],
                control_methods={
                    "chemical": ["Pendimethalin 30% EC @ 1L/ha (pre-emergence)", "Imazethapyr 10% SL @ 1L/ha (post-emergence)"],
                    "organic": ["Hand weeding at 25-30 DAS", "Mulching", "Intercropping"],
                    "mechanical": ["Inter-row cultivation", "Hoeing at 25 and 45 DAS"]
                },
                competition_impact="High - Can reduce yield by 30-40%",
                growth_stage_vulnerability=["vegetative", "flowering"]
            )
        ],
        growth_stages=["germination", "vegetative", "flowering", "pod_formation", "pod_filling", "maturity"],
        optimal_conditions={"temperature": "20-25°C", "rainfall": "350-400mm", "soil_ph": "6.0-7.5", "soil_type": "well-drained loam"},
        regional_importance=["Madhya Pradesh", "Maharashtra", "Rajasthan", "Karnataka", "Andhra Pradesh"]
    ),

    "pigeon_pea": Crop(
        name="Pigeon Pea (Arhar/Tur)",
        scientific_name="Cajanus cajan",
        category="pulse",
        common_diseases=[
            Disease(
                name="Fusarium Wilt",
                scientific_name="Fusarium udum",
                symptoms=["Yellowing of leaves", "Drooping", "Vascular discoloration", "Wilting starting from lower leaves"],
                causes=["Soil-borne fungus", "High temperature", "Water stress"],
                treatment=["No effective chemical treatment", "Remove and burn infected plants"],
                prevention=["Use resistant varieties like Pusa 992", "Seed treatment with Trichoderma @ 4g/kg", "Deep summer plowing", "Crop rotation"],
                affected_parts=["vascular_system", "entire_plant"]
            ),
            Disease(
                name="Sterility Mosaic Disease",
                scientific_name="Pigeon Pea Sterility Mosaic Virus",
                symptoms=["Mosaic patterns on leaves", "Small pale green leaves", "Excessive vegetative growth", "Sterile flowers"],
                causes=["Viral infection", "Transmitted by eriophyid mites", "Infected planting material"],
                treatment=["Spray Dicofol 18.5% EC @ 2.5ml/L to control mites", "Remove infected plants immediately"],
                prevention=["Use disease-free seeds", "Grow resistant varieties", "Control mite vectors", "Early sowing"],
                affected_parts=["leaves", "flowers"]
            )
        ],
        common_weeds=[
            Weed(
                name="Purple Nutsedge",
                scientific_name="Cyperus rotundus",
                characteristics=["Perennial sedge", "Underground tubers", "Triangular stems", "Purple leaf bases"],
                control_methods={
                    "chemical": ["Pendimethalin 30% EC @ 1L/ha", "Imazethapyr 10% SL @ 75ml/ha"],
                    "organic": ["Hand weeding", "Summer plowing", "Crop rotation"],
                    "mechanical": ["Repeated hoeing", "Inter-cultivation"]
                },
                competition_impact="Moderate to severe",
                growth_stage_vulnerability=["all_stages"]
            )
        ],
        growth_stages=["germination", "vegetative", "flowering", "pod_development", "grain_filling", "maturity"],
        optimal_conditions={"temperature": "20-30°C", "rainfall": "600-1000mm", "soil_ph": "6.5-7.5", "soil_type": "deep loamy soil"},
        regional_importance=["Maharashtra", "Karnataka", "Madhya Pradesh", "Uttar Pradesh", "Gujarat"]
    ),

    "green_gram": Crop(
        name="Green Gram (Moong)",
        scientific_name="Vigna radiata",
        category="pulse",
        common_diseases=[
            Disease(
                name="Yellow Mosaic Virus",
                scientific_name="Mungbean Yellow Mosaic Virus",
                symptoms=["Yellow mosaic patterns on leaves", "Stunted growth", "Reduced pod formation", "Leaf curling"],
                causes=["Viral infection", "Whitefly transmission", "High temperature"],
                treatment=["Spray Imidacloprid 17.8% SL @ 0.5ml/L to control whiteflies", "Remove infected plants"],
                prevention=["Use resistant varieties like Pusa Vishal", "Control whitefly population", "Avoid late sowing", "Grow barrier crops"],
                affected_parts=["leaves", "entire_plant"]
            ),
            Disease(
                name="Powdery Mildew",
                scientific_name="Erysiphe polygoni",
                symptoms=["White powdery coating on leaves", "Leaf yellowing", "Premature defoliation", "Reduced pod size"],
                causes=["Fungal infection", "Dry weather with high humidity", "Dense canopy"],
                treatment=["Spray Sulfur 80% WP @ 2.5g/L", "Apply Carbendazim 50% WP @ 1g/L", "Use Azoxystrobin @ 1ml/L"],
                prevention=["Maintain proper spacing", "Avoid excess nitrogen", "Timely sowing", "Use resistant varieties"],
                affected_parts=["leaves", "stems", "pods"]
            )
        ],
        common_weeds=[
            Weed(
                name="Trianthema",
                scientific_name="Trianthema portulacastrum",
                characteristics=["Prostrate broadleaf", "Succulent", "Pink flowers", "Forms dense mats"],
                control_methods={
                    "chemical": ["Pendimethalin 30% EC @ 1L/ha", "Imazethapyr 10% SL @ 75ml/ha"],
                    "organic": ["Hand weeding at 20 DAS", "Mulching", "Cover cropping"],
                    "mechanical": ["Inter-row weeding", "Hoeing"]
                },
                competition_impact="High - Reduces yield by 25-30%",
                growth_stage_vulnerability=["early_vegetative"]
            )
        ],
        growth_stages=["germination", "vegetative", "flowering", "pod_formation", "pod_filling", "maturity"],
        optimal_conditions={"temperature": "25-30°C", "rainfall": "600-900mm", "soil_ph": "6.5-7.5", "soil_type": "well-drained loam"},
        regional_importance=["Rajasthan", "Maharashtra", "Karnataka", "Andhra Pradesh", "Orissa"]
    ),

    "black_gram": Crop(
        name="Black Gram (Urad)",
        scientific_name="Vigna mungo",
        category="pulse",
        common_diseases=[
            Disease(
                name="Yellow Mosaic Virus",
                scientific_name="Mungbean Yellow Mosaic Virus",
                symptoms=["Bright yellow mosaic on leaves", "Stunting", "Flower drop", "Poor pod setting"],
                causes=["Whitefly-transmitted virus", "High temperature", "Dry weather"],
                treatment=["Spray Imidacloprid @ 0.5ml/L", "Thiamethoxam @ 0.3g/L for whitefly control"],
                prevention=["Use resistant varieties", "Early sowing", "Control whitefly vectors", "Reflective mulches"],
                affected_parts=["leaves", "flowers"]
            ),
            Disease(
                name="Cercospora Leaf Spot",
                scientific_name="Cercospora canescens",
                symptoms=["Circular brown spots on leaves", "Gray center with purple margins", "Premature leaf drop", "Reduced photosynthesis"],
                causes=["Fungal infection", "High humidity", "Warm weather"],
                treatment=["Spray Mancozeb 75% WP @ 2.5g/L", "Apply Carbendazim @ 1g/L", "2-3 sprays at 10-day intervals"],
                prevention=["Crop rotation", "Remove crop debris", "Avoid overhead irrigation", "Use healthy seeds"],
                affected_parts=["leaves"]
            )
        ],
        common_weeds=[
            Weed(
                name="Echinochloa",
                scientific_name="Echinochloa colonum",
                characteristics=["Annual grass", "Erect growth", "Purple stems", "Rapid growth"],
                control_methods={
                    "chemical": ["Pendimethalin @ 1L/ha", "Quizalofop-ethyl @ 50g/ha (post-emergence)"],
                    "organic": ["Hand weeding", "Mulching", "Cover crops"],
                    "mechanical": ["Inter-cultivation", "Hoeing at 20-25 DAS"]
                },
                competition_impact="Moderate",
                growth_stage_vulnerability=["vegetative"]
            )
        ],
        growth_stages=["germination", "vegetative", "flowering", "pod_development", "maturity"],
        optimal_conditions={"temperature": "25-35°C", "rainfall": "600-1000mm", "soil_ph": "6.5-7.5", "soil_type": "loam to clay loam"},
        regional_importance=["Andhra Pradesh", "Maharashtra", "Madhya Pradesh", "Uttar Pradesh", "Tamil Nadu"]
    ),

    "lentil": Crop(
        name="Lentil (Masoor)",
        scientific_name="Lens culinaris",
        category="pulse",
        common_diseases=[
            Disease(
                name="Rust",
                scientific_name="Uromyces viciae-fabae",
                symptoms=["Orange-brown pustules on leaves", "Premature defoliation", "Reduced pod formation", "Yield loss"],
                causes=["Fungal infection", "Cool humid weather", "Dense planting"],
                treatment=["Spray Mancozeb 75% WP @ 2.5g/L", "Apply Propiconazole @ 0.1%", "Repeat at 15-day intervals"],
                prevention=["Use resistant varieties", "Optimum plant spacing", "Avoid late sowing", "Remove infected debris"],
                affected_parts=["leaves", "stems", "pods"]
            ),
            Disease(
                name="Wilt",
                scientific_name="Fusarium oxysporum f.sp. lentis",
                symptoms=["Yellowing of leaves", "Vascular browning", "Drooping", "Plant death"],
                causes=["Soil-borne fungus", "High temperature", "Water stress"],
                treatment=["No effective chemical control", "Remove infected plants"],
                prevention=["Use wilt-resistant varieties", "Crop rotation", "Seed treatment with bioagents", "Deep summer plowing"],
                affected_parts=["vascular_system", "entire_plant"]
            )
        ],
        common_weeds=[
            Weed(
                name="Lathyrus",
                scientific_name="Lathyrus aphaca",
                characteristics=["Annual climber", "Yellow flowers", "Mimics lentil", "Reduces crop quality"],
                control_methods={
                    "chemical": ["Pendimethalin 30% EC @ 1L/ha", "Imazethapyr @ 75ml/ha"],
                    "organic": ["Hand weeding", "Use clean seeds", "Crop rotation"],
                    "mechanical": ["Hand pulling", "Inter-row weeding"]
                },
                competition_impact="High - Look-alike weed, difficult to separate",
                growth_stage_vulnerability=["all_stages"]
            )
        ],
        growth_stages=["germination", "vegetative", "flowering", "pod_formation", "maturity"],
        optimal_conditions={"temperature": "18-25°C", "rainfall": "300-400mm", "soil_ph": "6.0-7.5", "soil_type": "loamy to clay loam"},
        regional_importance=["Uttar Pradesh", "Madhya Pradesh", "West Bengal", "Bihar", "Jharkhand"]
    ),

    "groundnut": Crop(
        name="Groundnut (Peanut)",
        scientific_name="Arachis hypogaea",
        category="oilseed",
        common_diseases=[
            Disease(
                name="Tikka Disease (Leaf Spot)",
                scientific_name="Cercospora arachidicola",
                symptoms=["Circular brown spots on leaves", "Yellow halo around spots", "Premature defoliation", "Reduced pod yield"],
                causes=["Fungal infection", "High humidity", "Warm temperature"],
                treatment=["Spray Mancozeb 75% WP @ 2.5g/L", "Apply Chlorothalonil @ 2g/L", "3-4 sprays at 10-day intervals"],
                prevention=["Use resistant varieties", "Crop rotation", "Remove crop debris", "Balanced fertilization"],
                affected_parts=["leaves"]
            ),
            Disease(
                name="Stem Rot",
                scientific_name="Sclerotium rolfsii",
                symptoms=["Wilting of plants", "Brown lesions on stem near soil", "White mycelial growth", "Mustard seed-like sclerotia"],
                causes=["Soil-borne fungus", "High soil moisture", "High temperature"],
                treatment=["Spray Carbendazim @ 1g/L on stem base", "Apply Trichoderma-enriched FYM", "Metalaxyl soil drench"],
                prevention=["Deep summer plowing", "Crop rotation", "Proper drainage", "Seed treatment with Trichoderma"],
                affected_parts=["stem", "collar_region"]
            ),
            Disease(
                name="Rust",
                scientific_name="Puccinia arachidis",
                symptoms=["Reddish-brown pustules on leaves", "Premature leaf drop", "Reduced photosynthesis", "Yield reduction"],
                causes=["Fungal infection", "Cool humid nights", "Warm days"],
                treatment=["Spray Tebuconazole @ 1ml/L", "Apply Propiconazole @ 1ml/L", "2-3 sprays at 15-day intervals"],
                prevention=["Use rust-resistant varieties", "Avoid dense planting", "Remove volunteer plants", "Timely harvesting"],
                affected_parts=["leaves"]
            )
        ],
        common_weeds=[
            Weed(
                name="Cyperus",
                scientific_name="Cyperus rotundus",
                characteristics=["Perennial sedge", "Underground tubers", "Rapid spreading", "Drought tolerant"],
                control_methods={
                    "chemical": ["Pendimethalin 30% EC @ 1L/ha", "Imazethapyr @ 1L/ha", "Quizalofop-ethyl for grasses"],
                    "organic": ["Hand weeding at 20 and 40 DAS", "Mulching with crop residue", "Summer plowing"],
                    "mechanical": ["Inter-row cultivation", "Use of wheel hoe", "Repeated hoeing"]
                },
                competition_impact="High - Reduces yield by 30-50%",
                growth_stage_vulnerability=["all_stages"]
            ),
            Weed(
                name="Parthenium",
                scientific_name="Parthenium hysterophorus",
                characteristics=["Annual broadleaf", "White flowers", "Prolific seed producer", "Allelopathic"],
                control_methods={
                    "chemical": ["2,4-D @ 1kg/ha", "Metribuzin @ 0.5kg/ha (pre-emergence)"],
                    "organic": ["Hand pulling before flowering (wear gloves)", "Cover cropping", "Competitive cropping"],
                    "mechanical": ["Repeated cutting", "Uprooting", "Burning"]
                },
                competition_impact="Severe - Allelopathic effects, reduces crop growth",
                growth_stage_vulnerability=["early_to_mid_season"]
            )
        ],
        growth_stages=["germination", "vegetative", "flowering", "pegging", "pod_development", "pod_filling", "maturity"],
        optimal_conditions={"temperature": "25-30°C", "rainfall": "500-700mm", "soil_ph": "6.0-7.0", "soil_type": "well-drained sandy loam"},
        regional_importance=["Gujarat", "Andhra Pradesh", "Tamil Nadu", "Karnataka", "Rajasthan"]
    ),

    "soybean": Crop(
        name="Soybean",
        scientific_name="Glycine max",
        category="oilseed",
        common_diseases=[
            Disease(
                name="Yellow Mosaic Virus",
                scientific_name="Mungbean Yellow Mosaic Virus",
                symptoms=["Yellow mosaic on leaves", "Stunted growth", "Leaf curling", "Reduced pod formation"],
                causes=["Whitefly transmission", "Viral infection", "High temperature"],
                treatment=["Spray Imidacloprid @ 0.5ml/L", "Thiamethoxam @ 0.3g/L", "Control whitefly vectors"],
                prevention=["Use virus-resistant varieties", "Early sowing", "Control whitefly population", "Grow barrier crops"],
                affected_parts=["leaves", "entire_plant"]
            ),
            Disease(
                name="Rust",
                scientific_name="Phakopsora pachyrhizi",
                symptoms=["Small reddish-brown pustules on leaves", "Premature leaf drop", "Reduced photosynthesis", "Lower pod filling"],
                causes=["Fungal infection", "High humidity", "Moderate temperature"],
                treatment=["Spray Tebuconazole @ 1ml/L", "Apply Hexaconazole @ 2ml/L", "Trifloxystrobin + Tebuconazole"],
                prevention=["Use resistant cultivars", "Timely sowing", "Avoid dense planting", "Remove volunteer plants"],
                affected_parts=["leaves"]
            ),
            Disease(
                name="Bacterial Pustule",
                scientific_name="Xanthomonas axonopodis pv. glycines",
                symptoms=["Small pustules on leaves", "Yellow halo around pustules", "Leaf distortion", "Defoliation"],
                causes=["Bacterial infection", "High humidity", "Infected seeds"],
                treatment=["Spray Copper oxychloride @ 3g/L", "Streptocycline @ 0.5g/L", "Remove infected plants"],
                prevention=["Use disease-free seeds", "Crop rotation", "Avoid overhead irrigation", "Use resistant varieties"],
                affected_parts=["leaves"]
            )
        ],
        common_weeds=[
            Weed(
                name="Echinochloa",
                scientific_name="Echinochloa crusgalli",
                characteristics=["Annual grass", "Resembles rice", "Purple stems", "High seed production"],
                control_methods={
                    "chemical": ["Pendimethalin @ 1L/ha", "Imazethapyr @ 1L/ha", "Quizalofop-ethyl @ 50g/ha"],
                    "organic": ["Hand weeding at 20 and 40 DAS", "Mulching", "Intercropping"],
                    "mechanical": ["Inter-row cultivation", "Use of rotary weeder", "Hoeing"]
                },
                competition_impact="High - Competes strongly for resources",
                growth_stage_vulnerability=["vegetative", "flowering"]
            )
        ],
        growth_stages=["germination", "vegetative", "flowering", "pod_formation", "seed_filling", "maturity"],
        optimal_conditions={"temperature": "25-30°C", "rainfall": "600-1000mm", "soil_ph": "6.0-7.0", "soil_type": "well-drained loam"},
        regional_importance=["Madhya Pradesh", "Maharashtra", "Rajasthan", "Karnataka", "Andhra Pradesh"]
    ),

    "mustard": Crop(
        name="Mustard (Sarson)",
        scientific_name="Brassica juncea",
        category="oilseed",
        common_diseases=[
            Disease(
                name="Alternaria Blight",
                scientific_name="Alternaria brassicae",
                symptoms=["Circular dark brown spots on leaves", "Concentric rings in lesions", "Pod infection", "Premature leaf drop"],
                causes=["Fungal infection", "Cool humid weather", "Dew formation"],
                treatment=["Spray Mancozeb 75% WP @ 2.5g/L", "Apply Iprodione @ 1.5g/L", "Tebuconazole @ 1ml/L"],
                prevention=["Use disease-free seeds", "Crop rotation", "Proper spacing", "Avoid late sowing"],
                affected_parts=["leaves", "stems", "pods"]
            ),
            Disease(
                name="White Rust",
                scientific_name="Albugo candida",
                symptoms=["White pustules on leaves and stems", "Leaf thickening", "Stem gall formation", "Reduced seed yield"],
                causes=["Fungal infection", "Cool humid conditions", "Dense planting"],
                treatment=["Spray Metalaxyl + Mancozeb @ 2.5g/L", "Apply Ridomil MZ @ 2.5g/L", "2-3 sprays at 15-day intervals"],
                prevention=["Use resistant varieties", "Timely sowing", "Crop rotation", "Remove infected plants"],
                affected_parts=["leaves", "stems", "flowers"]
            )
        ],
        common_weeds=[
            Weed(
                name="Chenopodium",
                scientific_name="Chenopodium album",
                characteristics=["Annual broadleaf", "Mealy coating on leaves", "Rapid growth", "Prolific seeder"],
                control_methods={
                    "chemical": ["Pendimethalin @ 1L/ha", "Isoproturon @ 1kg/ha", "Metribuzin @ 175g/ha"],
                    "organic": ["Hand weeding at 25-30 DAS", "Mulching", "Cover cropping"],
                    "mechanical": ["Inter-row weeding", "Hoeing at 25 and 45 DAS"]
                },
                competition_impact="High - Major mustard weed",
                growth_stage_vulnerability=["vegetative", "flowering"]
            )
        ],
        growth_stages=["germination", "vegetative", "flowering", "siliqua_formation", "seed_filling", "maturity"],
        optimal_conditions={"temperature": "15-25°C", "rainfall": "300-400mm", "soil_ph": "6.0-7.5", "soil_type": "loamy to clay loam"},
        regional_importance=["Rajasthan", "Haryana", "Madhya Pradesh", "Uttar Pradesh", "Gujarat"]
    ),

    "sunflower": Crop(
        name="Sunflower",
        scientific_name="Helianthus annuus",
        category="oilseed",
        common_diseases=[
            Disease(
                name="Alternaria Blight",
                scientific_name="Alternaria helianthi",
                symptoms=["Dark brown spots on leaves", "Concentric rings", "Stem lesions", "Head rot"],
                causes=["Fungal infection", "High humidity", "Warm temperature"],
                treatment=["Spray Mancozeb @ 2.5g/L", "Apply Iprodione @ 1.5g/L", "Azoxystrobin @ 1ml/L"],
                prevention=["Use resistant hybrids", "Crop rotation", "Remove crop debris", "Proper drainage"],
                affected_parts=["leaves", "stems", "heads"]
            ),
            Disease(
                name="Downy Mildew",
                scientific_name="Plasmopara halstedii",
                symptoms=["Chlorotic patches on leaves", "Stunted growth", "White downy growth on leaf underside", "Deformed heads"],
                causes=["Soil-borne fungus", "Cool humid conditions", "Infected seeds"],
                treatment=["Spray Metalaxyl @ 2g/L", "Apply Ridomil MZ @ 2.5g/L", "Fosetyl-Al @ 2.5g/L"],
                prevention=["Treat seeds with Metalaxyl @ 6g/kg", "Use resistant hybrids", "Crop rotation", "Avoid waterlogging"],
                affected_parts=["leaves", "heads", "entire_plant"]
            )
        ],
        common_weeds=[
            Weed(
                name="Amaranthus",
                scientific_name="Amaranthus viridis",
                characteristics=["Annual broadleaf", "Erect growth", "Rapid development", "High biomass"],
                control_methods={
                    "chemical": ["Pendimethalin @ 1L/ha", "Oxyfluorfen @ 150ml/ha", "Imazethapyr @ 1L/ha"],
                    "organic": ["Hand weeding at 20 and 40 DAS", "Mulching", "Cover crops"],
                    "mechanical": ["Inter-cultivation", "Hoeing", "Hand pulling"]
                },
                competition_impact="Moderate to high",
                growth_stage_vulnerability=["early_vegetative"]
            )
        ],
        growth_stages=["germination", "vegetative", "bud_formation", "flowering", "seed_filling", "maturity"],
        optimal_conditions={"temperature": "20-27°C", "rainfall": "500-750mm", "soil_ph": "6.5-7.5", "soil_type": "well-drained loam"},
        regional_importance=["Karnataka", "Maharashtra", "Andhra Pradesh", "Bihar", "Orissa"]
    ),
})

# Add more crops (continued in next part due to size)
# Total: 48 crops covering cereals, pulses, oilseeds, vegetables, fruits, cash crops, spices

#!/usr/bin/env python3
"""
Weed Image Dataset Collector
Specialized collector for weed images from botanical and agricultural sources
"""

import requests
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pandas as pd
from dataclasses import dataclass
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class WeedImageData:
    """Structure for weed image data"""
    weed_name: str
    scientific_name: str
    common_names: List[str]
    family: str
    image_url: str
    source: str
    growth_stage: str  # seedling, juvenile, mature, flowering, seeding
    habitat: str  # crop_field, pasture, garden, roadside, etc.
    control_difficulty: str  # easy, moderate, difficult
    description: str
    control_methods: Optional[List[str]] = None

class WeedImageCollector:
    """Collector for weed images from various botanical and agricultural sources"""
    
    def __init__(self, output_dir: str = "weed_datasets"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Agricultural Research Bot 1.0'
        })
        
        # Comprehensive weed categories with detailed information
        self.weed_categories = {
            "broadleaf_weeds": {
                "dandelion": {
                    "scientific": "Taraxacum officinale",
                    "family": "Asteraceae",
                    "common_names": ["Common Dandelion", "Blowball"],
                    "habitats": ["lawn", "crop_field", "pasture", "garden"],
                    "difficulty": "moderate"
                },
                "plantain": {
                    "scientific": "Plantago major",
                    "family": "Plantaginaceae", 
                    "common_names": ["Broadleaf Plantain", "White Man's Foot"],
                    "habitats": ["lawn", "garden", "roadside"],
                    "difficulty": "easy"
                },
                "clover": {
                    "scientific": "Trifolium repens",
                    "family": "Fabaceae",
                    "common_names": ["White Clover", "Dutch Clover"],
                    "habitats": ["lawn", "pasture", "crop_field"],
                    "difficulty": "moderate"
                },
                "chickweed": {
                    "scientific": "Stellaria media",
                    "family": "Caryophyllaceae",
                    "common_names": ["Common Chickweed", "Starwort"],
                    "habitats": ["garden", "crop_field", "waste_areas"],
                    "difficulty": "easy"
                },
                "purslane": {
                    "scientific": "Portulaca oleracea",
                    "family": "Portulacaceae",
                    "common_names": ["Common Purslane", "Verdolaga"],
                    "habitats": ["garden", "crop_field", "sidewalk_cracks"],
                    "difficulty": "difficult"
                }
            },
            "grassy_weeds": {
                "crabgrass": {
                    "scientific": "Digitaria sanguinalis",
                    "family": "Poaceae",
                    "common_names": ["Large Crabgrass", "Hairy Crabgrass"],
                    "habitats": ["lawn", "garden", "crop_field"],
                    "difficulty": "moderate"
                },
                "foxtail": {
                    "scientific": "Setaria viridis",
                    "family": "Poaceae",
                    "common_names": ["Green Foxtail", "Wild Millet"],
                    "habitats": ["crop_field", "garden", "waste_areas"],
                    "difficulty": "moderate"
                },
                "quackgrass": {
                    "scientific": "Elymus repens",
                    "family": "Poaceae",
                    "common_names": ["Quackgrass", "Couch Grass"],
                    "habitats": ["crop_field", "garden", "pasture"],
                    "difficulty": "difficult"
                },
                "barnyard_grass": {
                    "scientific": "Echinochloa crus-galli",
                    "family": "Poaceae",
                    "common_names": ["Barnyard Grass", "Cockspur Grass"],
                    "habitats": ["rice_field", "wet_areas", "crop_field"],
                    "difficulty": "moderate"
                }
            },
            "sedges": {
                "yellow_nutsedge": {
                    "scientific": "Cyperus esculentus",
                    "family": "Cyperaceae",
                    "common_names": ["Yellow Nutsedge", "Chufa"],
                    "habitats": ["crop_field", "garden", "wet_areas"],
                    "difficulty": "difficult"
                },
                "purple_nutsedge": {
                    "scientific": "Cyperus rotundus",
                    "family": "Cyperaceae",
                    "common_names": ["Purple Nutsedge", "Nut Grass"],
                    "habitats": ["crop_field", "garden", "irrigation_ditches"],
                    "difficulty": "difficult"
                }
            },
            "annual_weeds": {
                "pigweed": {
                    "scientific": "Amaranthus palmeri",
                    "family": "Amaranthaceae",
                    "common_names": ["Palmer Amaranth", "Palmer Pigweed"],
                    "habitats": ["crop_field", "cotton_field", "soybean_field"],
                    "difficulty": "difficult"
                },
                "lambsquarters": {
                    "scientific": "Chenopodium album",
                    "family": "Amaranthaceae",
                    "common_names": ["Common Lambsquarters", "White Goosefoot"],
                    "habitats": ["crop_field", "garden", "waste_areas"],
                    "difficulty": "easy"
                },
                "ragweed": {
                    "scientific": "Ambrosia artemisiifolia",
                    "family": "Asteraceae",
                    "common_names": ["Common Ragweed", "Short Ragweed"],
                    "habitats": ["crop_field", "pasture", "roadside"],
                    "difficulty": "moderate"
                }
            },
            "perennial_weeds": {
                "canada_thistle": {
                    "scientific": "Cirsium arvense",
                    "family": "Asteraceae",
                    "common_names": ["Canada Thistle", "Creeping Thistle"],
                    "habitats": ["crop_field", "pasture", "roadside"],
                    "difficulty": "difficult"
                },
                "field_bindweed": {
                    "scientific": "Convolvulus arvensis",
                    "family": "Convolvulaceae",
                    "common_names": ["Field Bindweed", "Morning Glory"],
                    "habitats": ["crop_field", "garden", "fence_lines"],
                    "difficulty": "difficult"
                }
            }
        }
        
        self.growth_stages = ["seedling", "juvenile", "mature", "flowering", "seeding"]
        self.control_methods = {
            "mechanical": ["hand_pulling", "hoeing", "cultivation", "mowing"],
            "cultural": ["crop_rotation", "cover_crops", "mulching", "competitive_planting"],
            "chemical": ["pre_emergent", "post_emergent", "selective", "non_selective"],
            "biological": ["beneficial_insects", "allelopathy", "grazing"]
        }
    
    def collect_from_usda_plants_database(self) -> List[WeedImageData]:
        """Collect weed images from USDA Plants Database"""
        logger.info("🏛️ Collecting from USDA Plants Database...")
        
        # In production, this would make actual API calls to USDA
        return self._generate_usda_demo_data()
    
    def _generate_usda_demo_data(self) -> List[WeedImageData]:
        """Generate demo USDA data"""
        demo_data = []
        base_url = "https://via.placeholder.com/500x400"
        
        for category, weeds in self.weed_categories.items():
            for weed_name, info in weeds.items():
                for i, stage in enumerate(self.growth_stages):
                    for j, habitat in enumerate(info["habitats"][:2]):  # Limit for demo
                        color = f"{hash(f'{weed_name}{stage}') % 16777215:06x}"
                        demo_data.append(WeedImageData(
                            weed_name=weed_name,
                            scientific_name=info["scientific"],
                            common_names=info["common_names"],
                            family=info["family"],
                            image_url=f"{base_url}/{color}/000000?text=USDA+{weed_name}+{stage}",
                            source="USDA Plants Database Demo",
                            growth_stage=stage,
                            habitat=habitat,
                            control_difficulty=info["difficulty"],
                            description=f"USDA documentation of {weed_name} at {stage} stage in {habitat}",
                            control_methods=self.control_methods["mechanical"] + self.control_methods["chemical"]
                        ))
        
        return demo_data[:50]  # Limit for demo
    
    def collect_from_extension_services(self) -> List[WeedImageData]:
        """Collect from agricultural extension services"""
        logger.info("🌾 Collecting from Extension Services...")
        
        # Extension service URLs
        extension_sources = [
            "https://extension.umn.edu/weeds",
            "https://www.ag.ndsu.edu/weeds",
            "https://extension.psu.edu/weeds",
            "https://extension.umd.edu/resource/weed-identification"
        ]
        
        return self._generate_extension_demo_data()
    
    def _generate_extension_demo_data(self) -> List[WeedImageData]:
        """Generate demo extension service data"""
        demo_data = []
        base_url = "https://via.placeholder.com/600x450"
        
        # Focus on common agricultural weeds
        common_weeds = ["crabgrass", "dandelion", "pigweed", "lambsquarters", "foxtail"]
        
        for weed in common_weeds:
            # Find the weed info
            weed_info = None
            for category, weeds in self.weed_categories.items():
                if weed in weeds:
                    weed_info = weeds[weed]
                    break
            
            if weed_info:
                for i, stage in enumerate(["seedling", "mature", "flowering"]):
                    color_map = {"seedling": "90EE90", "mature": "228B22", "flowering": "FFD700"}
                    demo_data.append(WeedImageData(
                        weed_name=weed,
                        scientific_name=weed_info["scientific"],
                        common_names=weed_info["common_names"],
                        family=weed_info["family"],
                        image_url=f"{base_url}/{color_map[stage]}/000000?text=Ext+{weed}+{stage}",
                        source="Extension Service Demo",
                        growth_stage=stage,
                        habitat="crop_field",
                        control_difficulty=weed_info["difficulty"],
                        description=f"Extension service documentation of {weed} at {stage} stage"
                    ))
        
        return demo_data
    
    def collect_from_weed_id_apps(self) -> List[WeedImageData]:
        """Collect from weed identification applications and databases"""
        logger.info("📱 Collecting from Weed ID Applications...")
        
        # Weed ID sources
        weed_id_sources = [
            "iMapInvasives",
            "PlantNet",
            "Seek by iNaturalist",
            "LeafSnap",
            "PictureThis"
        ]
        
        return self._generate_weed_id_demo_data()
    
    def _generate_weed_id_demo_data(self) -> List[WeedImageData]:
        """Generate demo weed ID app data"""
        demo_data = []
        base_url = "https://via.placeholder.com/400x300"
        
        # Focus on easily identifiable weeds
        for category, weeds in self.weed_categories.items():
            for weed_name, info in list(weeds.items())[:2]:  # First 2 from each category
                color = f"{hash(weed_name) % 16777215:06x}"
                demo_data.append(WeedImageData(
                    weed_name=weed_name,
                    scientific_name=info["scientific"],
                    common_names=info["common_names"],
                    family=info["family"],
                    image_url=f"{base_url}/{color}/FFFFFF?text=ID+{weed_name}",
                    source="Weed ID App Demo",
                    growth_stage="mature",
                    habitat="field_observation",
                    control_difficulty=info["difficulty"],
                    description=f"Field identification photo of {weed_name}",
                    control_methods=["identification", "reporting"]
                ))
        
        return demo_data
    
    def collect_from_research_databases(self) -> List[WeedImageData]:
        """Collect from weed science research databases"""
        logger.info("🔬 Collecting from Research Databases...")
        
        research_sources = [
            "Weed Science Society of America",
            "International Weed Science Society", 
            "Invasive Species Database",
            "Global Biodiversity Information Facility"
        ]
        
        return self._generate_research_demo_data()
    
    def _generate_research_demo_data(self) -> List[WeedImageData]:
        """Generate demo research database data"""
        demo_data = []
        base_url = "https://via.placeholder.com/800x600"
        
        # Focus on scientifically important weeds
        research_weeds = ["pigweed", "canada_thistle", "field_bindweed", "yellow_nutsedge"]
        
        for weed in research_weeds:
            weed_info = None
            for category, weeds in self.weed_categories.items():
                if weed in weeds:
                    weed_info = weeds[weed]
                    break
            
            if weed_info:
                for stage in ["juvenile", "mature", "reproductive"]:
                    color = "4169E1"  # Research blue
                    demo_data.append(WeedImageData(
                        weed_name=weed,
                        scientific_name=weed_info["scientific"],
                        common_names=weed_info["common_names"],
                        family=weed_info["family"],
                        image_url=f"{base_url}/{color}/FFFFFF?text=Research+{weed}+{stage}",
                        source="Research Database Demo",
                        growth_stage=stage,
                        habitat="research_plot",
                        control_difficulty=weed_info["difficulty"],
                        description=f"Research documentation of {weed} biology and control",
                        control_methods=["experimental", "integrated_management"]
                    ))
        
        return demo_data
    
    def collect_from_citizen_science(self) -> List[WeedImageData]:
        """Collect from citizen science platforms"""
        logger.info("👥 Collecting from Citizen Science...")
        
        # Focus on common garden and landscape weeds
        return self._generate_citizen_science_demo_data()
    
    def _generate_citizen_science_demo_data(self) -> List[WeedImageData]:
        """Generate demo citizen science data"""
        demo_data = []
        base_url = "https://via.placeholder.com/300x225"
        
        citizen_weeds = ["dandelion", "clover", "plantain", "chickweed", "crabgrass"]
        
        for weed in citizen_weeds:
            weed_info = None
            for category, weeds in self.weed_categories.items():
                if weed in weeds:
                    weed_info = weeds[weed]
                    break
            
            if weed_info:
                for i in range(3):  # Multiple citizen observations
                    color = "32CD32"  # Citizen green
                    demo_data.append(WeedImageData(
                        weed_name=weed,
                        scientific_name=weed_info["scientific"],
                        common_names=weed_info["common_names"],
                        family=weed_info["family"],
                        image_url=f"{base_url}/{color}/000000?text=Citizen+{weed}+{i+1}",
                        source="Citizen Science Demo",
                        growth_stage="observed",
                        habitat="residential",
                        control_difficulty=weed_info["difficulty"],
                        description=f"Citizen science observation of {weed}",
                        control_methods=["manual_removal", "organic_control"]
                    ))
        
        return demo_data
    
    def download_images(self, image_data_list: List[WeedImageData]) -> List[Dict[str, Any]]:
        """Download weed images and save with metadata"""
        logger.info(f"📥 Downloading {len(image_data_list)} weed images...")
        
        downloaded = []
        
        for i, data in enumerate(image_data_list):
            try:
                # Create directory structure
                weed_dir = self.output_dir / data.weed_name
                stage_dir = weed_dir / data.growth_stage
                stage_dir.mkdir(parents=True, exist_ok=True)
                
                # Download image
                response = self.session.get(data.image_url, timeout=30)
                response.raise_for_status()
                
                # Generate filename
                filename = f"{data.weed_name}_{data.growth_stage}_{data.habitat}_{i}.jpg"
                file_path = stage_dir / filename
                
                # Save image
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                # Create metadata
                metadata = {
                    "filename": str(file_path.relative_to(self.output_dir)),
                    "weed_name": data.weed_name,
                    "scientific_name": data.scientific_name,
                    "common_names": data.common_names,
                    "family": data.family,
                    "growth_stage": data.growth_stage,
                    "habitat": data.habitat,
                    "control_difficulty": data.control_difficulty,
                    "source": data.source,
                    "description": data.description,
                    "control_methods": data.control_methods,
                    "url": data.image_url,
                    "file_size": len(response.content),
                    "hash": hashlib.md5(response.content).hexdigest()
                }
                
                downloaded.append(metadata)
                
                if i % 10 == 0:
                    logger.info(f"🌿 Downloaded {i+1}/{len(image_data_list)} weed images")
                
                time.sleep(0.3)  # Rate limiting
                
            except Exception as e:
                logger.error(f"❌ Failed to download {data.image_url}: {e}")
        
        logger.info(f"✅ Successfully downloaded {len(downloaded)} weed images")
        return downloaded
    
    def save_metadata(self, metadata_list: List[Dict[str, Any]]):
        """Save weed metadata to files"""
        if not metadata_list:
            logger.warning("No metadata to save")
            return
        
        # Save as CSV
        df = pd.DataFrame(metadata_list)
        csv_path = self.output_dir / "weed_metadata.csv"
        df.to_csv(csv_path, index=False)
        
        # Save as JSON
        json_path = self.output_dir / "weed_metadata.json"
        with open(json_path, 'w') as f:
            json.dump(metadata_list, f, indent=2)
        
        # Generate summary
        summary = {
            "total_images": len(metadata_list),
            "weeds": df['weed_name'].value_counts().to_dict(),
            "families": df['family'].value_counts().to_dict(),
            "growth_stages": df['growth_stage'].value_counts().to_dict(),
            "habitats": df['habitat'].value_counts().to_dict(),
            "sources": df['source'].value_counts().to_dict(),
            "control_difficulty": df['control_difficulty'].value_counts().to_dict()
        }
        
        summary_path = self.output_dir / "weed_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"💾 Saved weed metadata: {csv_path}")
        logger.info(f"📊 Dataset summary: {len(summary['weeds'])} weeds, {len(summary['families'])} families")
    
    def collect_complete_dataset(self) -> Dict[str, Any]:
        """Run complete weed image collection"""
        logger.info("🚀 Starting complete weed image collection...")
        
        start_time = time.time()
        
        # Collect from all sources
        all_data = []
        all_data.extend(self.collect_from_usda_plants_database())
        all_data.extend(self.collect_from_extension_services())
        all_data.extend(self.collect_from_weed_id_apps())
        all_data.extend(self.collect_from_research_databases())
        all_data.extend(self.collect_from_citizen_science())
        
        logger.info(f"📊 Collected {len(all_data)} weed image records")
        
        # Download images
        downloaded_metadata = self.download_images(all_data)
        
        # Save metadata
        self.save_metadata(downloaded_metadata)
        
        end_time = time.time()
        
        results = {
            "total_collected": len(downloaded_metadata),
            "unique_weeds": len(set(item['weed_name'] for item in downloaded_metadata)),
            "unique_families": len(set(item['family'] for item in downloaded_metadata)),
            "growth_stages": len(set(item['growth_stage'] for item in downloaded_metadata)),
            "duration": end_time - start_time,
            "output_dir": str(self.output_dir)
        }
        
        logger.info("✅ Weed image collection completed!")
        return results

def main():
    """Main execution"""
    collector = WeedImageCollector()
    results = collector.collect_complete_dataset()
    
    print("\n" + "="*60)
    print("🌿 WEED IMAGE DATASET COLLECTION COMPLETE")
    print("="*60)
    print(f"📸 Total Images: {results['total_collected']}")
    print(f"🏷️  Unique Weeds: {results['unique_weeds']}")
    print(f"🏛️  Plant Families: {results['unique_families']}")
    print(f"🌱 Growth Stages: {results['growth_stages']}")
    print(f"⏱️  Duration: {results['duration']:.1f} seconds")
    print(f"📁 Output: {results['output_dir']}")
    print("="*60)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Agricultural Image Dataset Collector
Comprehensive system for collecting plant disease and weed images from web sources
"""

import requests
import base64
import json
import os
import time
import csv
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from urllib.parse import urljoin, urlparse
from PIL import Image
import io
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import concurrent.futures
from dataclasses import dataclass, asdict
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ImageMetadata:
    """Metadata for collected images"""
    url: str
    filename: str
    category: str  # 'disease' or 'weed'
    subcategory: str  # specific disease/weed type
    source: str  # website/database source
    description: str
    size: Tuple[int, int]
    file_size: int
    hash_md5: str
    collection_date: str
    crop_type: Optional[str] = None
    severity: Optional[str] = None
    quality_score: Optional[float] = None

class AgricultureImageCollector:
    """Main class for collecting agricultural images from web sources"""
    
    def __init__(self, output_dir: str = "agricultural_datasets"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.disease_dir = self.output_dir / "diseases"
        self.weed_dir = self.output_dir / "weeds"
        self.metadata_dir = self.output_dir / "metadata"
        
        for dir_path in [self.disease_dir, self.weed_dir, self.metadata_dir]:
            dir_path.mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        self.collected_images = []
        self.failed_downloads = []
        
        # Rate limiting
        self.request_delay = 1.0  # seconds between requests
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Implement rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _get_image_hash(self, image_data: bytes) -> str:
        """Calculate MD5 hash of image data"""
        return hashlib.md5(image_data).hexdigest()
    
    def _validate_image(self, image_data: bytes) -> Optional[Tuple[int, int]]:
        """Validate and get image dimensions"""
        try:
            image = Image.open(io.BytesIO(image_data))
            return image.size
        except Exception:
            return None
    
    def download_image(self, url: str, filename: str, category: str, 
                      subcategory: str, source: str, description: str = "",
                      crop_type: Optional[str] = None) -> Optional[ImageMetadata]:
        """Download a single image and save metadata"""
        try:
            self._rate_limit()
            
            logger.info(f"Downloading: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Validate image
            image_size = self._validate_image(response.content)
            if not image_size:
                logger.warning(f"Invalid image: {url}")
                return None
            
            # Skip very small images
            if image_size[0] < 100 or image_size[1] < 100:
                logger.warning(f"Image too small: {url} - {image_size}")
                return None
            
            # Determine save directory
            save_dir = self.disease_dir if category == "disease" else self.weed_dir
            subcategory_dir = save_dir / subcategory
            subcategory_dir.mkdir(exist_ok=True)
            
            # Save image
            file_path = subcategory_dir / filename
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Create metadata
            metadata = ImageMetadata(
                url=url,
                filename=str(file_path.relative_to(self.output_dir)),
                category=category,
                subcategory=subcategory,
                source=source,
                description=description,
                size=image_size,
                file_size=len(response.content),
                hash_md5=self._get_image_hash(response.content),
                collection_date=time.strftime("%Y-%m-%d %H:%M:%S"),
                crop_type=crop_type
            )
            
            self.collected_images.append(metadata)
            logger.info(f"✅ Downloaded: {filename} ({image_size[0]}x{image_size[1]})")
            return metadata
            
        except Exception as e:
            logger.error(f"❌ Failed to download {url}: {e}")
            self.failed_downloads.append({"url": url, "error": str(e)})
            return None
    
    def collect_from_plant_disease_apis(self) -> List[ImageMetadata]:
        """Collect disease images from plant disease APIs and databases"""
        logger.info("🔍 Collecting from plant disease APIs...")
        
        collected = []
        
        # Plant disease database sources (simulated - you would need actual API keys)
        disease_sources = [
            {
                "name": "PlantNet API",
                "diseases": ["leaf_spot", "rust", "powdery_mildew", "blight", "mosaic_virus"],
                "url_template": "https://my-api.plantnet.org/v2/identify/plants?images={}&modifiers=crops&api-key=YOUR_API_KEY"
            },
            {
                "name": "Open Plant Pathology",
                "diseases": ["bacterial_spot", "fungal_infection", "viral_disease", "nutrient_deficiency"],
                "url_template": "https://www.openplantpathology.org/api/images?disease={}&limit=50"
            }
        ]
        
        # For demonstration, we'll create synthetic disease image URLs
        # In production, you would integrate with actual APIs
        demo_disease_images = self._generate_demo_disease_urls()
        
        for i, (disease, urls) in enumerate(demo_disease_images.items()):
            for j, url in enumerate(urls[:10]):  # Limit for demo
                filename = f"{disease}_{i}_{j}.jpg"
                metadata = self.download_image(
                    url, filename, "disease", disease, 
                    "Demo Agricultural Database",
                    f"Plant disease example: {disease}"
                )
                if metadata:
                    collected.append(metadata)
        
        return collected
    
    def collect_from_weed_databases(self) -> List[ImageMetadata]:
        """Collect weed images from agricultural weed databases"""
        logger.info("🌿 Collecting from weed databases...")
        
        collected = []
        
        # Weed database sources
        weed_sources = [
            {
                "name": "USDA Weed Database",
                "weeds": ["dandelion", "crabgrass", "plantain", "clover", "chickweed"],
                "url_template": "https://plants.usda.gov/api/images?plant={}&category=weed"
            },
            {
                "name": "AgriLife Extension",
                "weeds": ["pigweed", "lambsquarters", "foxtail", "purslane", "ragweed"],
                "url_template": "https://agrilife.tamu.edu/api/weed-images?type={}"
            }
        ]
        
        # For demonstration, create synthetic weed image URLs
        demo_weed_images = self._generate_demo_weed_urls()
        
        for i, (weed, urls) in enumerate(demo_weed_images.items()):
            for j, url in enumerate(urls[:10]):  # Limit for demo
                filename = f"{weed}_{i}_{j}.jpg"
                metadata = self.download_image(
                    url, filename, "weed", weed,
                    "Demo Weed Database", 
                    f"Weed identification example: {weed}"
                )
                if metadata:
                    collected.append(metadata)
        
        return collected
    
    def _generate_demo_disease_urls(self) -> Dict[str, List[str]]:
        """Generate demo disease image URLs (replace with actual API calls)"""
        return {
            "leaf_spot": [
                "https://via.placeholder.com/400x300/228B22/000000?text=Leaf+Spot+1",
                "https://via.placeholder.com/450x350/32CD32/000000?text=Leaf+Spot+2",
                "https://via.placeholder.com/500x400/90EE90/000000?text=Leaf+Spot+3",
            ],
            "rust": [
                "https://via.placeholder.com/400x300/CD853F/000000?text=Rust+Disease+1",
                "https://via.placeholder.com/420x320/D2691E/000000?text=Rust+Disease+2",
                "https://via.placeholder.com/380x280/A0522D/000000?text=Rust+Disease+3",
            ],
            "powdery_mildew": [
                "https://via.placeholder.com/400x300/F5F5DC/000000?text=Powdery+Mildew+1",
                "https://via.placeholder.com/430x330/FFFACD/000000?text=Powdery+Mildew+2",
                "https://via.placeholder.com/410x310/F0F8FF/000000?text=Powdery+Mildew+3",
            ],
            "blight": [
                "https://via.placeholder.com/400x300/8B4513/000000?text=Blight+1",
                "https://via.placeholder.com/440x340/A0522D/000000?text=Blight+2",
                "https://via.placeholder.com/390x290/654321/000000?text=Blight+3",
            ]
        }
    
    def _generate_demo_weed_urls(self) -> Dict[str, List[str]]:
        """Generate demo weed image URLs (replace with actual API calls)"""
        return {
            "dandelion": [
                "https://via.placeholder.com/400x300/FFD700/000000?text=Dandelion+1",
                "https://via.placeholder.com/420x320/FFFF00/000000?text=Dandelion+2",
                "https://via.placeholder.com/380x280/FFA500/000000?text=Dandelion+3",
            ],
            "crabgrass": [
                "https://via.placeholder.com/400x300/9ACD32/000000?text=Crabgrass+1",
                "https://via.placeholder.com/430x330/6B8E23/000000?text=Crabgrass+2",
                "https://via.placeholder.com/410x310/808000/000000?text=Crabgrass+3",
            ],
            "plantain": [
                "https://via.placeholder.com/400x300/228B22/000000?text=Plantain+1",
                "https://via.placeholder.com/440x340/32CD32/000000?text=Plantain+2",
                "https://via.placeholder.com/390x290/00FF00/000000?text=Plantain+3",
            ],
            "clover": [
                "https://via.placeholder.com/400x300/98FB98/000000?text=Clover+1",
                "https://via.placeholder.com/420x320/90EE90/000000?text=Clover+2",
                "https://via.placeholder.com/380x280/8FBC8F/000000?text=Clover+3",
            ]
        }
    
    def scrape_research_papers(self, keywords: List[str], max_papers: int = 20) -> List[ImageMetadata]:
        """Scrape images from agricultural research papers"""
        logger.info("📚 Scraping research paper images...")
        
        collected = []
        
        # Research paper sources (demo URLs)
        research_sources = [
            "https://www.frontiersin.org/journals/plant-science",
            "https://apsjournals.apsnet.org/",
            "https://www.cambridge.org/core/journals/plant-pathology"
        ]
        
        # This would be expanded to actually scrape research papers
        # For demo, we'll create synthetic research image URLs
        for keyword in keywords:
            demo_urls = [
                f"https://via.placeholder.com/500x400/4169E1/000000?text=Research+{keyword}+{i}"
                for i in range(3)
            ]
            
            for i, url in enumerate(demo_urls):
                filename = f"research_{keyword}_{i}.jpg"
                metadata = self.download_image(
                    url, filename, "disease", keyword,
                    "Research Papers", f"Research image: {keyword}"
                )
                if metadata:
                    collected.append(metadata)
        
        return collected
    
    def save_metadata(self):
        """Save collected metadata to CSV and JSON files"""
        if not self.collected_images:
            logger.warning("No images collected to save metadata")
            return
        
        # Convert to list of dictionaries
        metadata_list = [asdict(img) for img in self.collected_images]
        
        # Save as CSV
        csv_path = self.metadata_dir / "collected_images.csv"
        df = pd.DataFrame(metadata_list)
        df.to_csv(csv_path, index=False)
        logger.info(f"💾 Saved metadata CSV: {csv_path}")
        
        # Save as JSON
        json_path = self.metadata_dir / "collected_images.json"
        with open(json_path, 'w') as f:
            json.dump(metadata_list, f, indent=2)
        logger.info(f"💾 Saved metadata JSON: {json_path}")
        
        # Save failed downloads
        if self.failed_downloads:
            failed_path = self.metadata_dir / "failed_downloads.json"
            with open(failed_path, 'w') as f:
                json.dump(self.failed_downloads, f, indent=2)
            logger.info(f"💾 Saved failed downloads: {failed_path}")
        
        # Generate summary
        self._generate_summary()
    
    def _generate_summary(self):
        """Generate collection summary"""
        summary = {
            "total_images": len(self.collected_images),
            "diseases": {},
            "weeds": {},
            "sources": {},
            "collection_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        for img in self.collected_images:
            # Count by category
            if img.category == "disease":
                summary["diseases"][img.subcategory] = summary["diseases"].get(img.subcategory, 0) + 1
            else:
                summary["weeds"][img.subcategory] = summary["weeds"].get(img.subcategory, 0) + 1
            
            # Count by source
            summary["sources"][img.source] = summary["sources"].get(img.source, 0) + 1
        
        summary_path = self.metadata_dir / "collection_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"📊 Collection Summary:")
        logger.info(f"  Total Images: {summary['total_images']}")
        logger.info(f"  Disease Categories: {len(summary['diseases'])}")
        logger.info(f"  Weed Categories: {len(summary['weeds'])}")
        logger.info(f"  Sources: {len(summary['sources'])}")
    
    def collect_all(self) -> Dict[str, Any]:
        """Run complete collection process"""
        logger.info("🚀 Starting comprehensive agricultural image collection...")
        
        start_time = time.time()
        
        # Collect from various sources
        disease_images = self.collect_from_plant_disease_apis()
        weed_images = self.collect_from_weed_databases()
        research_images = self.scrape_research_papers(
            ["leaf_spot", "rust", "blight", "dandelion", "crabgrass"]
        )
        
        # Save metadata
        self.save_metadata()
        
        end_time = time.time()
        duration = end_time - start_time
        
        results = {
            "total_collected": len(self.collected_images),
            "disease_images": len([img for img in self.collected_images if img.category == "disease"]),
            "weed_images": len([img for img in self.collected_images if img.category == "weed"]),
            "failed_downloads": len(self.failed_downloads),
            "duration_seconds": duration,
            "output_directory": str(self.output_dir)
        }
        
        logger.info("✅ Collection completed!")
        logger.info(f"📈 Results: {results}")
        
        return results

def main():
    """Main execution function"""
    collector = AgricultureImageCollector()
    results = collector.collect_all()
    
    print("\n" + "="*50)
    print("🌾 AGRICULTURAL IMAGE COLLECTION COMPLETE")
    print("="*50)
    print(f"📸 Total Images Collected: {results['total_collected']}")
    print(f"🦠 Disease Images: {results['disease_images']}")
    print(f"🌿 Weed Images: {results['weed_images']}")
    print(f"⏱️  Duration: {results['duration_seconds']:.1f} seconds")
    print(f"📁 Output Directory: {results['output_directory']}")
    print("="*50)

if __name__ == "__main__":
    main()
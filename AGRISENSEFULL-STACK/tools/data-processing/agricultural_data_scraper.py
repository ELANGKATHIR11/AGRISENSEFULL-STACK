#!/usr/bin/env python3
"""
Agricultural Data Scraper for Disease and Weed Detection
Collects images and metadata from various agricultural databases and research sources
"""

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup, Tag
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging
from urllib.parse import urljoin, urlparse
import time
import hashlib
from PIL import Image
import io
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HERE = Path(__file__).parent
DATASETS_DIR = HERE.parent.parent / "datasets"
DISEASE_DATA_DIR = DATASETS_DIR / "disease_detection"
WEED_DATA_DIR = DATASETS_DIR / "weed_management"

# Create directories
DISEASE_DATA_DIR.mkdir(parents=True, exist_ok=True)
WEED_DATA_DIR.mkdir(parents=True, exist_ok=True)


class AgriculturalDataScraper:
    """Comprehensive scraper for agricultural disease and weed data"""

    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Known agricultural databases and sources
        self.disease_sources = {
            "plantnet": "https://identify.plantnet.org/",
            "inaturalist": "https://www.inaturalist.org/",
            "plantvillage": "https://plantvillage.psu.edu/",
            "usda_ars": "https://www.ars.usda.gov/",
            "extension_services": [
                "https://extension.umn.edu/",
                "https://extension.psu.edu/",
                "https://extension.wisc.edu/"
            ]
        }
        
        self.weed_sources = {
            "invasive_org": "https://www.invasive.org/",
            "weedscience": "https://weedscience.org/",
            "usda_plants": "https://plants.usda.gov/",
            "weed_database": "https://www.weedscience.com/"
        }
        
        # Common plant diseases to search for
        self.target_diseases = [
            "bacterial_spot", "early_blight", "late_blight", "leaf_mold", "septoria_leaf_spot",
            "spider_mites", "target_spot", "yellow_leaf_curl_virus", "mosaic_virus",
            "bacterial_canker", "bacterial_speck", "powdery_mildew", "downy_mildew",
            "anthracnose", "black_rot", "clubroot", "damping_off", "fusarium_wilt",
            "verticillium_wilt", "root_rot", "crown_rot", "rust", "smut"
        ]
        
        # Common weeds to search for
        self.target_weeds = [
            "crabgrass", "dandelion", "clover", "plantain", "chickweed", "lambsquarters",
            "pigweed", "foxtail", "barnyard_grass", "johnson_grass", "quackgrass",
            "bermuda_grass", "nutgrass", "thistle", "dock", "bindweed", "purslane",
            "shepherd_purse", "wild_mustard", "ragweed", "goldenrod", "smartweed"
        ]

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def download_image(self, url: str, save_path: Path) -> bool:
        """Download and save an image from URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Verify it's an image
            image = Image.open(io.BytesIO(response.content))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large
            if image.width > 1024 or image.height > 1024:
                image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            
            # Save the image
            image.save(save_path, 'JPEG', quality=90)
            logger.info(f"Downloaded image: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download image {url}: {e}")
            return False

    def search_google_images(self, query: str, num_images: int = 50) -> List[str]:
        """Search Google Images for plant disease/weed images"""
        try:
            # Google Images search URL
            search_url = f"https://www.google.com/search?q={query}&tbm=isch&hl=en"
            
            response = requests.get(search_url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract image URLs from search results
            image_urls = []
            img_tags = soup.find_all('img')
            
            for img in img_tags[:num_images]:
                # Ensure img is a Tag and has attributes
                if isinstance(img, Tag) and hasattr(img, 'attrs'):
                    if 'src' in img.attrs:
                        src = img.attrs['src']
                        if isinstance(src, str) and src.startswith('http') and any(ext in src for ext in ['.jpg', '.jpeg', '.png']):
                            image_urls.append(src)
                            
                    if 'data-src' in img.attrs:
                        src = img.attrs['data-src']
                        if isinstance(src, str) and src.startswith('http') and any(ext in src for ext in ['.jpg', '.jpeg', '.png']):
                            image_urls.append(src)
            
            return image_urls[:num_images]
            
        except Exception as e:
            logger.error(f"Failed to search Google Images for '{query}': {e}")
            return []

    def search_inaturalist(self, query: str, num_images: int = 30) -> List[Dict[str, Any]]:
        """Search iNaturalist for plant observations"""
        try:
            # iNaturalist API
            api_url = "https://api.inaturalist.org/v1/observations"
            params = {
                'q': query,
                'quality_grade': 'research',
                'photos': 'true',
                'per_page': num_images,
                'order': 'desc',
                'order_by': 'created_at'
            }
            
            response = requests.get(api_url, params=params)
            data = response.json()
            
            observations = []
            for obs in data.get('results', []):
                if obs.get('photos'):
                    for photo in obs['photos']:
                        observations.append({
                            'url': photo['url'],
                            'medium_url': photo.get('medium_url', photo['url']),
                            'attribution': photo.get('attribution'),
                            'species': obs.get('species_guess', ''),
                            'observed_on': obs.get('observed_on', ''),
                            'location': obs.get('place_guess', ''),
                            'quality_grade': obs.get('quality_grade', ''),
                            'source': 'inaturalist'
                        })
            
            return observations
            
        except Exception as e:
            logger.error(f"Failed to search iNaturalist for '{query}': {e}")
            return []

    def collect_disease_data(self, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Collect comprehensive disease detection data"""
        if output_dir is None:
            output_dir = DISEASE_DATA_DIR
            
        results = {
            'collected_diseases': {},
            'total_images': 0,
            'sources': []
        }
        
        for disease in self.target_diseases:
            disease_dir = output_dir / disease
            disease_dir.mkdir(exist_ok=True)
            
            logger.info(f"Collecting data for disease: {disease}")
            
            # Search multiple sources
            disease_data = {
                'images': [],
                'metadata': [],
                'sources': []
            }
            
            # Google Images search
            search_queries = [
                f"{disease} plant disease",
                f"{disease} symptoms plant",
                f"{disease} crop disease",
                f"{disease} leaf disease"
            ]
            
            for query in search_queries:
                logger.info(f"Searching: {query}")
                
                # Google Images
                google_urls = self.search_google_images(query, 20)
                for i, url in enumerate(google_urls):
                    filename = f"google_{disease}_{i}_{hashlib.md5(url.encode()).hexdigest()[:8]}.jpg"
                    save_path = disease_dir / filename
                    
                    if self.download_image(url, save_path):
                        disease_data['images'].append(str(save_path))
                        disease_data['metadata'].append({
                            'filename': filename,
                            'source': 'google_images',
                            'query': query,
                            'disease': disease,
                            'url': url
                        })
                
                # iNaturalist search
                inaturalist_data = self.search_inaturalist(query, 15)
                for i, obs in enumerate(inaturalist_data):
                    filename = f"inat_{disease}_{i}_{hashlib.md5(obs['url'].encode()).hexdigest()[:8]}.jpg"
                    save_path = disease_dir / filename
                    
                    if self.download_image(obs['medium_url'], save_path):
                        disease_data['images'].append(str(save_path))
                        disease_data['metadata'].append({
                            'filename': filename,
                            'source': 'inaturalist',
                            'query': query,
                            'disease': disease,
                            'url': obs['url'],
                            'species': obs['species'],
                            'location': obs['location'],
                            'observed_on': obs['observed_on']
                        })
                
                # Add delay to be respectful
                time.sleep(2)
            
            results['collected_diseases'][disease] = disease_data
            results['total_images'] += len(disease_data['images'])
            
            # Save metadata for this disease
            metadata_file = disease_dir / f"{disease}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(disease_data, f, indent=2)
        
        return results

    def collect_weed_data(self, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Collect comprehensive weed detection data"""
        if output_dir is None:
            output_dir = WEED_DATA_DIR
            
        results = {
            'collected_weeds': {},
            'total_images': 0,
            'sources': []
        }
        
        for weed in self.target_weeds:
            weed_dir = output_dir / weed
            weed_dir.mkdir(exist_ok=True)
            
            logger.info(f"Collecting data for weed: {weed}")
            
            weed_data = {
                'images': [],
                'metadata': [],
                'sources': []
            }
            
            # Search multiple sources
            search_queries = [
                f"{weed} weed identification",
                f"{weed} invasive plant",
                f"{weed} garden weed",
                f"{weed} agriculture weed"
            ]
            
            for query in search_queries:
                logger.info(f"Searching: {query}")
                
                # Google Images
                google_urls = self.search_google_images(query, 20)
                for i, url in enumerate(google_urls):
                    filename = f"google_{weed}_{i}_{hashlib.md5(url.encode()).hexdigest()[:8]}.jpg"
                    save_path = weed_dir / filename
                    
                    if self.download_image(url, save_path):
                        weed_data['images'].append(str(save_path))
                        weed_data['metadata'].append({
                            'filename': filename,
                            'source': 'google_images',
                            'query': query,
                            'weed': weed,
                            'url': url
                        })
                
                # iNaturalist search
                inaturalist_data = self.search_inaturalist(query, 15)
                for i, obs in enumerate(inaturalist_data):
                    filename = f"inat_{weed}_{i}_{hashlib.md5(obs['url'].encode()).hexdigest()[:8]}.jpg"
                    save_path = weed_dir / filename
                    
                    if self.download_image(obs['medium_url'], save_path):
                        weed_data['images'].append(str(save_path))
                        weed_data['metadata'].append({
                            'filename': filename,
                            'source': 'inaturalist',
                            'query': query,
                            'weed': weed,
                            'url': obs['url'],
                            'species': obs['species'],
                            'location': obs['location'],
                            'observed_on': obs['observed_on']
                        })
                
                time.sleep(2)
            
            results['collected_weeds'][weed] = weed_data
            results['total_images'] += len(weed_data['images'])
            
            # Save metadata
            metadata_file = weed_dir / f"{weed}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(weed_data, f, indent=2)
        
        return results

    def create_training_datasets(self):
        """Create structured training datasets from collected data"""
        
        # Create disease training dataset
        disease_csv_path = DATASETS_DIR / "disease_training_dataset.csv"
        disease_rows = []
        
        for disease_dir in DISEASE_DATA_DIR.iterdir():
            if disease_dir.is_dir():
                disease_name = disease_dir.name
                metadata_file = disease_dir / f"{disease_name}_metadata.json"
                
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    for item in metadata['metadata']:
                        disease_rows.append({
                            'image_path': item['filename'],
                            'disease': disease_name,
                            'source': item['source'],
                            'query': item['query'],
                            'full_path': str(disease_dir / item['filename'])
                        })
        
        # Save disease dataset
        with open(disease_csv_path, 'w', newline='') as f:
            if disease_rows:
                writer = csv.DictWriter(f, fieldnames=disease_rows[0].keys())
                writer.writeheader()
                writer.writerows(disease_rows)
        
        logger.info(f"Created disease training dataset: {disease_csv_path} ({len(disease_rows)} samples)")
        
        # Create weed training dataset
        weed_csv_path = DATASETS_DIR / "weed_training_dataset.csv"
        weed_rows = []
        
        for weed_dir in WEED_DATA_DIR.iterdir():
            if weed_dir.is_dir():
                weed_name = weed_dir.name
                metadata_file = weed_dir / f"{weed_name}_metadata.json"
                
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    for item in metadata['metadata']:
                        weed_rows.append({
                            'image_path': item['filename'],
                            'weed': weed_name,
                            'source': item['source'],
                            'query': item['query'],
                            'full_path': str(weed_dir / item['filename'])
                        })
        
        # Save weed dataset
        with open(weed_csv_path, 'w', newline='') as f:
            if weed_rows:
                writer = csv.DictWriter(f, fieldnames=weed_rows[0].keys())
                writer.writeheader()
                writer.writerows(weed_rows)
        
        logger.info(f"Created weed training dataset: {weed_csv_path} ({len(weed_rows)} samples)")
        
        return {
            'disease_dataset': str(disease_csv_path),
            'weed_dataset': str(weed_csv_path),
            'disease_samples': len(disease_rows),
            'weed_samples': len(weed_rows)
        }


def main():
    """Main function to run the data collection"""
    scraper = AgriculturalDataScraper()
    
    logger.info("Starting agricultural data collection...")
    
    # Collect disease data
    logger.info("Collecting disease detection data...")
    disease_results = scraper.collect_disease_data()
    logger.info(f"Collected {disease_results['total_images']} disease images")
    
    # Collect weed data
    logger.info("Collecting weed management data...")
    weed_results = scraper.collect_weed_data()
    logger.info(f"Collected {weed_results['total_images']} weed images")
    
    # Create training datasets
    logger.info("Creating training datasets...")
    dataset_info = scraper.create_training_datasets()
    
    # Save collection summary
    summary = {
        'collection_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'disease_results': disease_results,
        'weed_results': weed_results,
        'dataset_info': dataset_info
    }
    
    summary_file = DATASETS_DIR / "collection_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Data collection complete! Summary saved to {summary_file}")
    logger.info(f"Total images collected: {disease_results['total_images'] + weed_results['total_images']}")


if __name__ == "__main__":
    main()
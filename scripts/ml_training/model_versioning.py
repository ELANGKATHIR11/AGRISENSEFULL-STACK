"""
Model Versioning System for AgriSense ML Models
Implements semantic versioning for ML artifacts
"""
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import shutil


class ModelVersion:
    """
    Manages ML model versions using semantic versioning (MAJOR.MINOR.PATCH)
    
    MAJOR: Breaking changes, incompatible architecture
    MINOR: New features, improved accuracy (backward compatible)
    PATCH: Bug fixes, minor improvements
    """
    
    def __init__(self, model_type: str, base_path: Path):
        """
        Args:
            model_type: Type of model (disease, weed, water, fertilizer, chatbot)
            base_path: Base directory for model artifacts
        """
        self.model_type = model_type
        self.base_path = Path(base_path)
        self.versions_file = self.base_path / "versions.json"
        self.versions = self._load_versions()
    
    def _load_versions(self) -> Dict[str, Any]:
        """Load version registry"""
        if self.versions_file.exists():
            with open(self.versions_file, 'r') as f:
                return json.load(f)
        return {"current": None, "history": []}
    
    def _save_versions(self):
        """Save version registry"""
        self.base_path.mkdir(parents=True, exist_ok=True)
        with open(self.versions_file, 'w') as f:
            json.dump(self.versions, f, indent=2)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def create_version(
        self,
        version: str,
        artifact_paths: list[str],
        metadata: Dict[str, Any],
        is_production_ready: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new model version
        
        Args:
            version: Version string (e.g., "2.1.0")
            artifact_paths: List of file paths to version
            metadata: Model metadata (performance metrics, training info, etc.)
            is_production_ready: Whether model is ready for production
        
        Returns:
            Version info dictionary
        """
        # Validate version format
        if not self._validate_version(version):
            raise ValueError(f"Invalid version format: {version}. Use MAJOR.MINOR.PATCH")
        
        # Create version directory
        version_dir = self.base_path / f"v{version}"
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy artifacts and calculate checksums
        checksums = {}
        for artifact_path in artifact_paths:
            src = Path(artifact_path)
            if not src.exists():
                raise FileNotFoundError(f"Artifact not found: {artifact_path}")
            
            dst = version_dir / src.name
            shutil.copy2(src, dst)
            checksums[src.name] = self._calculate_checksum(dst)
        
        # Create version metadata
        version_info = {
            "version": version,
            "model_type": self.model_type,
            "created_at": datetime.utcnow().isoformat(),
            "artifacts": list(checksums.keys()),
            "checksums": checksums,
            "metadata": metadata,
            "production_ready": is_production_ready,
            "path": str(version_dir.relative_to(self.base_path))
        }
        
        # Save metadata file
        metadata_file = version_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(version_info, f, indent=2)
        
        # Update version registry
        self.versions["history"].append(version_info)
        if is_production_ready:
            self.versions["current"] = version
        self._save_versions()
        
        return version_info
    
    def get_version(self, version: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific version"""
        for v in self.versions["history"]:
            if v["version"] == version:
                return v
        return None
    
    def get_current_version(self) -> Optional[Dict[str, Any]]:
        """Get current production version"""
        current = self.versions.get("current")
        if current:
            return self.get_version(current)
        return None
    
    def list_versions(self) -> list[str]:
        """List all available versions"""
        return [v["version"] for v in self.versions["history"]]
    
    def promote_to_production(self, version: str) -> Dict[str, Any]:
        """Promote a version to production"""
        version_info = self.get_version(version)
        if not version_info:
            raise ValueError(f"Version {version} not found")
        
        old_version = self.versions.get("current")
        self.versions["current"] = version
        
        # Update production_ready flag
        for v in self.versions["history"]:
            if v["version"] == version:
                v["production_ready"] = True
                v["promoted_at"] = datetime.utcnow().isoformat()
        
        self._save_versions()
        
        return {
            "old_version": old_version,
            "new_version": version,
            "promoted_at": datetime.utcnow().isoformat()
        }
    
    def rollback(self) -> Optional[Dict[str, Any]]:
        """Rollback to previous production version"""
        # Find previous production version
        production_versions = [
            v for v in self.versions["history"]
            if v.get("production_ready") and v["version"] != self.versions.get("current")
        ]
        
        if not production_versions:
            return None
        
        # Sort by created_at and get the most recent
        production_versions.sort(key=lambda x: x["created_at"], reverse=True)
        previous = production_versions[0]
        
        old_version = self.versions.get("current")
        self.versions["current"] = previous["version"]
        self._save_versions()
        
        return {
            "rolled_back_from": old_version,
            "rolled_back_to": previous["version"],
            "rollback_at": datetime.utcnow().isoformat()
        }
    
    def verify_integrity(self, version: str) -> Dict[str, bool]:
        """Verify integrity of model artifacts using checksums"""
        version_info = self.get_version(version)
        if not version_info:
            raise ValueError(f"Version {version} not found")
        
        version_dir = self.base_path / version_info["path"]
        results = {}
        
        for artifact, expected_checksum in version_info["checksums"].items():
            artifact_path = version_dir / artifact
            if not artifact_path.exists():
                results[artifact] = False
                continue
            
            actual_checksum = self._calculate_checksum(artifact_path)
            results[artifact] = (actual_checksum == expected_checksum)
        
        return results
    
    def compare_versions(self, version1: str, version2: str) -> Dict[str, Any]:
        """Compare two versions"""
        v1 = self.get_version(version1)
        v2 = self.get_version(version2)
        
        if not v1 or not v2:
            raise ValueError("One or both versions not found")
        
        comparison = {
            "version1": version1,
            "version2": version2,
            "metadata_diff": {},
        }
        
        # Compare metadata if available
        if "metadata" in v1 and "metadata" in v2:
            m1 = v1["metadata"]
            m2 = v2["metadata"]
            
            if "performance_metrics" in m1 and "performance_metrics" in m2:
                pm1 = m1["performance_metrics"]
                pm2 = m2["performance_metrics"]
                comparison["performance_diff"] = {
                    key: {
                        "v1": pm1.get(key),
                        "v2": pm2.get(key),
                        "improvement": pm2.get(key, 0) - pm1.get(key, 0)
                    }
                    for key in set(pm1.keys()) | set(pm2.keys())
                }
        
        return comparison
    
    @staticmethod
    def _validate_version(version: str) -> bool:
        """Validate version string format (MAJOR.MINOR.PATCH)"""
        parts = version.split('.')
        if len(parts) != 3:
            return False
        return all(part.isdigit() for part in parts)
    
    @staticmethod
    def parse_version(version: str) -> tuple[int, int, int]:
        """Parse version string into (major, minor, patch)"""
        major, minor, patch = version.split('.')
        return int(major), int(minor), int(patch)
    
    @staticmethod
    def increment_version(current: str, bump: str = "patch") -> str:
        """
        Increment version number
        
        Args:
            current: Current version string
            bump: What to bump ("major", "minor", or "patch")
        
        Returns:
            New version string
        """
        major, minor, patch = ModelVersion.parse_version(current)
        
        if bump == "major":
            return f"{major + 1}.0.0"
        elif bump == "minor":
            return f"{major}.{minor + 1}.0"
        elif bump == "patch":
            return f"{major}.{minor}.{patch + 1}"
        else:
            raise ValueError(f"Invalid bump type: {bump}")


# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python model_versioning.py <command> [args]")
        print("Commands: create, list, current, promote, rollback, verify")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Example usage
    if command == "create":
        # python model_versioning.py create disease 3.3.0 path/to/model.joblib
        model_type = sys.argv[2]
        version = sys.argv[3]
        artifacts = sys.argv[4:]
        
        mv = ModelVersion(model_type, Path(f"ml_models/{model_type}"))
        info = mv.create_version(
            version=version,
            artifact_paths=artifacts,
            metadata={
                "training_date": datetime.utcnow().isoformat(),
                "performance_metrics": {}
            }
        )
        print(json.dumps(info, indent=2))
    
    elif command == "list":
        model_type = sys.argv[2]
        mv = ModelVersion(model_type, Path(f"ml_models/{model_type}"))
        print("\n".join(mv.list_versions()))
    
    elif command == "current":
        model_type = sys.argv[2]
        mv = ModelVersion(model_type, Path(f"ml_models/{model_type}"))
        current = mv.get_current_version()
        if current:
            print(json.dumps(current, indent=2))
        else:
            print("No production version set")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

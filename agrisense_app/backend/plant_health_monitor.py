#!/usr/bin/env python3
"""
Plant Health Monitor for AgriSense
Integrates disease detection and weed management for comprehensive plant health assessment
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging
from datetime import datetime, timedelta
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HERE = Path(__file__).parent

# Import our custom engines
try:
    from .disease_detection import DiseaseDetectionEngine
    from .weed_management import WeedManagementEngine
except ImportError:
    # Fallback for standalone execution
    from disease_detection import DiseaseDetectionEngine
    from weed_management import WeedManagementEngine


class PlantHealthMonitor:
    """Comprehensive plant health monitoring system"""

    def __init__(self, disease_model: str = "mobilenet_disease", weed_model: str = "weed_segmentation"):
        """
        Initialize the plant health monitor

        Args:
            disease_model: Disease detection model name
            weed_model: Weed management model name
        """
        self.disease_engine = DiseaseDetectionEngine(disease_model)
        self.weed_engine = WeedManagementEngine(weed_model)
        self.health_history = []

        logger.info("🌿 Plant Health Monitor initialized")

    def comprehensive_health_assessment(
        self,
        image_data: Union[str, bytes, Image.Image],
        field_info: Optional[Dict[str, Any]] = None,
        crop_type: str = "unknown",
        environmental_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive plant health assessment

        Args:
            image_data: Field image to analyze
            field_info: Optional field metadata (crop type, stage, etc.)
            crop_type: Type of crop being analyzed
            environmental_data: Environmental sensor data for enhanced analysis

        Returns:
            Complete health assessment results
        """
        assessment_start = datetime.now()

        try:
            # Run disease detection
            logger.info("🦠 Running disease detection...")
            disease_results = self.disease_engine.detect_disease(
                image_data=image_data, crop_type=crop_type, environmental_data=environmental_data
            )

            # Run weed management analysis
            logger.info("🌿 Running weed management analysis...")
            weed_results = self.weed_engine.detect_weeds(
                image_data=image_data, crop_type=crop_type, environmental_data=environmental_data
            )

            # Integrate results
            integrated_assessment = self._integrate_assessments(disease_results, weed_results, field_info)

            # Calculate overall health score
            health_score = self._calculate_health_score(disease_results, weed_results)

            # Generate actionable recommendations
            recommendations = self._generate_integrated_recommendations(
                disease_results, weed_results, health_score, field_info
            )

            # Risk assessment
            risk_assessment = self._comprehensive_risk_assessment(disease_results, weed_results, field_info)

            # Economic analysis
            economic_analysis = self._integrated_economic_analysis(disease_results, weed_results, field_info)

            # Monitoring plan
            monitoring_plan = self._create_monitoring_plan(disease_results, weed_results, health_score)

            assessment_duration = (datetime.now() - assessment_start).total_seconds()

            complete_assessment = {
                "assessment_id": self._generate_assessment_id(),
                "timestamp": assessment_start.isoformat(),
                "processing_time_seconds": assessment_duration,
                "overall_health_score": health_score,
                "field_info": field_info or {},
                "disease_analysis": disease_results,
                "weed_analysis": weed_results,
                "integrated_assessment": integrated_assessment,
                "recommendations": recommendations,
                "risk_assessment": risk_assessment,
                "economic_analysis": economic_analysis,
                "monitoring_plan": monitoring_plan,
                "alert_level": self._determine_alert_level(health_score, risk_assessment),
                "next_assessment_recommended": self._calculate_next_assessment_date(health_score),
            }

            # Store in history
            self.health_history.append(complete_assessment)

            logger.info(f"✅ Health assessment completed in {assessment_duration:.2f}s")
            logger.info(f"📊 Overall health score: {health_score:.1f}/100")

            return complete_assessment

        except Exception as e:
            logger.error(f"❌ Health assessment failed: {e}")
            return {"error": f"Health assessment failed: {str(e)}", "timestamp": assessment_start.isoformat()}

    def _integrate_assessments(
        self, disease_results: Dict[str, Any], weed_results: Dict[str, Any], field_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Integrate disease and weed assessment results

        Args:
            disease_results: Disease detection results
            weed_results: Weed management results
            field_info: Field metadata

        Returns:
            Integrated assessment
        """
        # Extract key metrics
        disease_confidence = disease_results.get("confidence", 0)
        disease_severity = disease_results.get("severity", "unknown")
        weed_coverage = weed_results.get("weed_coverage_percentage", 0)
        weed_pressure = weed_results.get("weed_pressure", "unknown")

        # Determine primary health concern
        primary_concern = self._identify_primary_concern(disease_results, weed_results)

        # Assess interaction effects
        interaction_effects = self._assess_interaction_effects(disease_results, weed_results)

        # Calculate stress factors
        stress_factors = self._calculate_stress_factors(disease_results, weed_results, field_info)

        # Determine intervention urgency
        intervention_urgency = self._assess_intervention_urgency(disease_results, weed_results)

        return {
            "primary_health_concern": primary_concern,
            "disease_status": {
                "detected": disease_results.get("primary_disease", "none") != "healthy",
                "severity": disease_severity,
                "confidence": disease_confidence,
            },
            "weed_status": {
                "coverage_percentage": weed_coverage,
                "pressure_level": weed_pressure,
                "management_required": weed_coverage > 5,
            },
            "interaction_effects": interaction_effects,
            "stress_factors": stress_factors,
            "intervention_urgency": intervention_urgency,
            "field_condition": self._assess_overall_field_condition(disease_results, weed_results),
        }

    def _identify_primary_concern(self, disease_results: Dict[str, Any], weed_results: Dict[str, Any]) -> str:
        """Identify the primary health concern"""
        disease_severity = disease_results.get("severity", "low")
        disease_confidence = disease_results.get("confidence", 0)
        weed_coverage = weed_results.get("weed_coverage_percentage", 0)
        weed_pressure = weed_results.get("weed_pressure", "minimal")

        # Critical disease takes priority
        if disease_severity == "critical" and disease_confidence > 0.8:
            return "critical_disease"

        # Severe weed infestation
        if weed_pressure == "severe" or weed_coverage > 25:
            return "severe_weed_infestation"

        # High disease pressure
        if disease_severity in ["high", "critical"] and disease_confidence > 0.6:
            return "disease_outbreak"

        # Moderate weed pressure
        if weed_pressure in ["high", "moderate"] or weed_coverage > 10:
            return "weed_competition"

        # Low-level issues
        if disease_severity == "medium" or weed_coverage > 5:
            return "routine_management"

        return "healthy_field"

    def _assess_interaction_effects(
        self, disease_results: Dict[str, Any], weed_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess interactions between disease and weed issues"""
        disease_present = disease_results.get("primary_disease", "healthy") != "healthy"
        weed_coverage = weed_results.get("weed_coverage_percentage", 0)

        interactions = {
            "disease_weed_synergy": False,
            "competition_stress": False,
            "treatment_conflicts": [],
            "compounding_factors": [],
        }

        # Disease-weed synergy
        if disease_present and weed_coverage > 10:
            interactions["disease_weed_synergy"] = True
            interactions["compounding_factors"].append("Weakened plants more susceptible to disease")
            interactions["compounding_factors"].append("Weed competition reduces plant immunity")

        # Competition stress
        if weed_coverage > 15:
            interactions["competition_stress"] = True
            interactions["compounding_factors"].append("Nutrient competition from weeds")
            interactions["compounding_factors"].append("Water stress from weed competition")

        # Treatment conflicts
        if disease_present and weed_coverage > 5:
            interactions["treatment_conflicts"].extend(
                [
                    "Timing herbicide application around disease treatment",
                    "Avoid plant stress during disease recovery",
                    "Consider integrated treatment approach",
                ]
            )

        return interactions

    def _calculate_stress_factors(
        self, disease_results: Dict[str, Any], weed_results: Dict[str, Any], field_info: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate various plant stress factors"""
        stress_factors = {
            "disease_stress": 0.0,
            "competition_stress": 0.0,
            "environmental_stress": 0.0,
            "management_stress": 0.0,
        }

        # Disease stress
        disease_severity = disease_results.get("severity", "low")
        disease_confidence = disease_results.get("confidence", 0)

        severity_scores = {"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0}
        stress_factors["disease_stress"] = severity_scores.get(disease_severity, 0) * disease_confidence

        # Competition stress from weeds
        weed_coverage = weed_results.get("weed_coverage_percentage", 0)
        stress_factors["competition_stress"] = min(weed_coverage / 30, 1.0)  # Max at 30% coverage

        # Environmental stress (if weather data available)
        if field_info and "weather" in field_info:
            weather = field_info["weather"]
            temp_stress = self._calculate_temperature_stress(weather.get("temperature"))
            moisture_stress = self._calculate_moisture_stress(weather.get("humidity"))
            stress_factors["environmental_stress"] = max(temp_stress, moisture_stress)

        # Management stress (treatment burden)
        disease_treatment_needed = disease_results.get("severity") in ["high", "critical"]
        weed_treatment_needed = weed_coverage > 10

        if disease_treatment_needed and weed_treatment_needed:
            stress_factors["management_stress"] = 0.8
        elif disease_treatment_needed or weed_treatment_needed:
            stress_factors["management_stress"] = 0.4

        return stress_factors

    def _calculate_temperature_stress(self, temperature: Optional[float]) -> float:
        """Calculate temperature stress factor"""
        if temperature is None:
            return 0.0

        # Optimal range 20-25°C, stress increases outside this range
        if 20 <= temperature <= 25:
            return 0.0
        elif 15 <= temperature < 20 or 25 < temperature <= 30:
            return 0.3
        elif 10 <= temperature < 15 or 30 < temperature <= 35:
            return 0.6
        else:
            return 1.0

    def _calculate_moisture_stress(self, humidity: Optional[float]) -> float:
        """Calculate moisture stress factor"""
        if humidity is None:
            return 0.0

        # Optimal range 60-80%, stress at extremes
        if 60 <= humidity <= 80:
            return 0.0
        elif 40 <= humidity < 60 or 80 < humidity <= 90:
            return 0.3
        elif 20 <= humidity < 40 or 90 < humidity <= 95:
            return 0.6
        else:
            return 1.0

    def _assess_intervention_urgency(
        self, disease_results: Dict[str, Any], weed_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess urgency of intervention needed"""
        disease_severity = disease_results.get("severity", "low")
        disease_results.get("risk_level", "low")
        weed_pressure = weed_results.get("weed_pressure", "minimal")
        weed_coverage = weed_results.get("weed_coverage_percentage", 0)

        urgency_score = 0
        urgency_factors = []

        # Disease urgency
        if disease_severity == "critical":
            urgency_score += 40
            urgency_factors.append("Critical disease detected")
        elif disease_severity == "high":
            urgency_score += 25
            urgency_factors.append("High disease severity")
        elif disease_severity == "medium":
            urgency_score += 10

        # Weed urgency
        if weed_pressure == "severe":
            urgency_score += 30
            urgency_factors.append("Severe weed infestation")
        elif weed_pressure == "high":
            urgency_score += 20
            urgency_factors.append("High weed pressure")
        elif weed_coverage > 15:
            urgency_score += 15
            urgency_factors.append("Significant weed coverage")

        # Determine urgency level
        if urgency_score >= 50:
            urgency_level = "immediate"
            timeline = "within 24 hours"
        elif urgency_score >= 30:
            urgency_level = "urgent"
            timeline = "within 3 days"
        elif urgency_score >= 15:
            urgency_level = "moderate"
            timeline = "within 1 week"
        else:
            urgency_level = "routine"
            timeline = "within 2 weeks"

        return {
            "urgency_level": urgency_level,
            "urgency_score": urgency_score,
            "intervention_timeline": timeline,
            "urgency_factors": urgency_factors,
        }

    def _assess_overall_field_condition(self, disease_results: Dict[str, Any], weed_results: Dict[str, Any]) -> str:
        """Assess overall field condition"""
        disease_severity = disease_results.get("severity", "low")
        weed_coverage = weed_results.get("weed_coverage_percentage", 0)

        if disease_severity == "critical" or weed_coverage > 30:
            return "poor"
        elif disease_severity in ["high", "medium"] or weed_coverage > 15:
            return "fair"
        elif disease_severity == "low" and weed_coverage > 5:
            return "good"
        else:
            return "excellent"

    def _calculate_health_score(self, disease_results: Dict[str, Any], weed_results: Dict[str, Any]) -> float:
        """
        Calculate overall plant health score (0-100)

        Args:
            disease_results: Disease detection results
            weed_results: Weed management results

        Returns:
            Health score from 0 (critical) to 100 (perfect health)
        """
        base_score = 100.0

        # Disease impact
        disease_severity = disease_results.get("severity", "low")
        disease_confidence = disease_results.get("confidence", 0)

        severity_penalties = {"low": 5, "medium": 15, "high": 30, "critical": 50}
        disease_penalty = severity_penalties.get(disease_severity, 0) * disease_confidence

        # Weed impact
        weed_coverage = weed_results.get("weed_coverage_percentage", 0)
        weed_penalty = min(weed_coverage * 1.5, 40)  # Max 40 point penalty for weeds

        # Calculate final score
        health_score = base_score - disease_penalty - weed_penalty

        # Ensure score is within valid range
        return max(0.0, min(100.0, health_score))

    def _generate_integrated_recommendations(
        self,
        disease_results: Dict[str, Any],
        weed_results: Dict[str, Any],
        health_score: float,
        field_info: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate integrated management recommendations"""
        recommendations = {
            "immediate_actions": [],
            "short_term_plan": [],
            "long_term_strategy": [],
            "treatment_sequence": [],
            "monitoring_priorities": [],
            "prevention_measures": [],
        }

        disease_present = disease_results.get("severity") in ["medium", "high", "critical"]
        weed_management_needed = weed_results.get("weed_coverage_percentage", 0) > 8

        # Immediate actions
        if health_score < 50:
            recommendations["immediate_actions"].extend(
                [
                    "Emergency field assessment required",
                    "Document current conditions thoroughly",
                    "Prepare for intensive management intervention",
                ]
            )

        if disease_present and weed_management_needed:
            # Integrated approach needed
            recommendations["immediate_actions"].append("Implement integrated pest management strategy")
            recommendations["treatment_sequence"].extend(
                [
                    "1. Address critical disease issues first",
                    "2. Apply selective weed control measures",
                    "3. Monitor plant recovery",
                    "4. Adjust treatments based on response",
                ]
            )
        elif disease_present:
            # Focus on disease
            disease_treatments = disease_results.get("treatment_recommendations", {})
            immediate_treatments = disease_treatments.get("immediate", [])
            recommendations["immediate_actions"].extend(immediate_treatments)
        elif weed_management_needed:
            # Focus on weeds
            weed_plan = weed_results.get("management_recommendations", {})
            immediate_weed_actions = weed_plan.get("immediate_actions", [])
            recommendations["immediate_actions"].extend(immediate_weed_actions)

        # Short-term plan (1-4 weeks)
        recommendations["short_term_plan"].extend(
            [
                "Monitor treatment effectiveness",
                "Adjust irrigation based on plant stress",
                "Document recovery progress",
                "Prepare for follow-up treatments if needed",
            ]
        )

        # Long-term strategy
        recommendations["long_term_strategy"].extend(
            [
                "Develop field-specific management protocol",
                "Plan crop rotation to break pest cycles",
                "Invest in early detection systems",
                "Build soil health for natural resistance",
            ]
        )

        # Monitoring priorities
        if disease_present:
            recommendations["monitoring_priorities"].extend(
                ["Daily disease symptom assessment", "Treatment efficacy evaluation", "Weather impact monitoring"]
            )

        if weed_management_needed:
            recommendations["monitoring_priorities"].extend(
                ["Weed regrowth tracking", "Herbicide resistance monitoring", "Coverage percentage measurements"]
            )

        return recommendations

    def _comprehensive_risk_assessment(
        self, disease_results: Dict[str, Any], weed_results: Dict[str, Any], field_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform comprehensive risk assessment"""
        risks = {
            "immediate_risks": [],
            "medium_term_risks": [],
            "long_term_risks": [],
            "risk_factors": {},
            "mitigation_strategies": [],
        }

        # Disease risks
        disease_risk = disease_results.get("risk_level", "low")
        if disease_risk in ["high", "critical"]:
            risks["immediate_risks"].append("Disease outbreak potential")
            risks["mitigation_strategies"].append("Implement disease management protocol")

        # Weed risks
        weed_pressure = weed_results.get("weed_pressure", "minimal")
        if weed_pressure in ["high", "severe"]:
            risks["immediate_risks"].append("Yield loss from weed competition")
            risks["mitigation_strategies"].append("Aggressive weed control measures")

        # Economic risks
        disease_impact = disease_results.get("economic_impact", {})
        weed_impact = weed_results.get("economic_impact", {})

        disease_loss = disease_impact.get("potential_loss_percent", {})
        weed_loss = weed_impact.get("estimated_yield_loss", {})

        if isinstance(disease_loss, dict):
            max_disease_loss = disease_loss.get("max", 0)
        else:
            max_disease_loss = 0

        if isinstance(weed_loss, dict):
            max_weed_loss = weed_loss.get("maximum_percent", 0)
        else:
            max_weed_loss = 0

        total_potential_loss = max_disease_loss + max_weed_loss

        if total_potential_loss > 30:
            risks["immediate_risks"].append("Severe economic loss potential")
        elif total_potential_loss > 15:
            risks["medium_term_risks"].append("Significant economic impact")

        # Environmental risks
        if field_info and "weather" in field_info:
            weather = field_info["weather"]
            if weather.get("humidity", 0) > 85:
                risks["medium_term_risks"].append("High humidity favoring disease development")

        return risks

    def _integrated_economic_analysis(
        self, disease_results: Dict[str, Any], weed_results: Dict[str, Any], field_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Integrated economic impact analysis"""
        disease_impact = disease_results.get("economic_impact", {})
        weed_impact = weed_results.get("economic_impact", {})

        # Extract yield loss estimates
        disease_loss = disease_impact.get("potential_loss_percent", {})
        weed_loss = weed_impact.get("estimated_yield_loss", {})

        if isinstance(disease_loss, dict):
            disease_min = disease_loss.get("min", 0)
            disease_max = disease_loss.get("max", 0)
        else:
            disease_min = disease_max = 0

        if isinstance(weed_loss, dict):
            weed_min = weed_loss.get("minimum_percent", 0)
            weed_max = weed_loss.get("maximum_percent", 0)
        else:
            weed_min = weed_max = 0

        # Combined impact (not simply additive due to interactions)
        combined_min = disease_min + weed_min * 0.8  # Reduced weed impact when disease present
        combined_max = disease_max + weed_max * 0.9

        # Treatment costs
        disease_treatment_cost = disease_impact.get("treatment_cost_level", "minimal")
        weed_treatment_cost = weed_impact.get("treatment_cost_per_acre", {})

        cost_levels = {"minimal": 10, "low": 25, "medium": 50, "high": 100}
        total_treatment_cost = cost_levels.get(disease_treatment_cost, 25)

        if isinstance(weed_treatment_cost, dict):
            total_treatment_cost += weed_treatment_cost.get("herbicide", 0)

        return {
            "total_yield_loss_estimate": {
                "minimum_percent": combined_min,
                "maximum_percent": combined_max,
                "expected_percent": (combined_min + combined_max) / 2,
            },
            "total_treatment_cost_per_acre": total_treatment_cost,
            "cost_benefit_analysis": {
                "treatment_justified": combined_max > (total_treatment_cost / 10),  # Rough calculation
                "roi_potential": "high" if combined_max > 20 else "medium" if combined_max > 10 else "low",
            },
            "economic_priority": "critical" if combined_max > 25 else "high" if combined_max > 15 else "medium",
        }

    def _create_monitoring_plan(
        self, disease_results: Dict[str, Any], weed_results: Dict[str, Any], health_score: float
    ) -> Dict[str, Any]:
        """Create integrated monitoring plan"""
        disease_results.get("monitoring_suggestions", [])
        weed_results.get("monitoring_schedule", {})

        # Determine monitoring frequency based on health score
        if health_score < 50:
            base_frequency = "daily"
            duration_days = 14
        elif health_score < 70:
            base_frequency = "every_2_days"
            duration_days = 21
        elif health_score < 85:
            base_frequency = "twice_weekly"
            duration_days = 30
        else:
            base_frequency = "weekly"
            duration_days = 45

        monitoring_checklist = []

        # Disease monitoring items
        if disease_results.get("severity") in ["medium", "high", "critical"]:
            monitoring_checklist.extend(
                ["Disease symptom progression", "Treatment effectiveness", "New infection sites"]
            )

        # Weed monitoring items
        if weed_results.get("weed_coverage_percentage", 0) > 5:
            monitoring_checklist.extend(["Weed coverage changes", "New weed emergence", "Herbicide effectiveness"])

        # Standard items
        monitoring_checklist.extend(["Overall plant vigor", "Environmental conditions", "Photo documentation"])

        return {
            "monitoring_frequency": base_frequency,
            "monitoring_duration_days": duration_days,
            "monitoring_checklist": monitoring_checklist,
            "key_metrics_to_track": [
                "Health score trend",
                "Disease severity changes",
                "Weed coverage percentage",
                "Treatment response",
            ],
            "alert_thresholds": {
                "health_score_drop": 10,
                "disease_severity_increase": True,
                "weed_coverage_increase": 5,
            },
        }

    def _determine_alert_level(self, health_score: float, risk_assessment: Dict[str, Any]) -> str:
        """Determine appropriate alert level"""
        immediate_risks = len(risk_assessment.get("immediate_risks", []))

        if health_score < 40 or immediate_risks >= 3:
            return "critical"
        elif health_score < 60 or immediate_risks >= 2:
            return "high"
        elif health_score < 80 or immediate_risks >= 1:
            return "medium"
        else:
            return "low"

    def _calculate_next_assessment_date(self, health_score: float) -> str:
        """Calculate when next assessment should be performed"""
        if health_score < 50:
            days_ahead = 1
        elif health_score < 70:
            days_ahead = 3
        elif health_score < 85:
            days_ahead = 7
        else:
            days_ahead = 14

        next_date = datetime.now() + timedelta(days=days_ahead)
        return next_date.isoformat()

    def _generate_assessment_id(self) -> str:
        """Generate unique assessment ID"""
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"PHM_{timestamp}_{len(self.health_history):04d}"

    def get_health_trends(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Analyze health trends from historical assessments

        Args:
            days_back: Number of days to analyze

        Returns:
            Trend analysis
        """
        if not self.health_history:
            return {"error": "No historical data available"}

        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_assessments = [
            assessment
            for assessment in self.health_history
            if datetime.fromisoformat(assessment["timestamp"]) >= cutoff_date
        ]

        if not recent_assessments:
            return {"error": f"No assessments found in last {days_back} days"}

        # Extract health scores
        health_scores = [assessment["overall_health_score"] for assessment in recent_assessments]

        # Calculate trend
        if len(health_scores) >= 2:
            trend_direction = (
                "improving"
                if health_scores[-1] > health_scores[0]
                else "declining" if health_scores[-1] < health_scores[0] else "stable"
            )
        else:
            trend_direction = "insufficient_data"

        return {
            "assessment_count": len(recent_assessments),
            "date_range": {"start": recent_assessments[0]["timestamp"], "end": recent_assessments[-1]["timestamp"]},
            "health_score_trend": {
                "direction": trend_direction,
                "current_score": health_scores[-1],
                "average_score": sum(health_scores) / len(health_scores),
                "min_score": min(health_scores),
                "max_score": max(health_scores),
            },
            "trend_analysis": self._analyze_specific_trends(recent_assessments),
        }

    def _analyze_specific_trends(self, assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze specific health parameter trends"""
        disease_severities = []
        weed_coverages = []
        alert_levels = []

        for assessment in assessments:
            disease_analysis = assessment.get("disease_analysis", {})
            weed_analysis = assessment.get("weed_analysis", {})

            disease_severities.append(disease_analysis.get("severity", "unknown"))
            weed_coverages.append(weed_analysis.get("weed_coverage_percentage", 0))
            alert_levels.append(assessment.get("alert_level", "low"))

        return {
            "disease_trend": self._categorize_trend(disease_severities),
            "weed_trend": "increasing" if weed_coverages[-1] > weed_coverages[0] else "decreasing",
            "alert_frequency": {level: alert_levels.count(level) for level in set(alert_levels)},
            "recommendations": self._generate_trend_recommendations(assessments),
        }

    def _categorize_trend(self, severity_list: List[str]) -> str:
        """Categorize disease severity trend"""
        severity_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4, "unknown": 0}
        scores = [severity_scores.get(s, 0) for s in severity_list]

        if len(scores) < 2:
            return "insufficient_data"

        if scores[-1] > scores[0]:
            return "worsening"
        elif scores[-1] < scores[0]:
            return "improving"
        else:
            return "stable"

    def _generate_trend_recommendations(self, assessments: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on trends"""
        recommendations = []

        if len(assessments) >= 3:
            recent_scores = [a["overall_health_score"] for a in assessments[-3:]]
            if all(recent_scores[i] < recent_scores[i - 1] for i in range(1, len(recent_scores))):
                recommendations.append("Health score declining - investigate underlying causes")

        # Check for recurring issues
        disease_issues = sum(
            1 for a in assessments if a.get("disease_analysis", {}).get("severity") in ["high", "critical"]
        )
        if disease_issues > len(assessments) * 0.5:
            recommendations.append("Recurring disease issues - consider resistant varieties")

        weed_issues = sum(1 for a in assessments if a.get("weed_analysis", {}).get("weed_coverage_percentage", 0) > 15)
        if weed_issues > len(assessments) * 0.3:
            recommendations.append("Persistent weed pressure - review management strategy")

        return recommendations


def main():
    """Test the plant health monitor"""
    print("🌿 Testing Plant Health Monitor")
    print("=" * 50)

    # Initialize monitor
    monitor = PlantHealthMonitor()

    # Test comprehensive assessment
    print("\n🧪 Running comprehensive health assessment...")

    # Mock field info
    field_info = {
        "crop_type": "tomato",
        "growth_stage": "flowering",
        "field_size_acres": 5.2,
        "weather": {"temperature": 28, "humidity": 75},
    }

    # Run assessment
    assessment = monitor.comprehensive_health_assessment("mock_image_path", field_info)

    if "error" not in assessment:
        print(f"📊 Assessment ID: {assessment['assessment_id']}")
        print(f"⚡ Processing Time: {assessment['processing_time_seconds']:.2f}s")
        print(f"❤️ Health Score: {assessment['overall_health_score']:.1f}/100")
        print(f"🚨 Alert Level: {assessment['alert_level']}")

        print("\n🔍 Integrated Assessment:")
        integrated = assessment["integrated_assessment"]
        print(f"  Primary Concern: {integrated['primary_health_concern']}")
        print(f"  Field Condition: {integrated['field_condition']}")
        print(f"  Intervention Urgency: {integrated['intervention_urgency']['urgency_level']}")

        print("\n💡 Key Recommendations:")
        recommendations = assessment["recommendations"]
        for action in recommendations["immediate_actions"][:3]:
            print(f"  • {action}")

        print("\n💰 Economic Analysis:")
        economic = assessment["economic_analysis"]
        yield_loss = economic["total_yield_loss_estimate"]
        print(f"  Expected Yield Loss: {yield_loss['expected_percent']:.1f}%")
        print(f"  Treatment Cost: ${economic['total_treatment_cost_per_acre']:.2f}/acre")
        print(f"  Economic Priority: {economic['economic_priority']}")

        print("\n📅 Monitoring Plan:")
        monitoring = assessment["monitoring_plan"]
        print(f"  Frequency: {monitoring['monitoring_frequency']}")
        print(f"  Duration: {monitoring['monitoring_duration_days']} days")
        print(f"  Next Assessment: {assessment['next_assessment_recommended']}")

    else:
        print(f"❌ Assessment failed: {assessment['error']}")

    print("\n✅ Plant Health Monitor test completed!")


if __name__ == "__main__":
    main()

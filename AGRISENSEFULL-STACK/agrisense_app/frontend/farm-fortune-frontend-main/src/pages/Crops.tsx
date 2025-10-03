import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Search, Wheat, Droplets, Thermometer, Sun, Calendar, TrendingUp } from "lucide-react";

import { api, type CropCard } from "@/lib/api";
import { useTranslation } from "react-i18next";

const Crops = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [crops, setCrops] = useState<CropCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { t } = useTranslation();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await api.crops();
        if (!cancelled) {
          setCrops(res.items);
          console.log('Loaded crops:', res.items.length);
        }
      } catch (err) {
        if (!cancelled) {
          const errorMessage = err instanceof Error ? err.message : 'Failed to load crops';
          setError(errorMessage);
          console.error('Failed to load crops:', err);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true };
  }, []);

  const categories = useMemo(() => {
    const set = new Set<string>(["all"]);
    for (const c of crops) {
      if (c.category) set.add(c.category);
    }
    return Array.from(set);
  }, [crops]);

  const filteredCrops = useMemo(() => {
    const term = searchTerm.toLowerCase();
    return crops.filter(crop => {
      const nameHit = crop.name.toLowerCase().includes(term);
      const sci = (crop.scientificName || "").toLowerCase();
      const sciHit = sci.includes(term);
      const matchesCategory = selectedCategory === "all" || crop.category === selectedCategory;
      return (nameHit || sciHit) && matchesCategory;
    });
  }, [crops, searchTerm, selectedCategory]);

  const getWaterColor = (requirement: string | null | undefined) => {
    switch (requirement) {
      case "High": return "bg-primary text-primary-foreground";
      case "Medium": return "bg-accent text-accent-foreground";
      case "Low": return "bg-secondary text-secondary-foreground";
      default: return "bg-muted text-muted-foreground";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-secondary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">{t("nav_crops")}</h1>
          <p className="text-muted-foreground">{t("crops_browse_subtitle")}</p>
        </div>

        {/* Search and Filter */}
        <div className="mb-8">
          <Card className="shadow-medium">
            <CardContent className="pt-6">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder={t("search_crops_placeholder")}
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <div className="flex gap-2">
                  {categories.map((category) => (
                    <Button
                      key={category}
                      variant={selectedCategory === category ? "default" : "outline"}
                      size="sm"
                      onClick={() => setSelectedCategory(category)}
                      className={selectedCategory === category ? "bg-gradient-primary" : ""}
                    >
                      {category === "all" ? t("all_crops") : category}
                    </Button>
                  ))}
                </div>
              </div>
              <div className="mt-3 text-xs text-muted-foreground text-right">
                {t("showing_n_of_m").replace("{n}", String(filteredCrops.length)).replace("{m}", String(crops.length))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Crop Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCrops.map((crop) => (
            <Card key={crop.id} className="shadow-medium hover:shadow-strong transition-smooth">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2">
                    <Wheat className="w-5 h-5 text-primary" />
                    <div>
                      <CardTitle className="text-lg">{crop.name}</CardTitle>
                      <CardDescription className="text-xs italic">
                        {crop.scientificName}
                      </CardDescription>
                    </div>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {crop.category}
                  </Badge>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-4">
                {/* Description */}
                <p className="text-sm text-muted-foreground">{crop.description}</p>

                {/* Growing Conditions */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex items-center space-x-2 text-sm">
                    <Droplets className="w-4 h-4 text-primary" />
                    <span className="text-muted-foreground">{t("water_label")}:</span>
                    <Badge className={`text-xs ${getWaterColor(crop.waterRequirement)}`}>
                      {crop.waterRequirement}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center space-x-2 text-sm">
                    <Sun className="w-4 h-4 text-primary" />
                    <span className="text-muted-foreground">{t("season")}:</span>
                    <span className="font-medium text-foreground">{crop.season}</span>
                  </div>

                  <div className="flex items-center space-x-2 text-sm">
                    <Thermometer className="w-4 h-4 text-primary" />
                    <span className="text-muted-foreground">{t("temp_short")}:</span>
                    <span className="font-medium text-foreground">{crop.tempRange}</span>
                  </div>

                  <div className="flex items-center space-x-2 text-sm">
                    <TrendingUp className="w-4 h-4 text-primary" />
                    <span className="text-muted-foreground">{t("ph_short")}:</span>
                    <span className="font-medium text-foreground">{crop.phRange}</span>
                  </div>
                </div>

                {/* Growth Period */}
                <div className="flex items-center space-x-2 text-sm bg-accent rounded-lg p-2">
                  <Calendar className="w-4 h-4 text-accent-foreground" />
                  <span className="text-accent-foreground">{t("growth_period")}: {crop.growthPeriod}</span>
                </div>

                {/* Growing Tips */}
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-foreground">{t("growing_tips")}</h4>
                  <ul className="space-y-1">
                    {crop.tips.map((tip, index) => (
                      <li key={index} className="text-xs text-muted-foreground flex items-center space-x-2">
                        <div className="w-1 h-1 bg-primary rounded-full flex-shrink-0" />
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* No Results */}
        {!loading && !error && filteredCrops.length === 0 && (
          <div className="text-center py-12">
            <Wheat className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">{t("no_crops_found")}</h3>
            <p className="text-muted-foreground">{t("try_adjusting_search")}</p>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <h3 className="text-lg font-semibold text-foreground mb-2">Loading crops...</h3>
            <p className="text-muted-foreground">Please wait while we fetch the crop data</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="text-center py-12">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-red-600 text-xl">⚠️</span>
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">Failed to load crops</h3>
            <p className="text-muted-foreground mb-4">{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
            >
              Retry
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Crops;
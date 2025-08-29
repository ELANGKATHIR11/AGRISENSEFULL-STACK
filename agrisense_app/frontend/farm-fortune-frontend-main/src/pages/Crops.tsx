import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Search, Wheat, Droplets, Thermometer, Sun, Calendar, TrendingUp } from "lucide-react";

interface Crop {
  id: string;
  name: string;
  scientificName: string;
  category: string;
  season: string;
  waterRequirement: "Low" | "Medium" | "High";
  tempRange: string;
  phRange: string;
  growthPeriod: string;
  description: string;
  tips: string[];
}

const Crops = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");

  // Mock crop data
  const crops: Crop[] = [
    {
      id: "1",
      name: "Wheat",
      scientificName: "Triticum aestivum",
      category: "Cereal",
      season: "Winter",
      waterRequirement: "Medium",
      tempRange: "15-25°C",
      phRange: "6.0-7.5",
      growthPeriod: "120-150 days",
      description: "A cereal grain that is a worldwide staple food and one of the most important crops.",
      tips: ["Plant in well-drained soil", "Requires full sun exposure", "Monitor for rust diseases"]
    },
    {
      id: "2", 
      name: "Corn",
      scientificName: "Zea mays",
      category: "Cereal",
      season: "Summer",
      waterRequirement: "High",
      tempRange: "20-30°C",
      phRange: "6.0-6.8",
      growthPeriod: "90-120 days",
      description: "A large grain plant domesticated by indigenous peoples in Mesoamerica.",
      tips: ["Needs warm weather", "Deep watering required", "Rich, fertile soil preferred"]
    },
    {
      id: "3",
      name: "Rice",
      scientificName: "Oryza sativa",
      category: "Cereal",
      season: "Monsoon",
      waterRequirement: "High",
      tempRange: "22-32°C", 
      phRange: "5.5-7.0",
      growthPeriod: "105-150 days",
      description: "A staple food crop for over half of the world's population.",
      tips: ["Flooded field cultivation", "Warm, humid climate", "Regular water management"]
    },
    {
      id: "4",
      name: "Tomato",
      scientificName: "Solanum lycopersicum",
      category: "Vegetable",
      season: "Summer",
      waterRequirement: "Medium",
      tempRange: "18-27°C",
      phRange: "6.0-6.8",
      growthPeriod: "70-100 days",
      description: "A widely consumed vegetable rich in vitamins and antioxidants.",
      tips: ["Support with stakes", "Consistent watering", "Mulch around plants"]
    },
    {
      id: "5",
      name: "Potato",
      scientificName: "Solanum tuberosum",
      category: "Vegetable",
      season: "Winter",
      waterRequirement: "Medium",
      tempRange: "15-20°C",
      phRange: "5.0-6.5",
      growthPeriod: "70-120 days",
      description: "A starchy tuber that is the world's fourth-largest food crop.",
      tips: ["Hill soil around plants", "Avoid overwatering", "Harvest before frost"]
    },
    {
      id: "6",
      name: "Soybean",
      scientificName: "Glycine max",
      category: "Legume",
      season: "Summer",
      waterRequirement: "Medium",
      tempRange: "20-30°C",
      phRange: "6.0-7.0",
      growthPeriod: "90-150 days",
      description: "A species of legume that is an important source of protein and oil.",
      tips: ["Nitrogen-fixing crop", "Rotate with cereals", "Avoid waterlogged soil"]
    }
  ];

  const categories = ["all", "Cereal", "Vegetable", "Legume", "Fruit"];

  const filteredCrops = crops.filter(crop => {
    const matchesSearch = crop.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         crop.scientificName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === "all" || crop.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const getWaterColor = (requirement: string) => {
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
          <h1 className="text-3xl font-bold text-foreground mb-2">Crop Database</h1>
          <p className="text-muted-foreground">Browse our comprehensive crop library with growing requirements and tips</p>
        </div>

        {/* Search and Filter */}
        <div className="mb-8">
          <Card className="shadow-medium">
            <CardContent className="pt-6">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Search crops by name or scientific name..."
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
                      {category === "all" ? "All Crops" : category}
                    </Button>
                  ))}
                </div>
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
                    <span className="text-muted-foreground">Water:</span>
                    <Badge className={`text-xs ${getWaterColor(crop.waterRequirement)}`}>
                      {crop.waterRequirement}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center space-x-2 text-sm">
                    <Sun className="w-4 h-4 text-primary" />
                    <span className="text-muted-foreground">Season:</span>
                    <span className="font-medium text-foreground">{crop.season}</span>
                  </div>

                  <div className="flex items-center space-x-2 text-sm">
                    <Thermometer className="w-4 h-4 text-primary" />
                    <span className="text-muted-foreground">Temp:</span>
                    <span className="font-medium text-foreground">{crop.tempRange}</span>
                  </div>

                  <div className="flex items-center space-x-2 text-sm">
                    <TrendingUp className="w-4 h-4 text-primary" />
                    <span className="text-muted-foreground">pH:</span>
                    <span className="font-medium text-foreground">{crop.phRange}</span>
                  </div>
                </div>

                {/* Growth Period */}
                <div className="flex items-center space-x-2 text-sm bg-accent rounded-lg p-2">
                  <Calendar className="w-4 h-4 text-accent-foreground" />
                  <span className="text-accent-foreground">Growth Period: {crop.growthPeriod}</span>
                </div>

                {/* Growing Tips */}
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-foreground">Growing Tips:</h4>
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
        {filteredCrops.length === 0 && (
          <div className="text-center py-12">
            <Wheat className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">No crops found</h3>
            <p className="text-muted-foreground">Try adjusting your search terms or category filter</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Crops;
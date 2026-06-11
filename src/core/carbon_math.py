class CarbonMath:
    """
    Standalone engine responsible for converting raw hardware metrics 
    (CPU cores, execution time) into carbon emissions estimations (grams of CO2).
    """
    WATTAGE_PER_CORE = 10.0  # Estimated average watts consumed by a modern cloud CPU core
    AZURE_PUE = 1.15         # Power Usage Effectiveness of an efficient Azure datacenter
    GRID_INTENSITY_G_KWH = 350.0  # Regional average grid carbon intensity (grams CO2 per kWh)

    @classmethod
    def calculate_cluster_co2(cls, active_cores: float, duration_hours: float = 24.0) -> float:
        """Computes carbon footprint for a cluster running continuously at a given core load."""
        if active_cores <= 0:
            return 0.0
        
        # Power consumed by cores (kWh) = (Cores * Watts * Hours) / 1000
        energy_kwh = (active_cores * cls.WATTAGE_PER_CORE * duration_hours) / 1000.0
        
        # Include datacenter cooling/overhead via PUE multiplier
        total_energy_kwh = energy_kwh * cls.AZURE_PUE
        
        # Convert energy to carbon grams
        return round(total_energy_kwh * cls.GRID_INTENSITY_G_KWH, 3)

    @classmethod
    def calculate_pipeline_co2(cls, duration_seconds: float, runners: int = 1) -> float:
        """Computes carbon footprint for a transient CI/CD pipeline execution."""
        if duration_seconds <= 0:
            return 0.0
        
        # Map seconds to hours
        duration_hours = duration_seconds / 3600.0
        
        # Assume a standard build runner provisions an average of 2 cores
        assumed_cores = 2.0 * runners
        
        return cls.calculate_cluster_co2(active_cores=assumed_cores, duration_hours=duration_hours)
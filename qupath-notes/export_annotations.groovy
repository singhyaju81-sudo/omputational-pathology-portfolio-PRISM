// Export all QuPath annotation objects to GeoJSON (full-resolution pixel coords).
// Run via: Automate -> Script editor -> paste -> Run.
// Prints how many objects were found (per class) BEFORE writing, so you can
// confirm all classes were caught. Writes to your home folder.

def annotations = getAnnotationObjects()
println "Found ${annotations.size()} objects:"
annotations.each { println "  - " + (it.getPathClass() ?: "unclassified") }

def path = System.getProperty("user.home") + "/regions_all.geojson"
exportObjectsToGeoJson(annotations, path, "FEATURE_COLLECTION")
println "SAVED: " + path

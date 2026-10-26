import Foundation
import CoreLocation
import UIKit

/// `-screenshot <name>` opens one screen with fixed state for App Store screenshots (scripts/capture-screenshots.sh).
/// Names: home, eastern_bbq, lexington_bbq, hot_dogs, honors, inspections, detail, map, saved, about.
enum ScreenshotMode {
    /// Debug builds only: an App Store build ignores the launch argument, so no one can reach seeded screens or fake locations.
    static var name: String? {
        #if DEBUG
        let args = ProcessInfo.processInfo.arguments
        guard let i = args.firstIndex(of: "-screenshot"), i + 1 < args.count else { return nil }
        return args[i + 1]
        #else
        return nil
        #endif
    }
    static var isActive: Bool { name != nil }

    @MainActor
    static func apply(to model: AppModel) {
        guard let name, model.isLoaded else { return }
        model.filters = Filters()
        // downtown Raleigh (Fayetteville St at Martin St), so "nearest" lists have distances without a permission prompt
        model.screenshotLocation = CLLocation(latitude: 35.7774, longitude: -78.6386)
        // by name and town, ignoring case, so a rebuild with a slightly different casing still finds the place; the hand-checked one first
        let pick = { (n: String, town: String?) -> Place? in
            let hits = model.places.filter { $0.name.caseInsensitiveCompare(n) == .orderedSame && (town == nil || $0.city == town) }
            return hits.first(where: \.handChecked) ?? hits.first
        }
        for p in [pick("Sam Jones BBQ", "Raleigh"), pick("Lexington Barbecue", "Lexington"), pick("Beck's Restaurant", "Calabash")]
            .compactMap({ $0 }) where !model.isSaved(p) {
            model.toggleSaved(p)
        }
        let open = { (g: Guide) in model.tab = .guides; model.selectedGuide = g; model.guidesPath = [.guide(g)] }
        switch name {
        case "eastern_bbq":
            // from Greenville (Evans St at 5th St), between Ayden and the Parker's locations
            model.screenshotLocation = CLLocation(latitude: 35.6127, longitude: -77.3722)
            open(.easternBBQ)
        case "lexington_bbq":
            // from uptown Lexington (Main St at Center St)
            model.screenshotLocation = CLLocation(latitude: 35.8240, longitude: -80.2534)
            open(.lexingtonBBQ)
        case "hot_dogs": open(.hotDogs)
        case "honors": open(.honors)
        case "inspections": open(.inspections)
        case "detail":
            // Sam Jones BBQ: hand-checked, a Bib Gourmand, with Wake County's latest grade card
            open(.easternBBQ)
            if let p = pick("Sam Jones BBQ", "Raleigh") ?? model.places.first {
                model.selectedPlace = p; model.guidesPath.append(.place(p))
            }
        case "map": model.tab = .map
        case "saved": model.tab = .saved
        case "about": model.tab = .about
        default: model.tab = .guides; model.selectedGuide = nil
        }
        // iPad shows the place column next to every list, so give each shot a place instead of "Pick a place": a different
        // honored or hand-checked one per shot.
        guard UIDevice.current.userInterfaceIdiom == .pad, model.selectedPlace == nil else { return }
        let place: Place? = switch name {
        case "home": pick("Skylight Inn BBQ", "Ayden")
        case "eastern_bbq": pick("B's Barbecue", "Greenville")
        case "lexington_bbq": pick("Lexington Barbecue", "Lexington")
        case "hot_dogs": pick("The Roast Grill", "Raleigh")
        case "map": pick("The Pit Authentic Barbecue", "Raleigh")
        case "honors": pick("Counter", "Charlotte")
        case "inspections": pick("Poole's", "Raleigh")
        case "saved": pick("Beck's Restaurant", "Calabash")
        case "about": nil
        default: pick("Poole's", "Raleigh")
        }
        model.selectedPlace = place
    }
}

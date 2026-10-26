import XCTest
import CoreLocation
@testable import NorthCarolinaEats

@MainActor
final class NorthCarolinaEatsTests: XCTestCase {

    /// A tiny core file and two region detail files with the same shape as Resources/places.json and Resources/detail-*.json.
    private func sampleModel() async throws -> AppModel {
        let json = """
        {"v":1,"generated":"2026-10-26","overture_release":"2026-10-21.0","permits_updated":"2026-10-26",
         "permits_url":"https://data.wake.gov/datasets/124c2187da8c41c59bde04fa67eb2872","inspections_through":{"wak":"2026-09-14"},
         "results":["A","B","C"],"portal":"https://public.cdpehs.com/NCENVPBL/ESTABLISHMENT/ShowESTABLISHMENTTablePage.aspx?ESTTST_CTY=",
         "county_no":{"Wake County":92,"Davidson County":29,"Pitt County":74,"Brunswick County":10,"Mecklenburg County":60},
         "cities":["Raleigh","Lexington","Ayden","Calabash","Charlotte","Wake Forest"],
         "cuisines":["BBQ","Seafood","Hot Dogs & Sausages","Chicken & Wings","American & Other","Pizza"],
         "brands":["Bojangles"],"counties":["Wake County","Davidson County","Pitt County","Brunswick County","Mecklenburg County"],
         "regions":["Charlotte & the Southern Piedmont","Raleigh, Durham & the Triangle","Greensboro, Winston-Salem & the Triad","Asheville & the Mountains","Wilmington & the Southern Coast","Eastern North Carolina & the Outer Banks"],
         "srcs":["official","meta","AllThePlaces","DAC","research"],
         "count":9,"count_restaurants":8,
         "calibration":{"Wake County (food service permits)":{"listings":5482,"groups":{"meta_high":{"n":2235,"official":0.764}}}},
         "places":[
          {"id":"a","n":"Sam Jones BBQ","c":0,"co":0,"rg":1,"cu":0,"t":2,"s":1,"hc":1,"g":1,"mi":2,"ip":36,"a":"502 W Lenoir St","z":"27601",
           "la":35.7737,"lo":-78.6460,"dish":"whole hog","in":[0,0,"2026-08-04",96.5]},
          {"id":"b","n":"Lexington Barbecue","c":1,"co":1,"rg":2,"cu":0,"t":1,"s":1,"hc":1,"g":2,"h":1,"jbf":"America's Classic 2003","a":"100 Smokehouse Ln",
           "la":35.8110,"lo":-80.2840,"dish":"red slaw"},
          {"id":"c","n":"Bojangles","c":4,"co":4,"rg":0,"cu":3,"t":1,"s":2,"b":0,"ch":300,"la":35.22,"lo":-80.84},
          {"id":"d","n":"Beck's Restaurant","c":3,"co":3,"rg":4,"cu":1,"t":1,"s":1,"hc":1,"g":72,"f":1940,"a":"1014 River Rd","la":33.8870,"lo":-78.5640},
          {"id":"e","n":"Sheetz","c":0,"co":0,"rg":1,"cu":4,"t":1,"s":1,"v":1,"la":35.80,"lo":-78.70},
          {"id":"f","n":"Counter","c":4,"co":4,"rg":0,"cu":4,"t":1,"s":1,"hc":1,"mi":3,"ip":52,"a":"2001 W Morehead St","la":35.2330,"lo":-80.8710},
          {"id":"g","n":"The Roast Grill","c":0,"co":0,"rg":1,"cu":2,"t":2,"s":1,"hc":1,"g":4,"a":"7 S West St","la":35.7790,"lo":-78.6450,
           "in":[0,1,"2026-06-25",88.5]},
          {"id":"h","n":"Skylight Inn BBQ","c":2,"co":2,"rg":5,"cu":0,"t":1,"s":1,"hc":1,"g":1,"h":1,"jbf":"America's Classic 2003","a":"4618 Lee St","la":35.4720,"lo":-77.4170},
          {"id":"i","n":"Wake Forest Pizza","c":5,"co":0,"rg":1,"cu":5,"t":1,"s":1,"a":"100 S White St","la":35.98,"lo":-78.51}
         ]}
        """
        let triangle = """
        {"a":{"lic":[["Wake County food service permit","04092016000"]],"ph":"(919) 400-1234","w":"samjonesbbq.com",
              "in":{"n":12,"h":[["2026-08-04",0,96.5,0],["2026-01-10",1,89,0],["2025-09-02",0,94.5,1]],
                    "i":[["3-501.17","Priority Foundation","Ready-to-eat, TCS food; date marking",1.5],["6-501.12",null,"Cleaning, frequency and restrictions",0]]}},
         "g":{"w":"javascript:alert(1)","in":{"n":3,"h":[["2026-06-25",1,88.5,0]],"i":[]}}}
        """
        let triad = """
        {"b":{"w":"https://www.lexbbq.com/"}}
        """
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent("nc-test-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        let url = dir.appendingPathComponent("places.json")
        try json.data(using: .utf8)!.write(to: url)
        try triangle.data(using: .utf8)!.write(to: dir.appendingPathComponent("detail-raleigh-durham-the-triangle.json"))
        try triad.data(using: .utf8)!.write(to: dir.appendingPathComponent("detail-greensboro-winston-salem-the-triad.json"))
        let model = AppModel(defaults: UserDefaults(suiteName: "test-\(UUID().uuidString)")!)
        await model.load(from: url, detailFolder: dir)
        XCTAssertTrue(model.isLoaded, model.loadError ?? "")
        return model
    }

    func testDecodesAndHidesNonRestaurantsByDefault() async throws {
        let m = try await sampleModel()
        XCTAssertEqual(m.places.count, 9)
        XCTAssertEqual(m.restaurantCount, 8)
        XCTAssertFalse(m.list(.all, sort: .name, search: "", here: nil).contains { $0.name == "Sheetz" }, "a gas-station counter is hidden by default")
        m.filters.includeNonRestaurants = true
        XCTAssertTrue(m.list(.all, sort: .name, search: "", here: nil).contains { $0.name == "Sheetz" })
        XCTAssertEqual(m.permitsUpdated, "2026-10-26")
    }

    func testGuidesListOnlyWhatTheyPromise() async throws {
        let m = try await sampleModel()
        XCTAssertEqual(m.list(.easternBBQ, sort: .name, search: "", here: nil).map(\.name), ["Sam Jones BBQ", "Skylight Inn BBQ"])
        XCTAssertEqual(m.list(.lexingtonBBQ, sort: .name, search: "", here: nil).map(\.name), ["Lexington Barbecue"])
        XCTAssertEqual(m.list(.hotDogs, sort: .name, search: "", here: nil).map(\.name), ["The Roast Grill"])
        XCTAssertEqual(m.list(.calabash, sort: .name, search: "", here: nil).map(\.name), ["Beck's Restaurant"])
        XCTAssertEqual(m.list(.oldest, sort: .oldest, search: "", here: nil).map(\.name), ["Beck's Restaurant"])
        XCTAssertEqual(m.list(.honors, sort: .iconic, search: "", here: nil).map(\.name),
                       ["Counter", "Sam Jones BBQ", "Lexington Barbecue", "Skylight Inn BBQ"])
        XCTAssertEqual(m.list(.moravian, sort: .name, search: "", here: nil), [], "a guide with nothing hand-checked yet is empty, not padded")
    }

    /// Wake County's own scores, the grade rule .2662 gives them, and the state portal's page for every other county.
    func testInspectionsAreTheCountysOwn() async throws {
        let m = try await sampleModel()
        XCTAssertEqual(m.list(.inspections, sort: .recent, search: "", here: nil).map(\.name), ["Sam Jones BBQ", "The Roast Grill"])
        XCTAssertEqual(m.list(.inspections, sort: .lowestScore, search: "", here: nil).map(\.name), ["The Roast Grill", "Sam Jones BBQ"])
        XCTAssertEqual(m.list(.inspections, sort: .highestScore, search: "", here: nil).map(\.name), ["Sam Jones BBQ", "The Roast Grill"])
        let sam = try XCTUnwrap(m.place(id: "a")?.inspection)
        XCTAssertEqual(sam.score, 96.5); XCTAssertEqual(sam.scoreText, "96.5"); XCTAssertEqual(m.grade(sam.grade), "A"); XCTAssertEqual(sam.date, "2026-08-04")
        XCTAssertEqual(m.grade(m.place(id: "g")!.inspection!.grade), "B")
        XCTAssertNil(m.place(id: "b")!.inspection, "outside Wake County no score is shown, and none is computed")
        XCTAssertEqual(m.grade(7), "—", "a grade the data doesn't name is unknown")
        XCTAssertEqual(m.inspectionsThrough, "2026-09-14")
        XCTAssertEqual(m.portalURL(county: "Davidson County")?.absoluteString,
                       "https://public.cdpehs.com/NCENVPBL/ESTABLISHMENT/ShowESTABLISHMENTTablePage.aspx?ESTTST_CTY=29")
        XCTAssertNil(m.portalURL(county: nil))
        let d = await m.detail(for: m.place(id: "a")!)
        XCTAssertEqual(d?.inspection?.n, 12)
        XCTAssertEqual(d?.inspection?.visits.map(\.score), [96.5, 89, 94.5])
        XCTAssertEqual(d?.inspection?.visits.last?.reinspection, true)
        XCTAssertEqual(d?.inspection?.items.first?.severity, "Priority Foundation")
        XCTAssertNil(d?.inspection?.items.last?.severity, "a missing severity stays missing")
    }

    func testDatesAreCalendarDays() {
        var utc = Calendar(identifier: .gregorian)
        utc.timeZone = TimeZone(identifier: "UTC")!
        let d = DayFormat.date("2026-06-16")!
        XCTAssertEqual(utc.dateComponents([.year, .month, .day], from: d), DateComponents(year: 2026, month: 6, day: 16))
        XCTAssertTrue(DayFormat.monthYear("2025-09-01")!.contains("2025"))
        XCTAssertNil(DayFormat.date("2026-13-01"))
        XCTAssertEqual(DayFormat.text("soon"), "soon", "a value that isn't a date is shown as it is")
    }

    func testRegionDetailsLoadOnDemand() async throws {
        let m = try await sampleModel()
        let v = await m.detail(for: m.place(id: "a")!)
        XCTAssertEqual(v?.licenses.first?.id, "04092016000")
        XCTAssertEqual(v?.licenses.first?.source, "Wake County food service permit")
        XCTAssertEqual(v?.website?.absoluteString, "https://samjonesbbq.com", "a bare host gets https://")
        let g = await m.detail(for: m.place(id: "g")!)
        XCTAssertNil(g?.website, "a javascript: link never becomes a website button")
        let b = await m.detail(for: m.place(id: "b")!)
        XCTAssertEqual(b?.website?.host, "www.lexbbq.com")
        XCTAssertEqual(AppModel.regionSlug("Raleigh, Durham & the Triangle"), "raleigh-durham-the-triangle")
        let missing = await m.detail(for: m.place(id: "d")!)
        XCTAssertNil(missing, "a region with no detail file reads as no detail, not a crash")
    }

    func testSearchWordStartsTownsAndGuides() async throws {
        let m = try await sampleModel()
        XCTAssertEqual(m.list(.all, sort: .name, search: "skylight", here: nil).map(\.name), ["Skylight Inn BBQ"])
        XCTAssertEqual(m.list(.all, sort: .name, search: "raleigh", here: nil).map(\.name), ["Sam Jones BBQ", "The Roast Grill"], "a town narrows to it")
        XCTAssertEqual(m.list(.all, sort: .name, search: "🍕", here: nil), [], "an emoji finds nothing, not everything")
        XCTAssertEqual(m.list(.all, sort: .name, search: "whole hog", here: nil).map(\.name), ["Sam Jones BBQ", "Skylight Inn BBQ"], "a guide word means the guide")
        XCTAssertEqual(m.list(.all, sort: .name, search: "red slaw", here: nil).map(\.name), ["Lexington Barbecue"])
        XCTAssertEqual(m.list(.all, sort: .name, search: "wake forest", here: nil).map(\.name), ["Wake Forest Pizza"], "the town, not every Wake County place")
        XCTAssertEqual(m.list(.all, sort: .name, search: "becks", here: nil).map(\.name), ["Beck's Restaurant"], "apostrophes don't matter")
        // "barbecue" and "bbq" find the same places (QA 2026-10-26)
        // (names with the word itself come first, so compare as sets)
        let bbq = Set(m.list(.all, sort: .name, search: "bbq", here: nil).map(\.name))
        XCTAssertEqual(Set(m.list(.all, sort: .name, search: "barbecue", here: nil).map(\.name)), bbq)
        XCTAssertEqual(bbq, ["Lexington Barbecue", "Sam Jones BBQ", "Skylight Inn BBQ"])
    }

    func testOutsideNorthCarolinaUsesTheOutline() {
        func inside(_ la: Double, _ lo: Double) -> Bool { NorthCarolinaOutline.contains(CLLocationCoordinate2D(latitude: la, longitude: lo)) }
        XCTAssertTrue(inside(35.78, -78.64), "Raleigh"); XCTAssertTrue(inside(35.23, -80.84), "Charlotte"); XCTAssertTrue(inside(35.60, -82.55), "Asheville")
        XCTAssertTrue(inside(35.09, -84.03), "Murphy"); XCTAssertTrue(inside(35.91, -75.67), "Manteo"); XCTAssertTrue(inside(34.23, -77.94), "Wilmington")
        XCTAssertTrue(inside(36.22, -81.67), "Boone"); XCTAssertTrue(inside(36.06, -75.71), "Kitty Hawk"); XCTAssertTrue(inside(33.89, -78.57), "Calabash")
        XCTAssertFalse(inside(36.85, -76.29), "Norfolk"); XCTAssertFalse(inside(33.69, -78.89), "Myrtle Beach"); XCTAssertFalse(inside(34.85, -82.39), "Greenville SC")
        XCTAssertFalse(inside(35.96, -83.92), "Knoxville"); XCTAssertFalse(inside(33.75, -84.39), "Atlanta"); XCTAssertFalse(inside(37.33, -122.03), "Cupertino")
    }

    func testBundledData() async throws {
        let m = AppModel(defaults: UserDefaults(suiteName: "bundle-\(UUID().uuidString)")!)
        await m.load()
        XCTAssertTrue(m.isLoaded, m.loadError ?? "")
        XCTAssertGreaterThan(m.restaurantCount, 20_000)
        XCTAssertGreaterThanOrEqual(m.count(.honors), 60)
        XCTAssertEqual(m.bibCount, 11, "North Carolina's eleven Bib Gourmands (MICHELIN Guide American South 2026)")
        XCTAssertEqual(m.places.filter { $0.michelin == .oneStar }.map(\.name), ["Counter"])
        XCTAssertEqual(Set(m.places.map(\.id)).count, m.places.count, "ids are unique")
        for g in Guide.allCases where g.tag != nil {
            XCTAssertTrue(m.places.filter(g.includes).allSatisfy(\.handChecked), "\(g.title) lists only hand-checked places")
        }
        XCTAssertTrue(m.places.contains { $0.name == "Skylight Inn BBQ" && $0.jamesBeardLabel == "America's Classic" })
        // inspection results are Wake County's only, and only the three grade letters
        let inspected = m.places.filter { $0.inspection != nil }
        XCTAssertGreaterThan(inspected.count, 1_500)
        XCTAssertTrue(inspected.allSatisfy { $0.county == "Wake County" }, "an inspection result outside Wake County")
        XCTAssertEqual(Set(inspected.map { m.grade($0.inspection!.grade) }).subtracting(["A", "B", "C"]), [])
        XCTAssertTrue(inspected.allSatisfy { $0.inspection!.date <= m.inspectionsThrough }, "an inspection after the records-through date")
        XCTAssertTrue(inspected.allSatisfy { (70...100).contains($0.inspection!.score) }, "a score the grade card can't show")
        XCTAssertFalse(m.places.contains(where: \.servesBeer), "no alcohol list is published in North Carolina")
        // no Google-derived data: the data file has no rating, review or price fields at all
        let raw = try String(contentsOf: Bundle.main.url(forResource: "places", withExtension: "json")!, encoding: .utf8)
        for key in ["\"rating\"", "\"reviews\"", "\"price\"", "\"gmap_id\""] { XCTAssertFalse(raw.contains(key), "\(key) must not ship") }
    }

    /// Stable ids: md5(name + ~100 m cell)[:12], never a row number; every bundled region detail file decodes and its ids are core ids.
    func testIdsAndBundledDetailFiles() async throws {
        let m = AppModel(defaults: UserDefaults(suiteName: "ids-\(UUID().uuidString)")!)
        await m.load()
        XCTAssertTrue(m.places.allSatisfy { $0.id.count >= 12 && $0.id.prefix(12).allSatisfy(\.isHexDigit) && $0.id.dropFirst(12).allSatisfy { $0 == "x" } })
        let ids = Set(m.places.map(\.id))
        var permitted = 0
        for region in Set(m.places.compactMap(\.region)) {
            let url = try XCTUnwrap(Bundle.main.url(forResource: "detail-" + AppModel.regionSlug(region), withExtension: "json"), region)
            let d = try JSONDecoder().decode([String: PlaceDetail].self, from: Data(contentsOf: url))
            XCTAssertTrue(Set(d.keys).isSubset(of: ids), "\(region) detail ids are core ids")
            permitted += d.values.filter { $0.licenses.contains { $0.source == "Wake County food service permit" && $0.id != nil } }.count
        }
        XCTAssertGreaterThan(permitted, 1_500, "Wake places carry their State ID")
    }

    func testBundledDataGuards() async throws {
        let m = AppModel(defaults: UserDefaults(suiteName: "guards-\(UUID().uuidString)")!)
        await m.load()
        XCTAssertTrue(m.isLoaded, m.loadError ?? "")
        XCTAssertEqual(DataGuards.adultVenues(m.places), [], "no strip club under its name")
        XCTAssertEqual(DataGuards.badWebsites(try DataGuards.bundledLinks(m.places)), [], "no directory, Google or news page as a restaurant's website")
        XCTAssertEqual(DataGuards.badNames(m.places), [], "no visible name ending in \u{201C} the\u{201D} or \u{201C} of\u{201D}, or just \u{201C}The\u{201D}")
        XCTAssertEqual(DataGuards.legalNames(m.places), [], "no license holder entity name (\u{201C}… LLC\u{201D}) shown as a place's name")
        XCTAssertEqual(DataGuards.nonRestaurants(m.places), [], "no nail salon, senior home, gun store or gas station among the restaurants")
    }

    /// Each guard above fires on a copy of the bundled data broken the way QA found it elsewhere: a guard that can't fail guards nothing.
    func testGuardsCatchABrokenCopy() async throws {
        let raw = try Data(contentsOf: Bundle.main.url(forResource: "places", withExtension: "json")!)
        var file = try XCTUnwrap(JSONSerialization.jsonObject(with: raw) as? [String: Any])
        var places = try XCTUnwrap(file["places"] as? [[String: Any]])
        let idx = places.indices.filter { places[$0]["v"] == nil }.prefix(6).map { $0 }
        places[idx[2]]["n"] = "Baby Dolls Gentlemen's Club"
        places[idx[3]]["n"] = "Kitchen the"
        places[idx[4]]["n"] = "OLD NORTH STATE HOSPITALITY GROUP LLC"
        places[idx[5]]["n"] = "Tipsy Nails & Spa"
        file["places"] = places
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("places-broken.json")
        try JSONSerialization.data(withJSONObject: file).write(to: url)
        let m = AppModel(defaults: UserDefaults(suiteName: "broken-\(UUID().uuidString)")!)
        await m.load(from: url)
        XCTAssertTrue(m.isLoaded, m.loadError ?? "")
        let id = idx.map { places[$0]["id"] as? String }
        func caught(_ found: [String], _ i: Int, _ what: String) {
            XCTAssertTrue(found.contains { $0.contains("[\(id[i] ?? "?")]") }, "the guard missed \(what)")
        }
        let links = [(name: "A", id: "x1", url: "https://www.yelp.com/biz/some-place"), (name: "B", id: "x2", url: "https://www.newsobserver.com/living/food-drink/article123.html"),
                     (name: "C", id: "x3", url: "https://smart.com/menu")]
        XCTAssertEqual(DataGuards.badWebsites(links).count, 2, "the guard catches a Yelp page and a news story, and not smart.com")
        caught(DataGuards.adultVenues(m.places), 2, "a gentlemen's club")
        caught(DataGuards.badNames(m.places), 3, "\u{201C}Kitchen the\u{201D}")
        caught(DataGuards.legalNames(m.places), 4, "a license holder's entity name")
        caught(DataGuards.nonRestaurants(m.places), 5, "a nail salon shown as a restaurant")
    }
}

/// Checks on the bundled data, written as functions so testGuardsCatchABrokenCopy can prove each one fires.
enum DataGuards {
    /// directories, Google and news sites: matched on the link's host, so "smart.com" isn't "rt.com"
    static let badHosts = #"^https?://([^/?#]*\.)?(yelp\.com|business\.site|google\.com|groupon\.com|yellowpages\.com|tripadvisor\.com|newsobserver\.com|charlotteobserver\.com|citizen-times\.com|journalnow\.com|greensboro\.com|starnewsonline\.com|wral\.com|wsoctv\.com|wcnc\.com|ourstate\.com|indyweek\.com|eater\.com|rt\.com)([:/?#]|$)"#

    static func badWebsites(_ links: [(name: String, id: String, url: String)]) -> [String] {
        links.compactMap { l in
            guard l.url.range(of: badHosts, options: [.regularExpression, .caseInsensitive]) != nil else { return nil }
            return "\(l.name) [\(l.id)]: \(l.url)"
        }
    }

    /// every website link in the bundled region detail files, with its place's name
    static func bundledLinks(_ places: [Place]) throws -> [(name: String, id: String, url: String)] {
        let names = Dictionary(places.map { ($0.id, $0.name) }, uniquingKeysWith: { a, _ in a })
        var out: [(name: String, id: String, url: String)] = []
        for region in Set(places.compactMap(\.region)) {
            guard let url = Bundle.main.url(forResource: "detail-" + AppModel.regionSlug(region), withExtension: "json") else { continue }
            for (id, d) in try JSONDecoder().decode([String: PlaceDetail].self, from: Data(contentsOf: url)) {
                if let w = d.website?.absoluteString { out.append((names[id] ?? "?", id, w)) }
            }
        }
        return out
    }

    static let adultNames = #"\bnude\b|adult book ?store|gentlem[ae]n['’]?s club|strip club|exotic dancer|\bmen['’]?s club|rick['’]?s cabaret|xtc cabaret|baby dolls|spearmint rhino|bikini bar|pt['’]?s showclub|showgirls|centerfolds|treasures? gentlem"#

    /// every permit or license number in the bundled region detail files, by place id
    static func bundledLicenses(_ places: [Place]) throws -> [String: [String]] {
        var out: [String: [String]] = [:]
        for region in Set(places.compactMap(\.region)) {
            guard let url = Bundle.main.url(forResource: "detail-" + AppModel.regionSlug(region), withExtension: "json") else { continue }
            for (id, d) in try JSONDecoder().decode([String: PlaceDetail].self, from: Data(contentsOf: url)) where !d.licenses.isEmpty {
                out[id] = d.licenses.compactMap(\.id)
            }
        }
        return out
    }

    static func adultVenues(_ places: [Place]) -> [String] {
        places.filter { $0.name.range(of: adultNames, options: [.regularExpression, .caseInsensitive]) != nil }.map { "\($0.name) [\($0.id)]" }
    }

    /// a name cut off after "the" or "of" ("Kitchen the", "Wines of") or nothing but "The", among the places shown by default
    static func badNames(_ places: [Place]) -> [String] {
        places.filter { p in
            let n = p.name.trimmingCharacters(in: .whitespaces).lowercased()
            return !p.isVenue && (n.hasSuffix(" the") || n.hasSuffix(" of") || n == "the")
        }.map { "\($0.name) [\($0.id)]" }
    }

    /// a license holder (owner) is never shown; a business name that's still a legal entity shouldn't be either
    static let legalSuffix = #"\b(llc|l\.l\.c|inc|corp|corporation)\.?$"#

    static func legalNames(_ places: [Place]) -> [String] {
        places.filter { !$0.isVenue && $0.name.range(of: legalSuffix, options: [.regularExpression, .caseInsensitive]) != nil }
            .map { "\($0.name) [\($0.id)]" }
    }

    /// businesses that aren't places to eat, among the places shown by default
    static let nonRestaurantNames = #"\bnails?\b|assisted living|gun (?:club|range|shop|store)|shooting range|firearms|petroleum|\bauto (?:repair|parts)\b"#

    static func nonRestaurants(_ places: [Place]) -> [String] {
        places.filter { !$0.isVenue && $0.name.range(of: nonRestaurantNames, options: [.regularExpression, .caseInsensitive]) != nil }
            .map { "\($0.name) [\($0.id)]" }
    }
}

/// pipeline/website_blocklist.json (hacked, taken-over, expired or another business's sites, confirmed by hand in the link sweeps):
/// no link on it may ship in any field of any JSON file the app bundles. The 2026-10-19 QA found the export had only filtered the
/// website field, or nothing, so hijacked links were still in the bundle. Read from the repo, so a new entry needs no code change.
final class LinkBlocklistTests: XCTestCase {
    func testNoBlocklistedLinkInBundledData() throws {
        let entries = try LinkBlocklist.entries()
        XCTAssertFalse(entries.isEmpty, "the blocklist is missing or empty")
        let files = LinkBlocklist.bundledJSON()
        XCTAssertFalse(files.isEmpty, "no bundled JSON found")
        var hits: [String] = []
        for url in files {
            let text = try String(contentsOf: url, encoding: .utf8)
            hits += LinkBlocklist.hits(in: text, entries).map { "\(url.lastPathComponent): \($0)" }
        }
        XCTAssertEqual(hits, [], "blocklisted links in the app's bundled data")
    }

    /// The guard fires on a copy of the bundled data broken three ways: a blocklisted domain, its subdomain, and a "url" entry.
    func testBlocklistGuardCatchesABrokenCopy() throws {
        let entries = try LinkBlocklist.entries()
        let file = try XCTUnwrap(LinkBlocklist.bundledJSON().max { (try? $0.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0) ?? 0 < (try? $1.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0) ?? 0 })
        let text = try String(contentsOf: file, encoding: .utf8)
        let domain = try XCTUnwrap(entries.first { ($0["match"] as? String ?? "domain") == "domain" }?["domain"] as? String)
        let fake: [[String: Any]] = entries + [["match": "url", "url": "https://example.org/hacked-page"]]
        let before = LinkBlocklist.hits(in: text, fake).count
        let broken = text + "{\"w\":\"https://www.\(domain)/menu\"}{\"src\":\"http://shop.\(domain)/\"}{\"w\":\"https://example.org/hacked-page/\"}"
        XCTAssertEqual(LinkBlocklist.hits(in: broken, fake).count, before + 3, "a domain, a subdomain and a url entry are all caught")
        XCTAssertEqual(LinkBlocklist.hits(in: "{\"w\":\"https://not\(domain)/\"}", entries), [], "a host that only ends with the domain's letters isn't it")
    }
}

enum LinkBlocklist {
    static func entries() throws -> [[String: Any]] {
        let url = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
            .appendingPathComponent("pipeline/website_blocklist.json")
        return try XCTUnwrap(JSONSerialization.jsonObject(with: Data(contentsOf: url)) as? [[String: Any]])
    }

    /// every .json file in the app bundle, subfolders included
    static func bundledJSON() -> [URL] {
        let root = Bundle.main.bundleURL
        let all = FileManager.default.enumerator(at: root, includingPropertiesForKeys: nil)?.allObjects as? [URL] ?? []
        return all.filter { $0.pathExtension == "json" && !$0.path.contains("/PlugIns/") }
    }

    private static func host(_ u: URLComponents) -> String {
        var h = (u.host ?? "").lowercased()
        if h.hasSuffix(".") { h.removeLast() }
        return h.hasPrefix("www.") ? String(h.dropFirst(4)) : h
    }

    private static func trimmedPath(_ p: String) -> String { p.hasSuffix("/") ? String(p.dropLast()) : p }

    /// the links in a JSON text that an entry covers: a "domain" entry its domain and subdomains, a "url" entry that page only
    static func hits(in text: String, _ entries: [[String: Any]]) -> [String] {
        let t = text.replacingOccurrences(of: "\\/", with: "/")
        let rx = try! NSRegularExpression(pattern: #"https?://[^"\s\\]+"#, options: [.caseInsensitive])
        return rx.matches(in: t, range: NSRange(t.startIndex..., in: t)).compactMap { m -> String? in
            let s = String(t[Range(m.range, in: t)!])
            guard let u = URLComponents(string: s) else { return nil }
            let h = host(u)
            for e in entries {
                if (e["match"] as? String ?? "domain") == "url" {
                    guard let v = URLComponents(string: e["url"] as? String ?? "") else { continue }
                    if !h.isEmpty && h == host(v) && trimmedPath(u.path) == trimmedPath(v.path) { return s }
                } else {
                    var d = (e["domain"] as? String ?? "").lowercased()
                    if let r = d.range(of: "://") { d = String(d[r.upperBound...]) }
                    d = String(d.split(separator: "/").first ?? "")
                    if d.hasPrefix("www.") { d = String(d.dropFirst(4)) }
                    if !d.isEmpty && (h == d || h.hasSuffix("." + d)) { return s }
                }
            }
            return nil
        }
    }
}

/// QA 2026-10-19, P1 3a: the support address is nick@eatsranked.com (Nick, 2026-10-12). The old Gmail address must not come back
/// anywhere in the app's source or bundled files.
final class SupportEmailTests: XCTestCase {
    func testSupportEmailIsEatsRanked() {
        XCTAssertEqual(Links.supportEmail, "nick@eatsranked.com")
    }

    func testNoGmailInAppSource() throws {
        let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
            .appendingPathComponent("NorthCarolinaEats")
        XCTAssertGreaterThan(SupportEmailScan.textFiles(under: root).count, 5, "the app's source folder wasn't found")
        XCTAssertEqual(SupportEmailScan.hits(under: root), [], "the app's source still has a Gmail address")
    }

    /// The guard fires on a broken copy: a folder with one planted Gmail address.
    func testGmailGuardCatchesABrokenCopy() throws {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: dir.appendingPathComponent("App"), withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: dir) }
        try "static let supportEmail = \"someone@GMAIL.com\"\n".write(to: dir.appendingPathComponent("App/Links.swift"), atomically: true, encoding: .utf8)
        try "{\"ok\": \"nick@eatsranked.com\"}".write(to: dir.appendingPathComponent("App/data.json"), atomically: true, encoding: .utf8)
        XCTAssertEqual(SupportEmailScan.hits(under: dir), ["App/Links.swift"])
    }
}

enum SupportEmailScan {
    static let textExtensions: Set<String> = ["swift", "plist", "json", "strings", "xcstrings", "xcprivacy", "md", "txt", "html", "entitlements"]

    static func textFiles(under root: URL) -> [URL] {
        let all = FileManager.default.enumerator(at: root, includingPropertiesForKeys: nil)?.allObjects as? [URL] ?? []
        return all.filter { textExtensions.contains($0.pathExtension.lowercased()) }
    }

    /// paths (relative to root) of text files that mention gmail.com, in any case
    static func hits(under root: URL) -> [String] {
        let base = root.resolvingSymlinksInPath().path + "/"
        return textFiles(under: root).compactMap { url in
            guard let text = try? String(contentsOf: url, encoding: .utf8),
                  text.range(of: "gmail.com", options: .caseInsensitive) != nil else { return nil }
            return url.resolvingSymlinksInPath().path.replacingOccurrences(of: base, with: "")
        }.sorted()
    }
}

/// QA 2026-10-19, P1 #13: outbound links ship without tracking tags (ref=google, referrer=google_food_ordering, cn_channel, utm_* …).
/// pipeline/tracking_params.py strips them in the export; these are the same rules.
final class TrackingParamTests: XCTestCase {
    func testNoTrackingParametersInBundledLinks() throws {
        let files = TrackingParams.bundledJSON()
        XCTAssertFalse(files.isEmpty, "no bundled JSON found")
        var hits: [String] = []
        for url in files {
            let text = try String(contentsOf: url, encoding: .utf8)
            hits += TrackingParams.tracked(in: text).map { "\(url.lastPathComponent): \($0)" }
        }
        XCTAssertEqual(hits, [], "links with tracking parameters in the app's bundled data")
    }

    /// The guard fires on a broken copy (four kinds of tracking tag, one in escaped JSON) and leaves a store's own parameters alone.
    func testTrackingGuardCatchesABrokenCopy() {
        let broken = #"[{"w":"https:\/\/places.example.com\/menu?ref=google"},{"w":"https://a.example/?utm_source=gmb&store=4"},"#
            + #"{"w":"https://b.example/x?referrer=google_food_ordering"},{"w":"https://c.example/order/1?cn_channel=cn_google"}]"#
        XCTAssertEqual(TrackingParams.tracked(in: broken).count, 4)
        let clean = #"[{"w":"https://order.example.com/menu?restaurantId=51&location=7"},{"w":"https://shop.example.com/?cid=12&ref=gs"}]"#
        XCTAssertEqual(TrackingParams.tracked(in: clean), [])
    }
}

enum TrackingParams {
    /// tracking by name, whatever the value
    static let keys = try! NSRegularExpression(pattern: #"^(?:utm[_-].*|gclid|gbraid|wbraid|dclid|fbclid|msclkid|mc_cid|mc_eid|_ga|_gl|igsh|"#
        + #"igshid|mibextid|srsltid|cn_channel|y_source|rwg_token|olonwp|ost_redirect_attribution|cmpid|yext_?.*)$"#, options: [.caseInsensitive])
    /// tracking only with these values
    static let values: [String: String] = ["ref": #"^(?:google|gmb|gbp|yext|bookmarks)\b"#, "referrer": "^google",
                                           "source": #"^(?:google|gmb|gbp|yext)\b"#, "cid": "^RF:YXT", "cmp": "^OKC-"]

    /// every .json file in the app bundle, subfolders included
    static func bundledJSON() -> [URL] {
        let all = FileManager.default.enumerator(at: Bundle.main.bundleURL, includingPropertiesForKeys: nil)?.allObjects as? [URL] ?? []
        return all.filter { $0.pathExtension == "json" && !$0.path.contains("/PlugIns/") }
    }

    static func isTracking(_ key: String, _ value: String) -> Bool {
        let k = key.trimmingCharacters(in: .whitespaces)
        if keys.firstMatch(in: k, range: NSRange(k.startIndex..., in: k)) != nil { return true }
        guard let pattern = values[k.lowercased()] else { return false }
        return value.trimmingCharacters(in: .whitespaces).range(of: pattern, options: [.regularExpression, .caseInsensitive]) != nil
    }

    /// links in a JSON text whose query carries a tracking parameter
    static func tracked(in text: String) -> [String] {
        let t = text.replacingOccurrences(of: "\\/", with: "/")
        let rx = try! NSRegularExpression(pattern: #"https?://[^\s"'<>\\]+"#)
        return rx.matches(in: t, range: NSRange(t.startIndex..., in: t)).compactMap { m -> String? in
            let s = String(t[Range(m.range, in: t)!])
            guard let q = s.split(separator: "?", maxSplits: 1).dropFirst().first else { return nil }
            let query = q.split(separator: "#", maxSplits: 1, omittingEmptySubsequences: false).first ?? ""
            for part in query.split(separator: "&") {
                let kv = part.split(separator: "=", maxSplits: 1, omittingEmptySubsequences: false)
                let k = String(kv[0]).replacingOccurrences(of: "+", with: " ").removingPercentEncoding ?? String(kv[0])
                let v = kv.count > 1 ? (String(kv[1]).replacingOccurrences(of: "+", with: " ").removingPercentEncoding ?? String(kv[1])) : ""
                if isTracking(k, v) { return s }
            }
            return nil
        }
    }
}
